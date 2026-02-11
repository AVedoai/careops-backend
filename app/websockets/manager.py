import socketio
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.user import User
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Store connected users by workspace
connected_users: Dict[int, set] = {}


class WebSocketManager:
    """WebSocket manager for real-time communication"""
    
    def __init__(self):
        self.sio = sio
    
    async def connect_user(self, sid: str, workspace_id: int, user_id: int):
        """Add user to workspace room"""
        if workspace_id not in connected_users:
            connected_users[workspace_id] = set()
        connected_users[workspace_id].add(sid)
        
        # Join workspace room
        await self.sio.enter_room(sid, f"workspace_{workspace_id}")
        
        logger.info(f"User {user_id} connected to workspace {workspace_id}")
    
    async def disconnect_user(self, sid: str):
        """Remove user from all rooms"""
        for workspace_id, sids in connected_users.items():
            if sid in sids:
                sids.discard(sid)
                await self.sio.leave_room(sid, f"workspace_{workspace_id}")
                logger.info(f"User disconnected from workspace {workspace_id}")
                break
    
    async def emit_to_workspace(self, workspace_id: int, event: str, data: Any):
        """Emit event to all users in workspace"""
        room = f"workspace_{workspace_id}"
        await self.sio.emit(event, data, room=room)
        logger.info(f"Emitted {event} to workspace {workspace_id}")
    
    async def emit_new_contact(self, workspace_id: int, contact_data: Dict[str, Any]):
        """Emit new contact event"""
        await self.emit_to_workspace(workspace_id, "new_contact", contact_data)
    
    async def emit_new_booking(self, workspace_id: int, booking_data: Dict[str, Any]):
        """Emit new booking event"""
        await self.emit_to_workspace(workspace_id, "new_booking", booking_data)
    
    async def emit_new_message(self, workspace_id: int, message_data: Dict[str, Any]):
        """Emit new message event"""
        await self.emit_to_workspace(workspace_id, "new_message", message_data)
    
    async def emit_booking_update(self, workspace_id: int, booking_data: Dict[str, Any]):
        """Emit booking update event"""
        await self.emit_to_workspace(workspace_id, "booking_updated", booking_data)
    
    async def emit_alert(self, workspace_id: int, alert_data: Dict[str, Any]):
        """Emit alert event"""
        await self.emit_to_workspace(workspace_id, "new_alert", alert_data)
    
    async def emit_inventory_update(self, workspace_id: int, item_data: Dict[str, Any]):
        """Emit inventory update event"""
        await self.emit_to_workspace(workspace_id, "inventory_updated", item_data)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    try:
        # Extract token from auth
        if not auth or 'token' not in auth:
            logger.error(f"No auth token provided for {sid}")
            return False
        
        token = auth['token']
        
        # Decode and verify token
        payload = decode_access_token(token)
        if not payload:
            logger.error(f"Invalid token for {sid}")
            return False
        
        user_id = payload.get("sub")
        if not user_id:
            logger.error(f"No user ID in token for {sid}")
            return False
        
        # Get user from database
        db = next(get_db())
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            if not user or not user.is_active:
                logger.error(f"User not found or inactive for {sid}")
                return False
            
            # Connect user to their workspace
            await websocket_manager.connect_user(sid, user.workspace_id, user.id)
            
            logger.info(f"WebSocket connection established for user {user.id}")
            return True
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error connecting WebSocket: {str(e)}")
        return False


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    try:
        await websocket_manager.disconnect_user(sid)
        logger.info(f"WebSocket disconnected: {sid}")
    except Exception as e:
        logger.error(f"Error disconnecting WebSocket: {str(e)}")


@sio.event
async def join_room(sid, data):
    """Handle room join requests"""
    try:
        room = data.get('room')
        if room:
            await sio.enter_room(sid, room)
            logger.info(f"User {sid} joined room {room}")
    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")


@sio.event
async def leave_room(sid, data):
    """Handle room leave requests"""
    try:
        room = data.get('room')
        if room:
            await sio.leave_room(sid, room)
            logger.info(f"User {sid} left room {room}")
    except Exception as e:
        logger.error(f"Error leaving room: {str(e)}")


# ASGI app for Socket.IO
socket_app = socketio.ASGIApp(sio)