"""
Notification Controller
API endpoints for notification management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from services.notification_service import NotificationService

router = APIRouter()


class SubscriptionRequest(BaseModel):
    project_id: str
    user_id: str
    channels: List[str]  # ["email", "slack", "discord", "webhook", "in_app"]
    notification_types: List[str]  # ["critical_issue", "quality_improvement", etc.]


class NotificationMarkRequest(BaseModel):
    notification_id: str


@router.post("/notifications/subscribe")
async def subscribe_to_notifications(request: SubscriptionRequest):
    """Subscribe user to project notifications"""
    notification_service = NotificationService(None)
    result = await notification_service.subscribe(
        request.project_id,
        request.user_id,
        request.channels,
        request.notification_types
    )
    return result


@router.post("/notifications/unsubscribe")
async def unsubscribe_from_notifications(project_id: str, user_id: str):
    """Unsubscribe user from project notifications"""
    notification_service = NotificationService(None)
    result = await notification_service.unsubscribe(project_id, user_id)
    return result


@router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    project_id: Optional[str] = Query(None),
    unread_only: bool = Query(False)
):
    """Get notifications for a user"""
    notification_service = NotificationService(None)
    notifications = await notification_service.get_notifications(
        user_id, project_id, unread_only
    )
    return {"notifications": notifications}


@router.post("/notifications/mark-read")
async def mark_notification_read(request: NotificationMarkRequest):
    """Mark notification as read"""
    notification_service = NotificationService(None)
    result = await notification_service.mark_as_read(request.notification_id)
    return result


@router.post("/notifications/test")
async def test_notification(
    project_id: str,
    user_id: str,
    channel: str = Query("in_app")
):
    """Send a test notification"""
    notification_service = NotificationService(None)
    
    # Subscribe user first
    await notification_service.subscribe(
        project_id, user_id, [channel], ["scan_complete"]
    )
    
    # Send test notification
    result = await notification_service.notify(
        project_id=project_id,
        notification_type="scan_complete",
        data={"message": "This is a test notification", "test": True},
        severity="info"
    )
    
    return result
