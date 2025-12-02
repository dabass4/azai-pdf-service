# Admin Panel Implementation - Complete Guide

## Overview

The Admin/Support Panel allows your company staff to manage all client organizations, troubleshoot issues, monitor system health, and resolve problems **without restarting the software or affecting other clients**.

---

## ✅ What's Been Built

### Backend Admin API (`/api/admin/...`)

#### **Organizations Management**
- `GET /admin/organizations` - List all organizations with filtering
- `GET /admin/organizations/{id}` - Get detailed organization info
- `POST /admin/organizations` - Create new organization
- `PUT /admin/organizations/{id}` - Update organization details

#### **Credentials Management** (Per Organization)
- `GET /admin/organizations/{id}/credentials` - View credentials (masked)
- `PUT /admin/organizations/{id}/credentials` - Update OMES/Availity credentials
- `POST /admin/organizations/{id}/test-credentials` - Test specific service connection

#### **System Health Monitoring**
- `GET /admin/system/health` - Get system health status
- `GET /admin/system/logs` - View system logs

#### **Support Tickets**
- `POST /admin/support/tickets` - Create support ticket
- `GET /admin/support/tickets` - List tickets with filtering

#### **Analytics**
- `GET /admin/analytics/overview` - Get usage analytics

### Frontend Admin Dashboard

#### **Dashboard Pages Created:**
1. **AdminDashboard.js** - Main overview with system health & analytics
2. **AdminOrganizations.js** - Manage all client organizations

#### **Features:**
- Real-time system health monitoring
- Organization list with search
- Detailed organization view (users, stats, integration status)
- Credential management per organization
- Quick actions for common tasks

---

## 🔐 Creating Super Admin User

Run this command to create your first super admin:

```bash
cd /app/backend
python create_super_admin.py --email admin@yourcompany.com --password YourSecurePassword123! --first-name John --last-name Doe
```

**Output:**
```
✅ Super admin user created successfully!
   Email: admin@yourcompany.com
   User ID: abc-123-def-456
   Name: John Doe

⚠️  Please save this information securely!

🔐 You can now login with these credentials to access the admin panel.
```

---

## 📊 Admin Panel Features

### 1. **Dashboard Overview**
- **System Health**: Real-time status of database, backend, frontend
- **Statistics**: Total organizations, users, timesheets
- **Analytics**: Growth metrics for last 30 days
- **Quick Actions**: Navigate to key admin functions

### 2. **Organizations Management**
View and manage all client organizations:
- Organization name, status, plan
- User count, timesheet count
- Search and filter capabilities
- Detailed view with:
  - Statistics (users, patients, employees, timesheets)
  - Integration status (OMES, Availity, Sandata)
  - User list with status
  
**Actions:**
- Create new organizations
- Update organization details
- Manage credentials per organization
- View usage statistics

### 3. **Credentials Management** (Per Organization)
Each organization can have separate credentials for:
- **OMES EDI**:
  - Trading Partner ID (TPID)
  - SOAP username/password
  - SFTP username/password
  
- **Availity**:
  - API key
  - Client secret
  - OAuth scopes
  
- **Sandata** (existing):
  - API key
  - Auth token

**Features:**
- Credentials are masked when viewed (security)
- Test connection for each service
- Update credentials without affecting other orgs
- No system restart required

### 4. **System Health Monitoring**
Real-time monitoring of:
- Database connection status
- Backend service status
- Frontend service status
- Statistics (active orgs, total users, recent activity)

### 5. **Support Tickets**
Track client issues:
- Create tickets for specific organizations
- Priority levels: low, medium, high, critical
- Categories: general, billing, technical, integration, credentials
- Status tracking: open, in_progress, resolved, closed

### 6. **Analytics Dashboard**
View system-wide usage:
- New organizations (last 30 days)
- New users (last 30 days)
- New timesheets (last 30 days)
- Top organizations by usage

---

## 🎯 Use Cases

### Use Case 1: Client Reports "Eligibility Check Not Working"

**Steps:**
1. Login to admin panel
2. Go to Organizations → Search for client
3. View organization details
4. Check "Integration Status" → See if OMES is configured
5. Click "Manage Credentials"
6. Test OMES SOAP connection
7. If failed, update credentials or fix issue
8. Test again
9. Resolve without affecting any other client

### Use Case 2: Set Up New Client Organization

**Steps:**
1. Admin Dashboard → "Manage Organizations"
2. Click "+ Create Organization"
3. Enter organization details
4. System creates organization + admin user
5. Go to "Manage Credentials" for that org
6. Enter OMES TPID, SOAP credentials, SFTP credentials
7. Enter Availity API credentials
8. Test all connections
9. Client can now login and start using the system

### Use Case 3: Troubleshoot Slow Performance for One Client

**Steps:**
1. Admin Dashboard → View system health
2. Check which organization is generating most activity
3. Go to that organization's details
4. Review statistics (timesheet count, users)
5. Check logs for that organization
6. Take action (optimize, upgrade plan, contact client)
7. Other clients unaffected

---

## 🏗️ Architecture

```
Admin Panel Architecture
│
├── Super Admin Users
│   └── organization_id: "super_admin"
│   └── is_admin: true
│
├── Regular Organizations (Clients)
│   ├── Organization A
│   │   ├── Users (organization_id: "org-a")
│   │   ├── Patients
│   │   ├── Timesheets
│   │   └── Credentials (OMES, Availity, Sandata)
│   │
│   ├── Organization B
│   │   ├── Users (organization_id: "org-b")
│   │   ├── Patients
│   │   ├── Timesheets
│   │   └── Credentials (different from Org A)
│   │
│   └── Organization C...
│
└── Admin Operations (Isolated)
    ├── View all organizations
    ├── Manage credentials per org
    ├── Create support tickets
    ├── Monitor system health
    └── No cross-contamination
```

---

## 🔒 Security

### Authorization
- All `/api/admin/*` endpoints require `is_admin: true`
- Non-admin users get **403 Forbidden**
- Super admins have special `organization_id: "super_admin"`

### Data Isolation
- Each organization's data is isolated by `organization_id`
- Admin can **view** any organization's data
- Admin **cannot** accidentally modify wrong organization
- Credentials are **masked** when viewed (last 4 characters visible)

### Audit Trail
- All admin actions can be logged
- Support tickets track who created/resolved issues
- Timestamps on all operations

---

## 📝 Database Collections

### New Collections:
- **organization_config**: Stores per-organization credentials
  ```json
  {
    "organization_id": "org-123",
    "omes_tpid": "1234567",
    "omes_soap_username": "username",
    "omes_soap_password": "password",
    "omes_sftp_username": "sftp_user",
    "availity_api_key": "key",
    "availity_client_secret": "secret",
    "updated_at": "2025-01-15T10:00:00Z"
  }
  ```

- **support_tickets**: Track client issues
  ```json
  {
    "ticket_id": "ticket-abc",
    "organization_id": "org-123",
    "title": "Eligibility check failing",
    "description": "Client reports...",
    "priority": "high",
    "category": "integration",
    "status": "open",
    "created_by": "admin-user-id",
    "created_at": "2025-01-15T10:00:00Z"
  }
  ```

---

## 🚀 Next Steps

### Frontend Pages to Build (Optional):

1. **Credentials Management Page** (`AdminCredentials.js`)
   - Form to update OMES/Availity credentials
   - Test connection buttons
   - Save credentials per organization

2. **Support Tickets Page** (`AdminSupport.js`)
   - Create new tickets
   - List all tickets
   - Filter by status, priority, organization
   - Update ticket status

3. **Logs Viewer** (`AdminLogs.js`)
   - View system logs
   - Filter by level (ERROR, WARNING, INFO)
   - Search logs
   - Download logs

4. **Create Organization Form** (`AdminCreateOrg.js`)
   - Form to create new organization
   - Generate admin user
   - Set initial plan

### Integration with Frontend Routing:

Add to `App.js` or routing file:
```javascript
// Admin routes (protected)
<Route path="/admin" element={<AdminDashboard />} />
<Route path="/admin/organizations" element={<AdminOrganizations />} />
<Route path="/admin/credentials" element={<AdminCredentials />} />
<Route path="/admin/support" element={<AdminSupport />} />
<Route path="/admin/logs" element={<AdminLogs />} />
```

---

## ✨ Key Benefits

1. **No Downtime**: Fix issues for one client without restarting
2. **Isolated**: Each organization has separate credentials/data
3. **Scalable**: Add unlimited organizations
4. **Secure**: Role-based access control
5. **Trackable**: Support tickets and audit logs
6. **Real-time**: Monitor system health instantly
7. **Efficient**: Troubleshoot from one central dashboard

---

## 🧪 Testing

### Test Admin Endpoints:

```bash
# 1. Create super admin
python create_super_admin.py --email admin@test.com --password Test123!

# 2. Login and get token
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"Test123!"}'

# 3. Test admin endpoints
curl http://localhost:8001/api/admin/organizations \
  -H "Authorization: Bearer YOUR_TOKEN"

curl http://localhost:8001/api/admin/system/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 Summary

**Backend:** ✅ Complete
- Admin API routes implemented
- Authorization middleware
- Credentials management per org
- System health monitoring
- Support tickets system

**Frontend:** ✅ Basic UI Created
- Admin dashboard with health & analytics
- Organizations list and detail view
- Ready for additional pages

**Ready to Use:**
1. Create super admin user
2. Login to admin panel
3. Manage all client organizations
4. No restart needed for any operations

**Status:** Phase 1 Complete - Core admin functionality is working!
