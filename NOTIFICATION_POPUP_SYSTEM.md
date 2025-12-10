# AZAI Notification Pop-Up System

**In-App Notifications + Email for Every Notification**

---

## 🎯 Overview

The AZAI notification system now includes:

1. **In-App Pop-Ups:** Notifications appear automatically when users log in
2. **Email Delivery:** Every notification is ALSO sent to user's email
3. **Persistent Access:** Even if users close the pop-up, they have the email for reference
4. **Read/Unread Tracking:** System tracks which notifications each user has seen
5. **Notification Bell:** Shows unread count in navigation bar

---

## 🔔 User Experience

### When User Logs In:

**1. Pop-Up Appears Automatically**
```
┌─────────────────────────────────────────┐
│  🔔 AZAI Notification          [COLOR]  │ ← Priority-based color
├─────────────────────────────────────────┤
│  📢 Medicaid Processing Delay           │
│                                         │
│  Source: MEDICAID | Priority: HIGH      │
│  ─────────────────────────────────────  │
│                                         │
│  Due to system maintenance, Medicaid    │
│  claim processing will be delayed by    │
│  2-3 business days this week...         │
│                                         │
│  📧 Also sent to your email for records │
│                                         │
│                    [Got it!] ──────────►│
└─────────────────────────────────────────┘
```

**2. User Actions:**
- Click "Got it!" → Marks as read, dismisses pop-up
- Click X → Same as "Got it!"
- Next notification appears automatically (if multiple unread)

**3. Email Also Sent:**
- Professional HTML email lands in user's inbox
- Contains same information as pop-up
- User can refer back anytime

---

## 📊 Features Implemented

### Backend Components

**1. Read/Unread Tracking (`notification_models_extended.py`)**
```python
class UserNotificationStatus:
    - user_id
    - notification_id
    - read: bool
    - read_at: datetime
    - dismissed: bool
    - dismissed_at: datetime
```

**2. Extended API Routes (`routes_notifications_extended.py`)**

**New Endpoints:**
```bash
# Get unread notifications for current user
GET /api/notifications/unread

# Get unread count for badge
GET /api/notifications/unread-count

# Mark notification as read
POST /api/notifications/mark-read/{notification_id}

# Dismiss notification (mark read + dismissed)
POST /api/notifications/dismiss/{notification_id}

# Mark all as read
POST /api/notifications/mark-all-read
```

### Frontend Components

**1. NotificationPopup (`NotificationPopup.js`)**
- Full-screen modal overlay
- Priority-colored header
- Category icon
- Message display
- "Got it!" button
- Email reminder

**2. NotificationBell (`NotificationBell.js`)**
- Bell icon in navigation bar
- Unread count badge (e.g., "3")
- Dropdown with recent notifications
- Click notification to mark as read
- "Mark all read" button

**3. NotificationProvider (`NotificationContext.js`)**
- Fetches unread notifications on login
- Manages notification queue
- Shows pop-ups one at a time
- Tracks which have been shown
- Auto-advances to next notification

---

## 🚀 How It Works

### Login Flow:

```
User Logs In
    ↓
NotificationProvider checks for unread notifications
    ↓
GET /api/notifications/unread
    ↓
System returns notifications user hasn't read
    ↓
Notifications sorted by priority (urgent → high → normal → low)
    ↓
First notification shown as pop-up
    ↓
User clicks "Got it!"
    ↓
POST /api/notifications/dismiss/{id}
    ↓
Marked as read + dismissed in database
    ↓
Next notification shown (if any)
    ↓
Repeat until all shown
```

### Email Flow (Happens Simultaneously):

```
Admin sends notification
    ↓
System creates notification record
    ↓
Resolves recipient emails from preferences
    ↓
Sends professional HTML email to each recipient
    ↓
Email lands in user's inbox
    ↓
User can read anytime (even if pop-up was closed)
```

---

## 📧 Email + Pop-Up Strategy

### Why Both?

**Pop-Up:**
- ✅ Immediate attention
- ✅ Can't miss it on login
- ✅ High visibility

**Email:**
- ✅ Permanent record
- ✅ Can refer back later
- ✅ Can search/archive
- ✅ Available even if not logged in

### User Benefits:
1. **Immediate notification** via pop-up
2. **Permanent copy** in email
3. **Can't lose** the information
4. **Can share** email with colleagues
5. **Searchable** in email client

---

## 🎨 Notification Bell

### Location:
Navigation bar → Next to user info → Before logout button

### Badge Display:
- **No unread:** Plain bell icon
- **1-9 unread:** Badge shows number (e.g., "3")
- **10+ unread:** Badge shows "9+"

### Dropdown Features:
- Shows last 5 unread notifications
- Click notification → Mark as read
- "Mark all read" button
- Link to preferences
- Timestamp and source for each

### Auto-Refresh:
- Count refreshes every 30 seconds
- Updates after marking notifications as read

---

## 💾 Database Structure

### notifications Collection (Existing)
```javascript
{
  "id": "notif-uuid",
  "organization_id": "org-uuid",
  "type": "medicaid_update",
  "title": "Medicaid Processing Delay",
  "message": "Due to system maintenance...",
  "send_email": true,  // Always true
  "send_in_app": true,  // Always true
  "email_sent": true,
  "created_at": "2025-12-10T10:00:00Z"
}
```

### user_notification_status Collection (NEW)
```javascript
{
  "id": "status-uuid",
  "user_id": "user-uuid",
  "notification_id": "notif-uuid",
  "organization_id": "org-uuid",
  "read": true,
  "read_at": "2025-12-10T10:05:00Z",
  "dismissed": true,
  "dismissed_at": "2025-12-10T10:05:00Z",
  "shown_in_app": true,
  "shown_at": "2025-12-10T10:05:00Z",
  "created_at": "2025-12-10T10:00:00Z"
}
```

**Indexes:**
```javascript
db.user_notification_status.createIndex({"user_id": 1, "notification_id": 1}, {unique: true})
db.user_notification_status.createIndex({"user_id": 1, "read": 1})
```

---

## 🧪 Testing

### Test Pop-Up System:

**1. Setup:**
```bash
# Configure SMTP in .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Restart backend
sudo supervisorctl restart backend

# Create MongoDB collections
db.createCollection("user_notification_status")
db.user_notification_status.createIndex({"user_id": 1, "notification_id": 1}, {unique: true})
```

**2. Send Test Notification (as admin):**
```bash
curl -X POST "${API_URL}/api/notifications/send" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "system_alert",
    "category": "info",
    "title": "Test Pop-Up Notification",
    "message": "This notification should appear as a pop-up when you log in AND be sent to your email.",
    "source": "admin",
    "recipients": ["all"],
    "priority": "high"
  }'
```

**3. Test User Experience:**
1. **Log out** from AZAI
2. **Check email** → Should have received notification
3. **Log back in** → Pop-up should appear automatically
4. Click "Got it!" → Pop-up closes
5. Check bell icon → Should show 0 unread
6. **Log out and log in again** → No pop-up (already read)

**4. Test Multiple Notifications:**
```bash
# Send 3 notifications
for i in 1 2 3; do
  curl -X POST "${API_URL}/api/notifications/send" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"type\": \"system_alert\",
      \"category\": \"info\",
      \"title\": \"Test Notification #$i\",
      \"message\": \"This is test notification number $i\",
      \"source\": \"admin\",
      \"recipients\": [\"all\"],
      \"priority\": \"normal\"
    }"
done
```

Expected:
- User receives 3 emails
- User logs in → First pop-up appears
- Click "Got it!" → Second pop-up appears
- Click "Got it!" → Third pop-up appears
- Click "Got it!" → No more pop-ups
- Bell icon shows "0" unread

---

## 🎭 Priority System

### Pop-Up Order:

Notifications appear in priority order:
1. **Urgent** (red header)
2. **High** (orange header)
3. **Normal** (blue header)
4. **Low** (gray header)

### Example:

**Notifications sent:**
- Notification A: Priority Normal
- Notification B: Priority Urgent
- Notification C: Priority High

**Pop-up order:**
1. Notification B (Urgent) ← Shown first
2. Notification C (High) ← Shown second
3. Notification A (Normal) ← Shown third

---

## 📱 Notification Bell Dropdown

### Features:

**Shows Recent 5 Unread:**
```
┌───────────────────────────────────────┐
│  Notifications          [Mark all read│
├───────────────────────────────────────┤
│  📢 Medicaid Delay         [HIGH]     │
│  Processing will be delayed...        │
│  Dec 10, 2025 - MEDICAID              │
├───────────────────────────────────────┤
│  ✅ Sandata Success       [NORMAL]    │
│  Batch #001 processed successfully    │
│  Dec 10, 2025 - SANDATA               │
├───────────────────────────────────────┤
│  Manage notification preferences →    │
└───────────────────────────────────────┘
```

**Click Actions:**
- Click notification → Mark as read, close dropdown
- Click "Mark all read" → All notifications marked as read
- Click "Manage preferences" → Navigate to `/notification-preferences`

---

## ⚙️ User Preferences Integration

### How Preferences Work:

**User disables "Sandata Alerts":**
1. User goes to `/notification-preferences`
2. Unchecks "Sandata Alerts"
3. Saves preferences

**Result:**
- User will NOT see Sandata pop-ups
- User will NOT receive Sandata emails
- Sandata notifications excluded from unread count

**Other notification types still work:**
- Medicaid updates → Still shown ✅
- ODM notices → Still shown ✅
- System alerts → Still shown ✅

---

## 🔍 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/notifications/send` | POST | Send notification (admin only) |
| `/api/notifications/unread` | GET | Get unread for current user |
| `/api/notifications/unread-count` | GET | Get count for badge |
| `/api/notifications/mark-read/{id}` | POST | Mark single as read |
| `/api/notifications/dismiss/{id}` | POST | Mark as read + dismissed |
| `/api/notifications/mark-all-read` | POST | Mark all as read |
| `/api/notifications/preferences/me` | GET | Get user preferences |
| `/api/notifications/preferences/me` | PUT | Update preferences |

---

## 🎓 Best Practices

### For Admins Sending Notifications:

**1. Be Clear and Concise:**
```
❌ Bad: "There's an issue with the system"
✅ Good: "Medicaid Processing Delayed Until Dec 12"
```

**2. Include Action Items:**
```
❌ Bad: "Update available"
✅ Good: "Update required by Dec 15. Go to Settings > Updates"
```

**3. Use Appropriate Priority:**
- **Urgent:** System down, immediate action required
- **High:** Service delays, important updates
- **Normal:** Feature announcements, reminders
- **Low:** Tips, suggestions

**4. Consider Timing:**
- Send during business hours (8 AM - 5 PM)
- Avoid weekends unless urgent
- Group related updates

---

## 🐛 Troubleshooting

### Issue: Pop-up not appearing on login

**Check:**
1. Are there unread notifications? `GET /api/notifications/unread`
2. User preferences enabled for that type?
3. Browser console for errors?
4. NotificationProvider wrapped around app?

**Solution:**
```javascript
// Verify NotificationProvider in App.js
<NotificationProvider>
  <AuthProvider>
    {/* App content */}
  </AuthProvider>
</NotificationProvider>
```

---

### Issue: Bell icon not showing unread count

**Check:**
1. Is user logged in?
2. NotificationBell component in navigation?
3. Check `/api/notifications/unread-count` response

**Solution:**
```bash
# Test endpoint
curl "${API_URL}/api/notifications/unread-count" \
  -H "Authorization: Bearer ${USER_TOKEN}"
```

---

### Issue: User still sees notification after clicking "Got it!"

**Check:**
1. Check network tab for API call to `/dismiss/{id}`
2. Verify MongoDB update
3. Clear browser cache

**Solution:**
```javascript
// Check database
db.user_notification_status.find({
  "user_id": "user-uuid",
  "notification_id": "notif-uuid"
})

// Should show read: true, dismissed: true
```

---

## 📊 Monitoring

### Key Metrics to Track:

**MongoDB Queries:**

**1. Total unread notifications per user:**
```javascript
db.user_notification_status.aggregate([
  { $match: { "read": false } },
  { $group: { _id: "$user_id", unread_count: { $sum: 1 } } },
  { $sort: { unread_count: -1 } }
])
```

**2. Notification engagement rate:**
```javascript
// Percentage of notifications that are read
db.user_notification_status.aggregate([
  { $group: {
      _id: null,
      total: { $sum: 1 },
      read: { $sum: { $cond: ["$read", 1, 0] } }
    }
  },
  { $project: {
      engagement_rate: { $multiply: [{ $divide: ["$read", "$total"] }, 100] }
    }
  }
])
```

**3. Average time to read:**
```javascript
db.user_notification_status.aggregate([
  { $match: { "read": true } },
  { $project: {
      time_to_read_seconds: {
        $divide: [
          { $subtract: [new Date("$read_at"), new Date("$created_at")] },
          1000
        ]
      }
    }
  },
  { $group: {
      _id: null,
      avg_time_to_read_seconds: { $avg: "$time_to_read_seconds" }
    }
  }
])
```

---

## ✅ Summary

**What Users Get:**

1. **Pop-up on login** → Can't miss important updates
2. **Email copy** → Permanent record for reference
3. **Notification bell** → See unread count anytime
4. **Dropdown preview** → Quick view of recent notifications
5. **Preference control** → Choose what to receive

**What Admins Get:**

1. **Single endpoint** → Send to all users at once
2. **Priority control** → Mark urgent/high/normal/low
3. **Category options** → Info/update/delay/warning/error
4. **Type options** → Medicaid/Sandata/Availity/ODM/System
5. **History tracking** → See all sent notifications

**What System Provides:**

1. **Dual delivery** → Email + in-app pop-up
2. **Read tracking** → Know what users have seen
3. **Preference filtering** → Respect user choices
4. **Priority sorting** → Urgent first
5. **Auto-advancement** → Shows multiple notifications sequentially

---

**Document Version:** 1.0  
**Last Updated:** December 10, 2025  
**System Status:** ✅ Fully Implemented & Tested
