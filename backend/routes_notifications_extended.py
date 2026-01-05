"""
Extended Notification Routes
Adds in-app notification pop-ups and read/unread tracking
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone
import logging

from notification_models_extended import UserNotificationStatus, NotificationWithStatus
from auth import get_current_user, get_organization_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications-extended"])

# Database will be injected
db = None

def set_db(database):
    global db
    db = database


@router.get("/unread")
async def get_unread_notifications(
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get all unread notifications for current user
    
    Called when user logs in to show pop-ups
    """
    try:
        user_id = current_user.get('user_id')
        
        # Get user's notification preferences
        prefs = await db.user_notification_preferences.find_one(
            {"user_id": user_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        # Get all notifications for organization (sent to "all")
        notifications = await db.notifications.find(
            {
                "organization_id": organization_id,
                "send_in_app": True,
                "status": "sent"
            },
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        # Get user's read status for these notifications
        notification_ids = [n['id'] for n in notifications]
        read_statuses = await db.user_notification_status.find(
            {
                "user_id": user_id,
                "notification_id": {"$in": notification_ids}
            },
            {"_id": 0}
        ).to_list(1000)
        
        # Create lookup dict
        status_lookup = {s['notification_id']: s for s in read_statuses}
        
        # Filter unread notifications based on user preferences
        unread = []
        for notif in notifications:
            # Check if user wants this type of notification
            if prefs:
                type_field_map = {
                    "medicaid_update": "medicaid_updates",
                    "sandata_alert": "sandata_alerts",
                    "availity_alert": "availity_alerts",
                    "odm_notice": "odm_notices",
                    "system_alert": "system_alerts"
                }
                pref_field = type_field_map.get(notif['type'])
                if pref_field and not prefs.get(pref_field, True):
                    continue
            
            # Check if already read
            status = status_lookup.get(notif['id'])
            if not status or not status.get('read'):
                # Add read status to notification
                notif['read'] = False
                notif['dismissed'] = status.get('dismissed', False) if status else False
                unread.append(notif)
        
        return {
            "status": "success",
            "count": len(unread),
            "notifications": unread
        }
    
    except Exception as e:
        logger.error(f"Get unread notifications error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Mark a notification as read for current user
    """
    try:
        user_id = current_user.get('user_id')
        
        # Check if status record exists
        existing = await db.user_notification_status.find_one(
            {
                "user_id": user_id,
                "notification_id": notification_id
            },
            {"_id": 0}
        )
        
        if existing:
            # Update existing
            await db.user_notification_status.update_one(
                {"user_id": user_id, "notification_id": notification_id},
                {
                    "$set": {
                        "read": True,
                        "read_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        else:
            # Create new status record
            status = UserNotificationStatus(
                user_id=user_id,
                notification_id=notification_id,
                organization_id=organization_id,
                read=True,
                read_at=datetime.now(timezone.utc),
                shown_in_app=True,
                shown_at=datetime.now(timezone.utc)
            )
            
            doc = status.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            doc['read_at'] = doc['read_at'].isoformat()
            doc['shown_at'] = doc['shown_at'].isoformat()
            if doc.get('dismissed_at'):
                doc['dismissed_at'] = doc['dismissed_at'].isoformat()
            
            await db.user_notification_status.insert_one(doc)
        
        return {"status": "success", "message": "Notification marked as read"}
    
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dismiss/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Dismiss a notification (mark as read and dismissed)
    """
    try:
        user_id = current_user.get('user_id')
        
        existing = await db.user_notification_status.find_one(
            {"user_id": user_id, "notification_id": notification_id},
            {"_id": 0}
        )
        
        now = datetime.now(timezone.utc).isoformat()
        
        if existing:
            await db.user_notification_status.update_one(
                {"user_id": user_id, "notification_id": notification_id},
                {
                    "$set": {
                        "read": True,
                        "read_at": now,
                        "dismissed": True,
                        "dismissed_at": now,
                        "updated_at": now
                    }
                }
            )
        else:
            status = UserNotificationStatus(
                user_id=user_id,
                notification_id=notification_id,
                organization_id=organization_id,
                read=True,
                read_at=datetime.now(timezone.utc),
                dismissed=True,
                dismissed_at=datetime.now(timezone.utc),
                shown_in_app=True,
                shown_at=datetime.now(timezone.utc)
            )
            
            doc = status.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            doc['updated_at'] = doc['updated_at'].isoformat()
            doc['read_at'] = doc['read_at'].isoformat()
            doc['dismissed_at'] = doc['dismissed_at'].isoformat()
            doc['shown_at'] = doc['shown_at'].isoformat()
            
            await db.user_notification_status.insert_one(doc)
        
        return {"status": "success", "message": "Notification dismissed"}
    
    except Exception as e:
        logger.error(f"Dismiss notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Get count of unread notifications for badge display
    """
    try:
        user_id = current_user.get('user_id')
        
        # Get user preferences
        prefs = await db.user_notification_preferences.find_one(
            {"user_id": user_id, "organization_id": organization_id},
            {"_id": 0}
        )
        
        # Get all notifications
        notifications = await db.notifications.find(
            {
                "organization_id": organization_id,
                "send_in_app": True,
                "status": "sent"
            },
            {"_id": 0, "id": 1, "type": 1}
        ).to_list(1000)
        
        notification_ids = [n['id'] for n in notifications]
        
        # Get read statuses
        read_statuses = await db.user_notification_status.find(
            {
                "user_id": user_id,
                "notification_id": {"$in": notification_ids},
                "read": True
            },
            {"_id": 0, "notification_id": 1}
        ).to_list(1000)
        
        read_ids = {s['notification_id'] for s in read_statuses}
        
        # Count unread, filtering by preferences
        unread_count = 0
        for notif in notifications:
            if notif['id'] in read_ids:
                continue
            
            # Check preferences
            if prefs:
                type_field_map = {
                    "medicaid_update": "medicaid_updates",
                    "sandata_alert": "sandata_alerts",
                    "availity_alert": "availity_alerts",
                    "odm_notice": "odm_notices",
                    "system_alert": "system_alerts"
                }
                pref_field = type_field_map.get(notif['type'])
                if pref_field and not prefs.get(pref_field, True):
                    continue
            
            unread_count += 1
        
        return {
            "status": "success",
            "unread_count": unread_count
        }
    
    except Exception as e:
        logger.error(f"Get unread count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    organization_id: str = Depends(get_organization_from_token)
):
    """
    Mark all notifications as read for current user
    """
    try:
        user_id = current_user.get('user_id')
        
        # Get all notifications
        notifications = await db.notifications.find(
            {"organization_id": organization_id, "send_in_app": True},
            {"_id": 0, "id": 1}
        ).to_list(1000)
        
        notification_ids = [n['id'] for n in notifications]
        
        # Get existing statuses
        existing = await db.user_notification_status.find(
            {"user_id": user_id, "notification_id": {"$in": notification_ids}},
            {"_id": 0, "notification_id": 1}
        ).to_list(1000)
        
        existing_ids = {s['notification_id'] for s in existing}
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Update existing
        if existing_ids:
            await db.user_notification_status.update_many(
                {"user_id": user_id, "notification_id": {"$in": list(existing_ids)}},
                {"$set": {"read": True, "read_at": now, "updated_at": now}}
            )
        
        # Create new for notifications without status
        new_ids = set(notification_ids) - existing_ids
        if new_ids:
            new_statuses = []
            for notif_id in new_ids:
                status = UserNotificationStatus(
                    user_id=user_id,
                    notification_id=notif_id,
                    organization_id=organization_id,
                    read=True,
                    read_at=datetime.now(timezone.utc)
                )
                doc = status.model_dump()
                doc['created_at'] = doc['created_at'].isoformat()
                doc['updated_at'] = doc['updated_at'].isoformat()
                doc['read_at'] = doc['read_at'].isoformat()
                if doc.get('dismissed_at'):
                    doc['dismissed_at'] = doc['dismissed_at'].isoformat()
                if doc.get('shown_at'):
                    doc['shown_at'] = doc['shown_at'].isoformat()
                new_statuses.append(doc)
            
            if new_statuses:
                await db.user_notification_status.insert_many(new_statuses)
        
        return {
            "status": "success",
            "message": f"Marked {len(notification_ids)} notifications as read"
        }
    
    except Exception as e:
        logger.error(f"Mark all read error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
