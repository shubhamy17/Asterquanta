from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio


class ConnectionManager:
    """Manages WebSocket connections per user_id for real-time progress updates"""
    
    def __init__(self):
        # Map user_id -> list of active WebSocket connections
        # Supports multiple tabs/windows per user
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept and register a new WebSocket connection for a user"""
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        print(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections.get(user_id, []))}")
    
    async def disconnect(self, user_id: int, websocket: WebSocket):
        """Remove a WebSocket connection when client disconnects"""
        async with self._lock:
            if user_id in self.active_connections:
                try:
                    self.active_connections[user_id].remove(websocket)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                except ValueError:
                    pass
        print(f"WebSocket disconnected for user {user_id}")
    
    async def broadcast_to_user(self, user_id: int, data: dict):
        """Send message to all connections for a specific user"""
        if user_id not in self.active_connections:
            return
        
        dead_connections = []
        message = json.dumps(data)
        
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                dead_connections.append(websocket)
        
        # Clean up dead connections
        async with self._lock:
            for ws in dead_connections:
                try:
                    self.active_connections[user_id].remove(ws)
                except (ValueError, KeyError):
                    pass
    
    def broadcast_to_user_sync(self, user_id: int, data: dict):
        """
        Sync wrapper to broadcast from non-async context (e.g., Temporal activities).
        Creates a new event loop if needed.
        """
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, schedule the coroutine
            asyncio.create_task(self.broadcast_to_user(user_id, data))
        except RuntimeError:
            # No running loop - create one for this call
            asyncio.run(self.broadcast_to_user(user_id, data))
    
    def get_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, []))
    
    def get_all_connected_users(self) -> List[int]:
        """Get list of all user_ids with active connections"""
        return list(self.active_connections.keys())


# Global singleton instance
manager = ConnectionManager()
