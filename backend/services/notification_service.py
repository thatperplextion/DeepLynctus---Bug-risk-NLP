"""
Notification Service
Handles real-time alerts, email notifications, and third-party integrations
"""

from typing import List, Dict, Optional
from datetime import datetime
import asyncio
from enum import Enum
import json


class NotificationType(Enum):
    CRITICAL_ISSUE = "critical_issue"
    HIGH_RISK_FILE = "high_risk_file"
    QUALITY_IMPROVEMENT = "quality_improvement"
    QUALITY_DEGRADATION = "quality_degradation"
    SCAN_COMPLETE = "scan_complete"
    REGRESSION_DETECTED = "regression_detected"


class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationService:
    """Manages notifications across multiple channels"""
    
    def __init__(self, db):
        self.db = db
        self.subscribers = {}
        self.notification_history = []
        
    async def subscribe(self, project_id: str, user_id: str, channels: List[str], 
                       notification_types: List[str]):
        """Subscribe user to notifications for a project"""
        key = f"{project_id}:{user_id}"
        self.subscribers[key] = {
            "project_id": project_id,
            "user_id": user_id,
            "channels": channels,
            "notification_types": notification_types,
            "created_at": datetime.utcnow().isoformat()
        }
        return {"status": "subscribed", "subscriber_key": key}
    
    async def unsubscribe(self, project_id: str, user_id: str):
        """Unsubscribe user from project notifications"""
        key = f"{project_id}:{user_id}"
        if key in self.subscribers:
            del self.subscribers[key]
            return {"status": "unsubscribed"}
        return {"status": "not_found"}
    
    async def notify(self, project_id: str, notification_type: str, 
                    data: Dict, severity: str = "info"):
        """Send notification to all subscribers"""
        notifications_sent = []
        
        for key, subscriber in self.subscribers.items():
            if subscriber["project_id"] != project_id:
                continue
                
            if notification_type not in subscriber["notification_types"]:
                continue
            
            notification = {
                "id": f"notif_{datetime.utcnow().timestamp()}",
                "project_id": project_id,
                "type": notification_type,
                "severity": severity,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "read": False
            }
            
            for channel in subscriber["channels"]:
                await self._send_to_channel(channel, notification, subscriber["user_id"])
                
            notifications_sent.append(notification)
            self.notification_history.append(notification)
        
        return {
            "notifications_sent": len(notifications_sent),
            "details": notifications_sent
        }
    
    async def _send_to_channel(self, channel: str, notification: Dict, user_id: str):
        """Send notification to specific channel"""
        if channel == "email":
            await self._send_email(notification, user_id)
        elif channel == "slack":
            await self._send_slack(notification, user_id)
        elif channel == "discord":
            await self._send_discord(notification, user_id)
        elif channel == "webhook":
            await self._send_webhook(notification, user_id)
        elif channel == "in_app":
            await self._store_in_app_notification(notification, user_id)
    
    async def _send_email(self, notification: Dict, user_id: str):
        """Send email notification"""
        # Integration with SMTP server or service like SendGrid
        print(f"📧 Email sent to {user_id}: {notification['type']}")
        # TODO: Implement actual email sending
        pass
    
    async def _send_slack(self, notification: Dict, user_id: str):
        """Send Slack notification"""
        # Integration with Slack Webhooks
        severity_emoji = {
            "critical": "🔴",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }
        
        message = {
            "text": f"{severity_emoji.get(notification['severity'], '📢')} *{notification['type'].upper()}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Project:* {notification['project_id']}\n*Type:* {notification['type']}\n*Severity:* {notification['severity']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:* {json.dumps(notification['data'], indent=2)}"
                    }
                }
            ]
        }
        
        print(f"💬 Slack message sent: {message['text']}")
        # TODO: Send to actual Slack webhook
        pass
    
    async def _send_discord(self, notification: Dict, user_id: str):
        """Send Discord notification"""
        # Integration with Discord Webhooks
        severity_color = {
            "critical": 0xFF0000,  # Red
            "warning": 0xFFA500,   # Orange
            "info": 0x0099FF,      # Blue
            "success": 0x00FF00    # Green
        }
        
        embed = {
            "title": notification['type'].replace('_', ' ').title(),
            "description": f"Project: {notification['project_id']}",
            "color": severity_color.get(notification['severity'], 0x0099FF),
            "fields": [
                {
                    "name": "Severity",
                    "value": notification['severity'].upper(),
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": notification['timestamp'],
                    "inline": True
                }
            ],
            "footer": {
                "text": "Bug Risk NLP Alert System"
            }
        }
        
        print(f"🎮 Discord notification sent: {embed['title']}")
        # TODO: Send to actual Discord webhook
        pass
    
    async def _send_webhook(self, notification: Dict, user_id: str):
        """Send generic webhook notification"""
        # TODO: Implement webhook POST request
        print(f"🔗 Webhook triggered for {user_id}")
        pass
    
    async def _store_in_app_notification(self, notification: Dict, user_id: str):
        """Store notification in database for in-app display"""
        # Store in database for user's notification center
        print(f"💾 In-app notification stored for {user_id}")
        pass
    
    async def get_notifications(self, user_id: str, project_id: Optional[str] = None, 
                               unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        notifications = [
            n for n in self.notification_history
            if (not project_id or n['project_id'] == project_id)
            and (not unread_only or not n['read'])
        ]
        return notifications[-50:]  # Return last 50 notifications
    
    async def mark_as_read(self, notification_id: str):
        """Mark notification as read"""
        for notification in self.notification_history:
            if notification['id'] == notification_id:
                notification['read'] = True
                return {"status": "marked_read"}
        return {"status": "not_found"}
    
    async def check_and_notify_critical_issues(self, project_id: str, scan_results: Dict):
        """Check scan results and send critical issue notifications"""
        critical_files = [
            f for f in scan_results.get('files', [])
            if f.get('risk_score', 0) >= 0.8
        ]
        
        if critical_files:
            await self.notify(
                project_id=project_id,
                notification_type=NotificationType.CRITICAL_ISSUE.value,
                data={
                    "critical_files": len(critical_files),
                    "files": [f['path'] for f in critical_files[:5]],
                    "message": f"Found {len(critical_files)} critical risk files"
                },
                severity="critical"
            )
    
    async def check_and_notify_regression(self, project_id: str, 
                                         comparison_result: Dict):
        """Notify about code quality regression"""
        if comparison_result.get('regression_detected'):
            new_issues = comparison_result.get('new_issues', [])
            
            await self.notify(
                project_id=project_id,
                notification_type=NotificationType.REGRESSION_DETECTED.value,
                data={
                    "new_issues_count": len(new_issues),
                    "quality_change": comparison_result.get('quality_change', 0),
                    "message": f"Code quality regression detected: {len(new_issues)} new issues"
                },
                severity="warning"
            )
    
    async def notify_quality_improvement(self, project_id: str, 
                                        improvement_data: Dict):
        """Notify about code quality improvements"""
        await self.notify(
            project_id=project_id,
            notification_type=NotificationType.QUALITY_IMPROVEMENT.value,
            data=improvement_data,
            severity="success"
        )
