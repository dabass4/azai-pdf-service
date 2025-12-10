# AZAI Notification System - Complete Guide

**Email Notifications for Medicaid, Sandata, Availity, and ODM Updates**

---

## 🎯 Overview

The AZAI notification system allows administrators to send email notifications to all users about:
- **Medicaid updates and delays**
- **Sandata status updates and alerts**
- **Availity clearinghouse notifications**
- **ODM (Ohio Department of Medicaid) notices**
- **System alerts and announcements**

---

## 📊 System Components

### Backend Components

**1. `/app/backend/notification_system.py`**
- Core notification models
- Email service (SMTP)
- Notification service logic
- Email template builder

**Models:**
- `Notification` - Individual notification records
- `UserNotificationPreference` - User email preferences
- `EmailService` - SMTP email sending
- `NotificationService` - Main notification logic

**2. `/app/backend/routes_notifications.py`**
- REST API endpoints
- Notification CRUD operations
- User preference management
- Webhook endpoints for external integrations

### Frontend Components

**1. `/app/frontend/src/pages/NotificationCenter.js`**
- Admin interface for sending notifications
- Notification history viewer
- Send notification form

**2. `/app/frontend/src/pages/NotificationPreferences.js`**
- User preference management
- Email notification toggles
- Per-type notification control

---

## 🔐 Access Control

### Admin Users:
- Send notifications to all users
- View notification history
- Access Notification Center (`/notifications`)

### Regular Users:
- Receive notifications via email
- Manage their preferences (`/notification-preferences`)
- Control which types of notifications they receive

---

## 📧 Email Configuration

### SMTP Setup

Add these environment variables to `/app/backend/.env`:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@azai.com
FROM_NAME=AZAI Notifications
```

### Email Service Providers

**Option 1: Gmail (For Testing)**
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

**How to get Gmail App Password:**
1. Go to Google Account settings
2. Security → 2-Step Verification (enable if not enabled)
3. App passwords → Generate new app password
4. Use generated password in SMTP_PASSWORD

**Option 2: SendGrid (Production)**
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

**Option 3: AWS SES**
```
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-user
SMTP_PASSWORD=your-ses-smtp-password
```

**Option 4: Mailgun**
```
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your-mailgun-smtp-password
```

---

## 🚀 API Endpoints

### Send Notification (Admin Only)

**POST** `/api/notifications/send`

**Headers:**
```
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "medicaid_update",
  "category": "delay",
  "title": "Medicaid Processing Delay - Week of Dec 10",
  "message": "Due to system maintenance, Medicaid claim processing will be delayed by 2-3 business days this week. Please plan accordingly.",
  "source": "medicaid",
  "recipients": ["all"],
  "send_email": true,
  "priority": "high"
}
```

**Notification Types:**
- `medicaid_update` - Medicaid updates
- `sandata_alert` - Sandata status updates
- `availity_alert` - Availity notifications
- `odm_notice` - ODM official notices
- `system_alert` - System announcements
- `custom` - Custom notifications

**Categories:**
- `info` - Informational
- `update` - General updates
- `delay` - Service delays
- `warning` - Warnings
- `error` - Errors/issues
- `success` - Success messages

**Priority Levels:**
- `low` - Low priority
- `normal` - Normal priority
- `high` - High priority
- `urgent` - Urgent (red flag)

**Response:**
```json
{
  "status": "success",
  "message": "Notification sent to 25 recipients",
  "notification": {
    "id": "notification-uuid",
    "title": "Medicaid Processing Delay...",
    "recipients_count": 25,
    "email_sent": true
  }
}
```

---

### Get Notification List

**GET** `/api/notifications/list?type=medicaid_update&limit=50`

**Query Parameters:**
- `type` - Filter by notification type
- `category` - Filter by category
- `priority` - Filter by priority
- `limit` - Max results (default 50)

**Response:**
```json
{
  "status": "success",
  "count": 15,
  "notifications": [
    {
      "id": "notif-uuid",
      "type": "medicaid_update",
      "category": "delay",
      "title": "Medicaid Processing Delay",
      "message": "Due to system maintenance...",
      "priority": "high",
      "email_sent": true,
      "recipient_emails": ["user1@example.com", "user2@example.com"],
      "created_at": "2025-12-10T10:00:00Z"
    }
  ]
}
```

---

### Get User Preferences

**GET** `/api/notifications/preferences/me`

**Response:**
```json
{
  "status": "success",
  "preferences": {
    "user_id": "user-uuid",
    "email": "user@example.com",
    "email_enabled": true,
    "medicaid_updates": true,
    "sandata_alerts": true,
    "availity_alerts": true,
    "odm_notices": true,
    "system_alerts": true,
    "digest_mode": false
  }
}
```

---

### Update User Preferences

**PUT** `/api/notifications/preferences/me`

**Request Body:**
```json
{
  "email_enabled": true,
  "medicaid_updates": true,
  "sandata_alerts": false,
  "availity_alerts": true,
  "odm_notices": true,
  "system_alerts": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Preferences updated",
  "preferences": { ... }
}
```

---

## 🔗 Webhook Endpoints (External Integrations)

These endpoints allow Sandata, Availity, and ODM to send automatic notifications to your users.

### Sandata Webhook

**POST** `/api/notifications/webhook/sandata?organization_id={org-id}`

**Request Body:**
```json
{
  "title": "Sandata Claim Processed",
  "message": "Claim #12345 has been successfully processed and accepted.",
  "status": "success"
}
```

**Auto-creates notification:**
- Type: `sandata_alert`
- Sends email to all users with Sandata alerts enabled
- Priority: High (if status is error/warning), Normal (if success/info)

---

### Availity Webhook

**POST** `/api/notifications/webhook/availity?organization_id={org-id}`

**Request Body:**
```json
{
  "title": "Eligibility Check Complete",
  "message": "Eligibility verification for Patient Jane Smith completed.",
  "status": "info"
}
```

---

### ODM Webhook

**POST** `/api/notifications/webhook/odm?organization_id={org-id}`

**Request Body:**
```json
{
  "title": "ODM System Maintenance Notice",
  "message": "ODM systems will be down for maintenance Dec 15-16.",
  "type": "warning"
}
```

---

## 📱 Frontend Usage

### Admin: Send Notification

1. Navigate to `/notifications` (Notification Center)
2. Click "Send Notification"
3. Fill in form:
   - Type: Select notification type
   - Category: Select category
   - Priority: Select priority level
   - Title: Enter notification title
   - Message: Enter message body
   - Send Email: Check to send email (default checked)
4. Click "Send to All Users"
5. Confirmation: Shows number of recipients

**Screenshot Flow:**
```
/notifications → [Send Notification] → Form → [Send] → Success!
```

---

### User: Manage Preferences

1. Navigate to `/notification-preferences`
2. Toggle "Email Notifications" master switch
3. Enable/disable specific notification types:
   - ✅ Medicaid Updates
   - ✅ Sandata Alerts
   - ✅ Availity Alerts
   - ✅ ODM Notices
   - ✅ System Alerts
4. Click "Save Preferences"

**Note:** Users can opt-out of specific types while keeping email enabled for others.

---

## 📧 Email Template

### Email Design

Notifications are sent as HTML emails with:
- **Header:** Colored banner with priority (blue/orange/red)
- **Icon:** Category icon (📢 update, ⚠️ warning, ✅ success, etc.)
- **Title:** Bold notification title
- **Metadata:** Source, type, priority
- **Message:** Full notification message
- **Footer:** Timestamp and manage preferences link

### Priority Colors:
- **Urgent:** Red background
- **High:** Orange background
- **Normal:** Blue background
- **Low:** Gray background

### Sample Email:

```
┌─────────────────────────────────────────┐
│  🔔 AZAI Notification         [ORANGE]  │  <- High Priority
├─────────────────────────────────────────┤
│                                         │
│  Medicaid Processing Delay              │  <- Title
│                                         │
│  Source: MEDICAID | Type: Update        │  <- Metadata
│  Priority: HIGH                         │
│  ─────────────────────────────────────  │
│                                         │
│  Due to system maintenance, Medicaid    │  <- Message
│  claim processing will be delayed by    │
│  2-3 business days this week. Please    │
│  plan accordingly.                      │
│                                         │
├─────────────────────────────────────────┤
│  This notification was sent by AZAI     │  <- Footer
│  December 10, 2025 at 10:00 AM UTC      │
│  To manage preferences, log in          │
└─────────────────────────────────────────┘
```

---

## 🔔 Notification Types Explained

### 1. Medicaid Updates
**Use for:**
- Processing delays
- Policy changes
- Rate updates
- Fee schedule changes
- System maintenance

**Example:**
```
Title: Medicaid Fee Schedule Update - January 2026
Message: The January 2026 Medicaid fee schedule has been published with rate increases for personal care services (T1019).
```

---

### 2. Sandata Alerts
**Use for:**
- Claim acceptance/rejection
- EVV data sync status
- Sandata system issues
- Processing confirmations

**Example:**
```
Title: Sandata Claim Batch Processed
Message: Batch #2025-12-10-001 containing 15 claims has been successfully processed. 14 accepted, 1 rejected (see details).
```

---

### 3. Availity Alerts
**Use for:**
- Eligibility verification results
- Clearinghouse status updates
- Submission confirmations
- Error notifications

**Example:**
```
Title: Availity Real-Time Eligibility Available
Message: Real-time eligibility checking is now available for Medicaid patients. Enable in Settings > Integrations.
```

---

### 4. ODM Notices
**Use for:**
- Official ODM announcements
- Regulatory changes
- Provider enrollment updates
- Compliance requirements

**Example:**
```
Title: ODM Provider Enrollment Renewal Required
Message: Your ODM provider enrollment expires on January 31, 2026. Please submit renewal application by December 31, 2025.
```

---

### 5. System Alerts
**Use for:**
- AZAI system updates
- New features
- Maintenance windows
- Security alerts

**Example:**
```
Title: AZAI System Update - New Geofencing Feature
Message: We've added GPS geofencing for manual clock-in/out to ensure EVV compliance. See the Clock In page for details.
```

---

## 💾 Database Collections

### notifications
```javascript
{
  "id": "notif-uuid",
  "organization_id": "org-uuid",
  "type": "medicaid_update",
  "category": "delay",
  "title": "Medicaid Processing Delay",
  "message": "Due to system maintenance...",
  "source": "medicaid",
  "recipients": ["all"],
  "recipient_emails": ["user1@example.com", "user2@example.com"],
  "send_email": true,
  "email_sent": true,
  "email_sent_at": "2025-12-10T10:05:00Z",
  "priority": "high",
  "status": "sent",
  "created_at": "2025-12-10T10:00:00Z",
  "created_by": "admin-user-uuid"
}
```

### user_notification_preferences
```javascript
{
  "id": "pref-uuid",
  "user_id": "user-uuid",
  "organization_id": "org-uuid",
  "email": "user@example.com",
  "email_enabled": true,
  "medicaid_updates": true,
  "sandata_alerts": true,
  "availity_alerts": true,
  "odm_notices": true,
  "system_alerts": true,
  "digest_mode": false,
  "digest_time": "09:00",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-12-10T10:00:00Z"
}
```

---

## 🧪 Testing

### Test Email Sending

**1. Configure SMTP:**
```bash
# Add to /app/backend/.env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-test-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**2. Restart Backend:**
```bash
sudo supervisorctl restart backend
```

**3. Send Test Notification:**
```bash
curl -X POST "${API_URL}/api/notifications/send" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "system_alert",
    "category": "info",
    "title": "Test Notification",
    "message": "This is a test notification to verify email delivery.",
    "source": "admin",
    "recipients": ["all"],
    "send_email": true,
    "priority": "normal"
  }'
```

**4. Check Email:**
- Check recipient inboxes
- Verify email formatting
- Check spam folder if not received

---

### Test User Preferences

**1. Get Preferences:**
```bash
curl "${API_URL}/api/notifications/preferences/me" \
  -H "Authorization: Bearer ${USER_TOKEN}"
```

**2. Update Preferences:**
```bash
curl -X PUT "${API_URL}/api/notifications/preferences/me" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email_enabled": true,
    "sandata_alerts": false
  }'
```

**3. Send Notification:**
- Send a Sandata alert
- User should NOT receive it (disabled in preferences)

---

### Test Webhooks

**Test Sandata Webhook:**
```bash
curl -X POST "${API_URL}/api/notifications/webhook/sandata?organization_id=test-org" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Sandata Alert",
    "message": "This is a test from Sandata webhook",
    "status": "success"
  }'
```

---

## 🚀 Deployment Checklist

**Before Going Live:**

- [ ] Configure SMTP credentials in `.env`
- [ ] Test email sending with real email addresses
- [ ] Create MongoDB collections:
  ```javascript
  db.createCollection("notifications")
  db.createCollection("user_notification_preferences")
  
  db.notifications.createIndex({"organization_id": 1, "created_at": -1})
  db.user_notification_preferences.createIndex({"user_id": 1, "organization_id": 1})
  ```
- [ ] Verify admin users can access `/notifications`
- [ ] Test sending notifications to all users
- [ ] Verify users can manage preferences at `/notification-preferences`
- [ ] Test webhook endpoints
- [ ] Set up email monitoring (bounce rate, delivery rate)
- [ ] Configure SPF/DKIM records for production email domain

---

## 📊 Monitoring & Analytics

### Track Notification Metrics

**MongoDB Queries:**

**Total notifications sent:**
```javascript
db.notifications.countDocuments({"status": "sent"})
```

**Notifications by type:**
```javascript
db.notifications.aggregate([
  { $group: { _id: "$type", count: { $sum: 1 } } }
])
```

**Email delivery rate:**
```javascript
db.notifications.aggregate([
  { $group: {
      _id: null,
      total: { $sum: 1 },
      sent: { $sum: { $cond: ["$email_sent", 1, 0] } }
    }
  }
])
```

**Users with email disabled:**
```javascript
db.user_notification_preferences.countDocuments({"email_enabled": false})
```

---

## ⚠️ Troubleshooting

### Issue: Emails not sending

**Check:**
1. SMTP credentials in `.env`
2. Backend logs: `tail -f /var/log/supervisor/backend.err.log | grep -i email`
3. SMTP connection: Test with a simple Python script
4. Firewall: Port 587 (TLS) or 465 (SSL) open?

**Solution:**
```bash
# Test SMTP connection
python3 << EOF
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-password')
print("SMTP connection successful!")
server.quit()
EOF
```

---

### Issue: Users not receiving certain notifications

**Check:**
1. User preferences: `GET /api/notifications/preferences/me`
2. Verify specific notification type is enabled
3. Check if `email_enabled` is true

**Solution:**
- Users can manage preferences at `/notification-preferences`
- Admin can view user preferences via database query

---

### Issue: Webhook not working

**Check:**
1. Organization ID in query parameter
2. Request payload format
3. Backend logs for webhook processing

**Solution:**
```bash
# Test webhook manually
curl -X POST "${API_URL}/api/notifications/webhook/sandata?organization_id=YOUR_ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","message":"Test message","status":"info"}'
```

---

## 🎓 Best Practices

**1. Email Frequency:**
- Don't spam users with too many notifications
- Group related updates when possible
- Use appropriate priority levels

**2. Message Content:**
- Be clear and concise
- Include actionable information
- Use plain language

**3. Timing:**
- Send during business hours when possible
- Avoid weekends unless urgent
- Consider time zones

**4. Testing:**
- Always test before sending to all users
- Send test to yourself first
- Verify formatting in multiple email clients

**5. Security:**
- Keep SMTP credentials secure
- Use app-specific passwords (not main password)
- Rotate credentials periodically

---

## 📞 Support

**Questions? Issues?**
- Check backend logs: `/var/log/supervisor/backend.err.log`
- Review notification history at `/notifications`
- Test email delivery with simple notification

---

**Document Version:** 1.0  
**Last Updated:** December 10, 2025  
**System Status:** ✅ Fully Implemented
