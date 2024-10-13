from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from chainlit.server import app, router

# WebSocket manager to handle multiple connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.latest_socket = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.latest_socket = websocket
        self.active_connections.append(websocket)
        print(f"Recall Websocket connected: f{websocket.url}")

    def disconnect(self, websocket: WebSocket):
        print(f"Recall Websocket disconnected: f{websocket.url}")
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        print(f"Sending broadcast {message} to {len(self.active_connections)}")
        for connection in self.active_connections:
            await connection.send_text(message)

# Create an instance of the ConnectionManager
manager = ConnectionManager()

@app.websocket("/ws_recall")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Receive data from the WebSocket
            print(f"Received data:{data}")
            await manager.send_message(f"Message text was: {data}", websocket)  # Echo back the received message
            await manager.broadcast(f"Broadcast: {data}")  # Broadcast the message to all connected clients
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"A client has disconnected. Number left: {len(manager.active_connections)}")
        #await manager.broadcast("A client has disconnected.")
