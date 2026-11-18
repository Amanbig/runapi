from fastapi import WebSocket


async def websocket(ws: WebSocket):
    """WebSocket echo: ws://localhost:8000/api/echo"""
    await ws.accept()
    try:
        while True:
            await ws.send_text(await ws.receive_text())
    except Exception:
        pass
