import os
import asyncio
import json
import logging
from typing import Dict, Set
import tornado.web
import tornado.websocket
import tornado.ioloop
import tornado.httpserver
from tornado.platform.asyncio import AsyncIOMainLoop
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kaveri")

# --- Global state ---
class WebSocketManager:
    def __init__(self):
        self.connections: Set[tornado.websocket.WebSocketHandler] = set()

    async def broadcast(self, message: dict):
        disconnected = set()
        msg = json.dumps(message)
        for conn in self.connections:
            try:
                conn.write_message(msg)
            except Exception:
                disconnected.add(conn)
        self.connections -= disconnected

ws_manager = WebSocketManager()

class AppState:
    model = None
    embeddings = None

app_state = AppState()

# --- WebSocket Handler ---
class KAVERIWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        ws_manager.connections.add(self)
        logger.info(f"WS connected. Total: {len(ws_manager.connections)}")
        self.write_message(json.dumps({"type": "connected", "message": "KAVERI WebSocket ready"}))

    def on_message(self, message):
        pass

    def on_close(self):
        ws_manager.connections.discard(self)

# --- FastAPI app ---
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
from simulator.event_streamer import router as simulator_router

fastapi_app = FastAPI(title="KAVERI API", version="1.0.0")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(firs_router, prefix="/api/firs", tags=["FIRs"])
fastapi_app.include_router(network_router, prefix="/api/network", tags=["Network"])
fastapi_app.include_router(hotspots_router, prefix="/api/hotspots", tags=["Hotspots"])
fastapi_app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
fastapi_app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
fastapi_app.include_router(stats_router, prefix="/api/stats", tags=["Stats"])
fastapi_app.include_router(export_router, prefix="/api/export", tags=["Export"])
fastapi_app.include_router(webhook_router, prefix="/webhook", tags=["Webhook"])
fastapi_app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
fastapi_app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
fastapi_app.include_router(simulator_router, prefix="/api", tags=["Simulator"])

@fastapi_app.get("/api/health")
async def health():
    return {"status": "ok", "service": "KAVERI"}

# --- Tornado app ---
def make_app():
    from tornado.wsgi import WSGIContainer
    from tornado.web import FallbackHandler
    api_container = WSGIContainer(fastapi_app)
    return tornado.web.Application([
        (r"/ws", KAVERIWebSocket),
        (r"/api/.*", FallbackHandler, dict(fallback=api_container)),
        (r"/webhook/.*", FallbackHandler, dict(fallback=api_container)),
        (r"/health.*", FallbackHandler, dict(fallback=api_container)),
    ])

async def main():
    AsyncIOMainLoop().install()
    app = make_app()
    port = int(os.environ.get("PORT", 9000))
    server = tornado.httpserver.HTTPServer(app)
    server.listen(port)
    logger.info(f"KAVERI server started on port {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
