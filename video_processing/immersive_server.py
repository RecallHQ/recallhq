from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from chainlit.server import app, router
import chainlit as cl

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

# An optional basic route to test the server
#@app.get("/")
#async def get():
#    return {"message": "Hello, WebSocket!"}
from fastapi.responses import StreamingResponse

from fastapi import Request, HTTPException
import os

from typing import Generator
VIDEO_PATH = "output_video.mp4"

# Helper function to generate video content for streaming
def video_stream(file_path: str, start: int = 0, end: int = None) -> Generator[bytes, None, None]:
    with open(file_path, "rb") as video_file:
        video_file.seek(start)
        remaining_bytes = end - start + 1 if end else None
        while remaining_bytes is None or remaining_bytes > 0:
            chunk_size = 1024 * 1024  # 1MB chunks
            data = video_file.read(min(chunk_size, remaining_bytes)) if remaining_bytes else video_file.read(chunk_size)
            if not data:
                break
            yield data
            if remaining_bytes:
                remaining_bytes -= len(data)

# Route for serving video content with support for range requests
@router.get("/recall_immersive_video")
async def stream_video(request: Request):
    range_header = request.headers.get("range")
    file_size = os.path.getsize(VIDEO_PATH)
    
    if range_header:
        # Extract the byte ranges from the header
        range_value = range_header.strip().replace("bytes=", "")
        range_start, range_end = range_value.split("-")
        
        # Convert to integers (default to the end of the file if range_end is not provided)
        range_start = int(range_start)
        range_end = int(range_end) if range_end else file_size - 1
        
        # Validate range
        if range_start >= file_size or range_end >= file_size:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")
        
        content_length = range_end - range_start + 1
        headers = {
            "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4"
        }
        return StreamingResponse(video_stream(VIDEO_PATH, start=range_start, end=range_end), status_code=206, headers=headers)
    
    # Default response for full video (no range request)
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes"
    }
    return StreamingResponse(video_stream(VIDEO_PATH), headers=headers)