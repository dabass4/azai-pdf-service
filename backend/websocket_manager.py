"""
WebSocket Manager for Real-Time Extraction Updates
"""

import socketio
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Allow all origins for development (restrict in production)
    logger=False,
    engineio_logger=False
)


class WebSocketManager:
    """Manage WebSocket connections and broadcast extraction updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[str]] = {}  # {timesheet_id: {sid1, sid2, ...}}
    
    async def connect(self, sid: str, environ: Dict):
        """Handle new WebSocket connection"""
        logger.info(f"WebSocket connected: {sid}")
    
    async def disconnect(self, sid: str):
        """Handle WebSocket disconnection"""
        # Remove from all timesheet subscriptions
        for timesheet_id in list(self.active_connections.keys()):
            if sid in self.active_connections[timesheet_id]:
                self.active_connections[timesheet_id].remove(sid)
                if not self.active_connections[timesheet_id]:
                    del self.active_connections[timesheet_id]
        
        logger.info(f"WebSocket disconnected: {sid}")
    
    async def subscribe_to_extraction(self, sid: str, timesheet_id: str):
        """Subscribe a client to extraction updates for a specific timesheet"""
        if timesheet_id not in self.active_connections:
            self.active_connections[timesheet_id] = set()
        
        self.active_connections[timesheet_id].add(sid)
        logger.info(f"Client {sid} subscribed to timesheet {timesheet_id}")
        
        # Acknowledge subscription
        await sio.emit('subscribed', {'timesheet_id': timesheet_id}, room=sid)
    
    async def broadcast_extraction_progress(self, progress_data: Dict):
        """Broadcast extraction progress to all subscribed clients"""
        timesheet_id = progress_data.get('timesheet_id')
        
        if timesheet_id and timesheet_id in self.active_connections:
            # Send to all clients subscribed to this timesheet
            for sid in self.active_connections[timesheet_id]:
                await sio.emit('extraction_progress', progress_data, room=sid)
            
            logger.debug(f"Broadcasted progress for {timesheet_id} to {len(self.active_connections[timesheet_id])} clients")


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    await ws_manager.connect(sid, environ)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    await ws_manager.disconnect(sid)


@sio.event
async def subscribe_extraction(sid, data):
    """Handle subscription to extraction updates"""
    timesheet_id = data.get('timesheet_id')
    if timesheet_id:
        await ws_manager.subscribe_to_extraction(sid, timesheet_id)
    else:
        await sio.emit('error', {'message': 'timesheet_id required'}, room=sid)


@sio.event
async def ping(sid, data):
    """Handle ping for connection keepalive"""
    await sio.emit('pong', {'timestamp': data.get('timestamp')}, room=sid)


# Export both sio and ws_manager
__all__ = ['sio', 'ws_manager']
