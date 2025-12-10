"""
Extended Notification Models
Adds read/unread status tracking per user
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid


class UserNotificationStatus(BaseModel):
    """Tracks which notifications each user has read"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    notification_id: str
    organization_id: str
    
    # Status
    read: bool = False
    read_at: Optional[datetime] = None
    dismissed: bool = False
    dismissed_at: Optional[datetime] = None
    
    # Delivery tracking
    shown_in_app: bool = False
    shown_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NotificationWithStatus(BaseModel):
    """Notification with user-specific read status"""
    # Notification fields
    id: str
    type: str
    category: str
    title: str
    message: str
    source: str
    priority: str
    created_at: datetime
    
    # User-specific status
    read: bool = False
    read_at: Optional[datetime] = None
    dismissed: bool = False
