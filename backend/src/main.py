"""
模块: main
职责: FastAPI + WebSocket 主服务（接入Session核心）
创建: 2026-07-18
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from core.session import Session
from core.file_bridge import FileBridge
from core.shutong_state import ShutongStateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shutong")

app = FastAPI(title="书童V1")


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def send(self, ws: WebSocket, message: dict):
        await ws.send_json(message)


manager = ConnectionManager()


async def _send(ws: WebSocket, msg_type: str, payload: dict):
    await manager.send(ws, {"type": msg_type, "payload": payload})


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    session: Optional[Session] = None

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "ping":
                await _send(websocket, "pong", {})
                continue

            if data.get("type") == "init_project":
                root = data.get("payload", {}).get("rootPath", "")
                if not root or not Path(root).is_dir():
                    await _send(websocket, "error", {"content": f"无效的项目路径: {root}"})
                    continue
                session = Session(root)
                results = await session.process("init_project", {})
                for msg in results:
                    try:
                        await _send(websocket, msg.type, msg.payload)
                    except Exception:
                        break
                continue

            if session:
                msg_type = data.get("type", "")
                payload = data.get("payload", {})
                results = await session.process(msg_type, payload)
                for msg in results:
                    try:
                        await _send(websocket, msg.type, msg.payload)
                    except Exception:
                        break
            else:
                await _send(websocket, "system", {"content": "请先选择项目路径"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception("WebSocket异常")
        manager.disconnect(websocket)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "shutong-v1"}


@app.get("/api/shutong/files")
async def shutong_files(path: str):
    try:
        fb = FileBridge(path)
        sm = ShutongStateManager(fb)
        return {"files": sm.get_all_statuses()}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.get("/api/file/read")
async def read_file_api(path: str, file_path: str):
    try:
        fb = FileBridge(path)
        return {"content": fb.read_file(file_path)}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
