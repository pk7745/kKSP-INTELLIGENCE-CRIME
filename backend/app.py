"""
KAVERI backend entry point — Tornado (outer server) + FastAPI (REST).
Tornado is required for Catalyst AppSail WebSocket support.
WebSocket at /ws, REST at /api/*, webhook at /webhook/*.
Runs on PORT (default 9000).
"""
import os
import asyncio
import json
import logging
from typing import Set

# ── FastAPI (REST + internal ASGI) ────────────────────────────────────────────
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ── Tornado (outer HTTP/WebSocket server for Catalyst AppSail) ────────────────
import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.httpserver
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kaveri")


# ── Global WebSocket manager (imported by other modules) ──────────────────────
class WebSocketManager:
    def __init__(self):
        self.connections: Set = set()     # holds both FastAPI WS + Tornado WS clients

    async def connect_fastapi(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)
        logger.info(f"FastAPI WS connected. Total: {len(self.connections)}")

    def add_tornado(self, handler):
        self.connections.add(handler)

    def disconnect(self, ws):
        self.connections.discard(ws)

    async def broadcast(self, message: dict):
        dead = set()
        text = json.dumps(message, default=str)
        for ws in list(self.connections):
            try:
                # FastAPI WebSocket
                if hasattr(ws, "send_text"):
                    await ws.send_text(text)
                # Tornado WebSocketHandler
                elif hasattr(ws, "write_message"):
                    ws.write_message(text)
            except Exception:
                dead.add(ws)
        self.connections -= dead


ws_manager = WebSocketManager()


# ── App state (ML model etc.) ─────────────────────────────────────────────────
class AppState:
    model = None
    embeddings = None

app_state = AppState()


# ── FastAPI app ───────────────────────────────────────────────────────────────
from api.firs import router as firs_router
from api.network import router as network_router
from api.hotspots import router as hotspots_router
from api.predictions import router as predictions_router
from api.alerts import router as alerts_router
from api.stats import router as stats_router
from api.export import router as export_router
from api.webhook import router as webhook_router
from ai.kaveri_engine import router as chat_router
from auth.rbac import router as auth_router
from simulator.event_streamer import router as sim_router

app = FastAPI(title="KAVERI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(chat_router,        prefix="/api/chat",        tags=["Chat"])
app.include_router(firs_router,        prefix="/api/firs",        tags=["FIRs"])
app.include_router(network_router,     prefix="/api/network",     tags=["Network"])
app.include_router(hotspots_router,    prefix="/api/hotspots",    tags=["Hotspots"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(alerts_router,      prefix="/api/alerts",      tags=["Alerts"])
app.include_router(stats_router,       prefix="/api/stats",       tags=["Stats"])
app.include_router(export_router,      prefix="/api/export",      tags=["Export"])
app.include_router(webhook_router,     prefix="/webhook",         tags=["Webhook"])
app.include_router(sim_router,         prefix="/api/simulator",   tags=["Simulator"])


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "KAVERI",
        "ws_connections": len(ws_manager.connections),
    }


# ── FastAPI native WebSocket (local dev / non-Catalyst environments) ──────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect_fastapi(websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "KAVERI WebSocket ready",
        }))
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"FastAPI WS disconnected. Total: {len(ws_manager.connections)}")


# ── Tornado WebSocket handler (Catalyst AppSail production) ───────────────────
class TornadoWSHandler(tornado.websocket.WebSocketHandler):
    """Native Tornado WebSocket handler required for Catalyst AppSail."""

    def check_origin(self, origin):
        return True  # Allow all origins (CORS handled separately)

    def open(self):
        ws_manager.add_tornado(self)
        logger.info(f"Tornado WS connected. Total: {len(ws_manager.connections)}")
        self.write_message(json.dumps({
            "type": "connected",
            "message": "KAVERI WebSocket ready (Tornado)",
        }))

    def on_message(self, message):
        try:
            msg = json.loads(message)
            if msg.get("type") == "ping":
                self.write_message(json.dumps({"type": "pong"}))
        except Exception:
            pass

    def on_close(self):
        ws_manager.disconnect(self)
        logger.info(f"Tornado WS disconnected. Total: {len(ws_manager.connections)}")


# ── Tornado ASGI proxy — bridges FastAPI into Tornado's HTTP server ───────────
class TornadoFastAPIHandler(tornado.web.RequestHandler):
    """
    Proxy all non-WebSocket requests from Tornado's HTTP server to FastAPI's ASGI app.
    This allows Tornado to be the single outer server (required for Catalyst AppSail)
    while FastAPI handles all REST logic.
    """
    SUPPORTED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")

    async def prepare(self):
        self._body = self.request.body

    async def _handle(self):
        import uvicorn.lifespan.off
        from io import BytesIO

        scope = {
            "type":         "http",
            "asgi":         {"version": "3.0"},
            "http_version": "1.1",
            "method":       self.request.method,
            "headers":      [
                (k.lower().encode(), v.encode())
                for k, v in self.request.headers.items()
            ],
            "path":         self.request.path,
            "query_string": self.request.query.encode() if self.request.query else b"",
            "root_path":    "",
        }

        body = self._body
        body_sent = False

        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        response_started = False
        response_body = BytesIO()

        async def send(event):
            nonlocal response_started
            if event["type"] == "http.response.start":
                self.set_status(event["status"])
                for name, value in event.get("headers", []):
                    self.set_header(name.decode(), value.decode())
                response_started = True
            elif event["type"] == "http.response.body":
                chunk = event.get("body", b"")
                if chunk:
                    response_body.write(chunk)
                if not event.get("more_body", False):
                    self.write(response_body.getvalue())
                    self.finish()

        await app(scope, receive, send)

    async def get(self):     await self._handle()
    async def post(self):    await self._handle()
    async def put(self):     await self._handle()
    async def patch(self):   await self._handle()
    async def delete(self):  await self._handle()
    async def options(self): await self._handle()
    async def head(self):    await self._handle()


def make_tornado_app():
    return tornado.web.Application([
        (r"/ws",    TornadoWSHandler),
        (r"/.*",    TornadoFastAPIHandler),
    ])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    logger.info(f"Starting KAVERI on port {port} (Tornado + FastAPI)")

    # Use asyncio event loop policy compatible with Tornado
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())

    tornado_app = make_tornado_app()
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(port)

    logger.info(f"Tornado HTTP server listening on port {port}")
    logger.info("WebSocket: /ws  |  REST: /api/*  |  Webhook: /webhook/*")

    tornado.ioloop.IOLoop.current().start()
