"""
Notification System for AZAI

Handles email notifications for:
- Medicaid updates and delays
- Sandata status updates
- Availity status updates
- ODM notifications
- System alerts
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)


class NotificationTemplate(BaseModel):
    """Email template for notifications"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # medicaid_update, sandata_alert, availity_alert, odm_notice, system_alert
    subject_template: str
    body_template: str  # Supports {variable} placeholders
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Notification(BaseModel):
    """Individual notification record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Notification details
    type: str  # medicaid_update, sandata_alert, availity_alert, odm_notice, system_alert, custom
    category: str  # update, delay, error, success, warning, info
    title: str
    message: str
    
    # Source information
    source: str  # medicaid, sandata, availity, odm, system, admin
    source_reference: Optional[str] = None  # External reference ID
    
    # Recipients
    recipients: List[str] = []  # List of user IDs or "all"
    recipient_emails: List[str] = []  # Resolved email addresses
    
    # Delivery
    send_email: bool = True
    send_in_app: bool = True
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    
    # Priority
    priority: str = "normal"  # low, normal, high, urgent
    
    # Status
    status: str = "pending"  # pending, sent, failed, scheduled
    scheduled_for: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None  # User ID who created


class UserNotificationPreference(BaseModel):
    """User notification preferences"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    organization_id: str
    email: EmailStr
    
    # Email preferences
    email_enabled: bool = True
    
    # Notification type preferences
    medicaid_updates: bool = True
    sandata_alerts: bool = True
    availity_alerts: bool = True
    odm_notices: bool = True
    system_alerts: bool = True
    
    # Frequency
    digest_mode: bool = False  # If true, send daily digest instead of immediate
    digest_time: str = "09:00"  # Time to send daily digest
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailService:
    """Email sending service"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@azai.com')
        self.from_name = os.getenv('FROM_NAME', 'AZAI Notifications')
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> Dict:
        """
        Send email using SMTP
        
        Returns:
            Dict with status and details
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text version
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            return {
                "status": "success",
                "recipients": to_emails,
                "sent_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "recipients": to_emails
            }


class NotificationService:
    """Main notification service"""
    
    def __init__(self, db):
        self.db = db
        self.email_service = EmailService()
    
    async def create_notification(
        self,
        organization_id: str,
        notification_type: str,
        category: str,
        title: str,
        message: str,
        source: str,
        recipients: List[str] = None,
        send_email: bool = True,
        priority: str = "normal",
        metadata: Dict = None,
        created_by: str = None
    ) -> Notification:
        """
        Create and send a notification
        
        Args:
            recipients: List of user IDs or ["all"] for all users
        """
        # Create notification
        # ALWAYS send email alongside in-app notification
        notification = Notification(
            organization_id=organization_id,
            type=notification_type,
            category=category,
            title=title,
            message=message,
            source=source,
            recipients=recipients or ["all"],
            send_email=True,  # Always send email
            send_in_app=True,  # Always show in app
            priority=priority,
            metadata=metadata,
            created_by=created_by
        )
        
        # Resolve recipient emails
        recipient_emails = await self._resolve_recipients(
            organization_id,
            notification.recipients,
            notification_type
        )
        notification.recipient_emails = recipient_emails
        
        # Save to database
        doc = notification.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        if doc.get('email_sent_at'):
            doc['email_sent_at'] = doc['email_sent_at'].isoformat()
        if doc.get('scheduled_for'):
            doc['scheduled_for'] = doc['scheduled_for'].isoformat()
        
        await self.db.notifications.insert_one(doc)
        
        # Send email if requested
        if send_email and recipient_emails:
            await self._send_notification_email(notification)
        
        logger.info(
            f"Notification created: {notification.id} - "
            f"Type: {notification_type}, Recipients: {len(recipient_emails)}"
        )
        
        return notification
    
    async def _resolve_recipients(
        self,
        organization_id: str,
        recipient_ids: List[str],
        notification_type: str
    ) -> List[str]:
        """
        Resolve recipient IDs to email addresses based on preferences
        """
        emails = []
        
        if "all" in recipient_ids:
            # Get all users in organization with preferences
            prefs = await self.db.user_notification_preferences.find(
                {
                    "organization_id": organization_id,
                    "email_enabled": True
                },
                {"_id": 0}
            ).to_list(10000)
            
            # Filter by notification type preference
            type_field_map = {
                "medicaid_update": "medicaid_updates",
                "sandata_alert": "sandata_alerts",
                "availity_alert": "availity_alerts",
                "odm_notice": "odm_notices",
                "system_alert": "system_alerts"
            }
            
            pref_field = type_field_map.get(notification_type, None)
            
            for pref in prefs:
                # Check if user wants this type of notification
                if pref_field and not pref.get(pref_field, True):
                    continue
                emails.append(pref['email'])
        else:
            # Get specific users
            for user_id in recipient_ids:
                user = await self.db.users.find_one({"id": user_id}, {"_id": 0})
                if user and user.get('email'):
                    # Check user preferences
                    pref = await self.db.user_notification_preferences.find_one(
                        {"user_id": user_id, "email_enabled": True},
                        {"_id": 0}
                    )
                    if pref:
                        emails.append(user['email'])
        
        return list(set(emails))  # Remove duplicates
    
    async def _send_notification_email(self, notification: Notification):
        """
        Send notification via email
        """
        if not notification.recipient_emails:
            return
        
        # Build email content
        html_body = self._build_email_html(notification)
        text_body = self._build_email_text(notification)
        
        # Send email
        result = self.email_service.send_email(
            to_emails=notification.recipient_emails,
            subject=notification.title,
            body_html=html_body,
            body_text=text_body
        )
        
        # Update notification status
        update_data = {}
        if result['status'] == 'success':
            update_data = {
                "email_sent": True,
                "email_sent_at": datetime.now(timezone.utc),
                "status": "sent"
            }
        else:
            update_data = {
                "email_sent": False,
                "status": "failed",
                "metadata": {
                    **(notification.metadata or {}),
                    "email_error": result.get('error')
                }
            }
        
        await self.db.notifications.update_one(
            {"id": notification.id},
            {"$set": update_data}
        )
    
    def _build_email_html(self, notification: Notification) -> str:
        """
        Build HTML email body
        """
        # Priority badge
        priority_colors = {
            "low": "#6B7280",
            "normal": "#3B82F6",
            "high": "#F59E0B",
            "urgent": "#EF4444"
        }
        priority_color = priority_colors.get(notification.priority, "#3B82F6")
        
        # Category icon
        category_icons = {
            "update": "📢",
            "delay": "⏰",
            "error": "❌",
            "success": "✅",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        icon = category_icons.get(notification.category, "📬")
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{notification.title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f3f4f6;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f3f4f6; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {priority_color}; padding: 20px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">{icon} AZAI Notification</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 30px;">
                            <h2 style="margin: 0 0 10px 0; color: #1f2937; font-size: 20px;">{notification.title}</h2>
                            <p style="margin: 0 0 5px 0; color: #6b7280; font-size: 14px;">
                                <strong>Source:</strong> {notification.source.upper()} | 
                                <strong>Type:</strong> {notification.type.replace('_', ' ').title()} |
                                <strong>Priority:</strong> {notification.priority.upper()}
                            </p>
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                            <div style="color: #374151; font-size: 16px; line-height: 1.6;">
                                {notification.message.replace(chr(10), '<br>')}
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px; text-align: center;">
                                This notification was sent by AZAI Healthcare Timesheet System<br>
                                {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')}
                            </p>
                            <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 12px; text-align: center;">
                                To manage notification preferences, log in to your AZAI account
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        return html
    
    def _build_email_text(self, notification: Notification) -> str:
        """
        Build plain text email body
        """
        text = f"""
AZAI NOTIFICATION
{'=' * 50}

Title: {notification.title}
Source: {notification.source.upper()}
Type: {notification.type.replace('_', ' ').title()}
Priority: {notification.priority.upper()}
Category: {notification.category.upper()}

{'=' * 50}

{notification.message}

{'=' * 50}

Sent: {datetime.now(timezone.utc).strftime('%B %d, %Y at %I:%M %p UTC')}

This notification was sent by AZAI Healthcare Timesheet System.
To manage notification preferences, log in to your AZAI account.
        """
        return text
