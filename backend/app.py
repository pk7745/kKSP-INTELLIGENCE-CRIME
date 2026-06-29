"""
KAVERI backend entry point — FastAPI + WebSocket via uvicorn/Starlette.
Runs on PORT (default 9000).  WebSocket at /ws, REST at /api/*, webhook at /webhook/*.
"""
import os
import asyncio
import json
import logging
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kaveri")


# ── Global WebSocket manager (imported by other modules) ──────────────────────
class WebSocketManager:
    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.add(ws)
        logger.info(f"WS connected. Total: {len(self.connections)}")

    def disconnect(self, ws: WebSocket):
        self.connections.discard(ws)

    async def broadcast(self, message: dict):
        dead = set()
        text = json.dumps(message, default=str)
        for ws in list(self.connections):
            try:
                await ws.send_text(text)
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
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
        logger.info(f"WS disconnected. Total: {len(ws_manager.connections)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    logger.info(f"Starting KAVERI on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
