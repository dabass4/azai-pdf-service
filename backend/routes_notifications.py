"""
Notification API Routes

Endpoints for managing notifications and preferences
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone
import logging

from notification_system import (
    Notification,
    UserNotificationPreference,
    NotificationService
)
from auth import get_current_user, get_organization_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Database will be injected
db = None

def set_db(database):
    global db
    db = database


class CreateNotificationRequest(BaseModel):
    """Request to create notification"""
    type: str  # medicaid_update, sandata_alert, availity_alert, odm_notice, system_alert, custom
    category: str  # update, delay, error, success, warning, info
    title: str
    message: str
    source: str  # medicaid, sandata, availity, odm, system, admin
    recipients: List[str] = ["all"]  # List of user IDs or ["all"]
    send_email: bool = True
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Optional[Dict] = None


class UpdatePreferencesRequest(BaseModel):
    """Request to update notification preferences"""
    email_enabled: Optional[bool] = None
    medicaid_updates: Optional[bool] = None
    sandata_alerts: Optional[bool] = None
    availity_alerts: Optional[bool] = None
    odm_notices: Optional[bool] = None
    system_alerts: Optional[bool] = None
    digest_mode: Optional[bool] = None
    digest_time: Optional[str] = None


# ========================================
# NOTIFICATION CRUD
# ========================================

@router.post("/send")
async def send_notification(
    request: CreateNotificationRequest,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Create and send a notification
    
    Admin only endpoint for sending notifications to users
    """
    try:
        # Check if user is admin
        if not current_user.get('is_admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can send notifications"
            )
        
        # Create notification service
        notification_service = NotificationService(db)
        
        # Create and send notification
        notification = await notification_service.create_notification(
            organization_id=organization_id,
            notification_type=request.type,
            category=request.category,
            title=request.title,
            message=request.message,
            source=request.source,
            recipients=request.recipients,
            send_email=request.send_email,
            priority=request.priority,
            metadata=request.metadata,
            created_by=current_user.get('user_id')
        )
        
        return {
            "status": "success",
            "message": f"Notification sent to {len(notification.recipient_emails)} recipients",
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "recipients_count": len(notification.recipient_emails),
                "email_sent": notification.email_sent
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_notifications(
    type: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get list of notifications for organization
    """
    try:
        query = {"organization_id": organization_id}
        
        if type:
            query["type"] = type
        if category:
            query["category"] = category
        if priority:
            query["priority"] = priority
        
        notifications = await db.notifications.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "status": "success",
            "count": len(notifications),
            "notifications": notifications
        }
    
    except Exception as e:
        logger.error(f"List notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get specific notification details
    """
    try:
        notification = await db.notifications.find_one(
            {"id": notification_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"status": "success", "notification": notification}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# USER PREFERENCES
# ========================================

@router.get("/preferences/me")
async def get_my_preferences(
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get current user's notification preferences
    """
    try:
        user_id = current_user.get('user_id')
        
        # Get or create preferences
        prefs = await db.user_notification_preferences.find_one(
            {"user_id": user_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        if not prefs:
            # Create default preferences
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            prefs = UserNotificationPreference(
                user_id=user_id,
                organization_id=organization_id,
                email=user['email']
            )
            
            doc = prefs.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            
            await db.user_notification_preferences.insert_one(doc)
            prefs = doc
        
        return {"status": "success", "preferences": prefs}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/me")
async def update_my_preferences(
    request: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Update current user's notification preferences
    """
    try:
        user_id = current_user.get('user_id')
        
        # Build update document
        update_data = {}
        if request.email_enabled is not None:
            update_data["email_enabled"] = request.email_enabled
        if request.medicaid_updates is not None:
            update_data["medicaid_updates"] = request.medicaid_updates
        if request.sandata_alerts is not None:
            update_data["sandata_alerts"] = request.sandata_alerts
        if request.availity_alerts is not None:
            update_data["availity_alerts"] = request.availity_alerts
        if request.odm_notices is not None:
            update_data["odm_notices"] = request.odm_notices
        if request.system_alerts is not None:
            update_data["system_alerts"] = request.system_alerts
        if request.digest_mode is not None:
            update_data["digest_mode"] = request.digest_mode
        if request.digest_time is not None:
            update_data["digest_time"] = request.digest_time
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update preferences
        result = await db.user_notification_preferences.update_one(
            {"user_id": user_id, "organization_id": organization_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Preferences not found")
        
        # Get updated preferences
        prefs = await db.user_notification_preferences.find_one(
            {"user_id": user_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        return {
            "status": "success",
            "message": "Preferences updated",
            "preferences": prefs
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# WEBHOOK ENDPOINTS (for external integrations)
# ========================================

@router.post("/webhook/sandata")
async def sandata_webhook(
    payload: Dict,
    organization_id: str = Query(...)
):
    """
    Webhook endpoint for Sandata notifications
    
    Sandata can POST status updates here
    """
    try:
        logger.info(f"Sandata webhook received: {payload}")
        
        # Create notification from Sandata update
        notification_service = NotificationService(db)
        
        # Parse Sandata payload
        title = payload.get('title', 'Sandata Status Update')
        message = payload.get('message', str(payload))
        category = payload.get('status', 'info').lower()  # success, error, warning, info
        
        await notification_service.create_notification(
            organization_id=organization_id,
            notification_type="sandata_alert",
            category=category,
            title=title,
            message=message,
            source="sandata",
            recipients=["all"],
            send_email=True,
            priority="normal" if category == "info" else "high",
            metadata=payload
        )
        
        return {"status": "success", "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"Sandata webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/availity")
async def availity_webhook(
    payload: Dict,
    organization_id: str = Query(...)
):
    """
    Webhook endpoint for Availity notifications
    """
    try:
        logger.info(f"Availity webhook received: {payload}")
        
        notification_service = NotificationService(db)
        
        title = payload.get('title', 'Availity Status Update')
        message = payload.get('message', str(payload))
        category = payload.get('status', 'info').lower()
        
        await notification_service.create_notification(
            organization_id=organization_id,
            notification_type="availity_alert",
            category=category,
            title=title,
            message=message,
            source="availity",
            recipients=["all"],
            send_email=True,
            priority="normal" if category == "info" else "high",
            metadata=payload
        )
        
        return {"status": "success", "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"Availity webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/odm")
async def odm_webhook(
    payload: Dict,
    organization_id: str = Query(...)
):
    """
    Webhook endpoint for ODM (Ohio Department of Medicaid) notifications
    """
    try:
        logger.info(f"ODM webhook received: {payload}")
        
        notification_service = NotificationService(db)
        
        title = payload.get('title', 'ODM Notice')
        message = payload.get('message', str(payload))
        category = payload.get('type', 'info').lower()
        
        await notification_service.create_notification(
            organization_id=organization_id,
            notification_type="odm_notice",
            category=category,
            title=title,
            message=message,
            source="odm",
            recipients=["all"],
            send_email=True,
            priority="high",  # ODM notices usually important
            metadata=payload
        )
        
        return {"status": "success", "message": "Webhook processed"}
    
    except Exception as e:
        logger.error(f"ODM webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
