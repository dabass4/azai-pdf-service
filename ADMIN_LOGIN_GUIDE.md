# Admin Panel Access Guide

## Overview
The Admin Panel allows your company (software provider) to manage multiple client organizations, configure their credentials, and monitor system health without affecting individual tenants.

---

## Step 1: Create Super Admin Account

### First Time Setup

Run this command in the backend directory to create your first super admin account:

```bash
cd /app/backend
python create_super_admin.py --email admin@yourcompany.com --password YourSecurePassword123 --first-name John --last-name Doe
```

**Example:**
```bash
python create_super_admin.py --email admin@medicaidservices.com --password SecureAdmin2024! --first-name Admin --last-name User
```

**Output:**
```
✅ Super admin user created successfully!
   Email: admin@medicaidservices.com
   User ID: abc-123-xyz
   Name: Admin User

⚠️  Please save this information securely!

🔐 You can now login with these credentials to access the admin panel.
```

---

## Step 2: Login to Admin Panel

### Access URL
**Production URL:** `https://claim-tracker-21.preview.emergentagent.com`

### Login Steps:
1. Navigate to the application URL
2. Click **"Sign In"** button (top right)
3. Enter your super admin credentials:
   - Email: `admin@yourcompany.com`
   - Password: `YourSecurePassword123`
4. Click **"Sign In"**

### After Login:
Once logged in as a super admin, you'll see an **"Admin"** link in the main navigation menu.

---

## Step 3: Access Admin Dashboard

### Navigation:
- After login, look for **"Admin"** in the main navigation bar
- Or directly navigate to: `/admin`

### Admin Dashboard Features:
The dashboard provides quick access to:
- 🏢 **Manage Organizations**
- 🔑 **Manage Credentials**
- 🎫 **Support Tickets**
- 📋 **View Logs**

---

## Managing Multiple Clients

### 1. Organization Management (`/admin/organizations`)

**What you can do:**
- ✅ View all client organizations in a table
- ✅ Create new client organizations
- ✅ Edit organization details (name, contact, NPI, taxonomy code)
- ✅ Set organization status (Active, Inactive, Suspended)
- ✅ Delete organizations

**Fields for each organization:**
- Organization Name *
- Contact Email *
- Contact Phone
- NPI Number
- Taxonomy Code
- Address
- Status (Active/Inactive/Suspended)

**Use Case:** When you onboard a new healthcare client (e.g., "ABC Home Healthcare"), create their organization record here first.

---

### 2. Credentials Management (`/admin/credentials`)

**What you can do:**
- ✅ Select an organization from dropdown
- ✅ Configure OMES EDI credentials (SOAP & SFTP)
- ✅ Configure Availity clearinghouse credentials
- ✅ Password fields with show/hide toggles
- ✅ Securely encrypted storage

**OMES EDI Credentials:**
- SOAP Endpoint URL
- SOAP Username
- SOAP Password
- SFTP Host
- SFTP Port
- SFTP Username
- SFTP Password

**Availity Credentials:**
- API Endpoint URL
- Client ID
- Client Secret
- Organization ID

**Use Case:** Each client has their own OMES and Availity credentials. Configure them here per organization so their claims are submitted under their credentials.

---

### 3. Support Ticket System (`/admin/support`)

**What you can do:**
- ✅ View all support tickets from clients
- ✅ Create new tickets
- ✅ Filter by priority (Low, Medium, High)
- ✅ Update ticket status (Open → In Progress → Resolved → Closed)
- ✅ Track ticket history

**Use Case:** When "ABC Home Healthcare" calls with an issue, create a support ticket, track progress, and mark it resolved when fixed.

---

### 4. System Logs Viewer (`/admin/logs`)

**What you can do:**
- ✅ View real-time system logs
- ✅ Filter by severity level (Info, Warning, Error, Debug)
- ✅ Search logs by keyword
- ✅ Export logs to file
- ✅ Monitor application health

**Use Case:** When investigating why claims are failing for a specific client, search logs for their organization ID or error messages.

---

## Multi-Tenant Architecture

### How It Works:
1. **Software Provider (You):**
   - Login with super admin account
   - Manage all client organizations
   - Configure credentials per client
   - Monitor system health

2. **Client Organizations (Your Customers):**
   - Each client has their own organization record
   - Their own OMES/Availity credentials
   - Their own patients, employees, timesheets
   - Isolated data - clients can't see each other's data

3. **Client Users:**
   - Regular users belong to a specific organization
   - They only see their organization's data
   - Cannot access admin panel
   - Use the main application features (timesheets, claims, etc.)

### Example Workflow:

**Scenario:** Onboarding a new client "XYZ Home Health"

1. **Create Organization:**
   - Go to `/admin/organizations`
   - Click "Add Organization"
   - Fill in: Name, Contact Email, NPI, etc.
   - Save

2. **Configure Credentials:**
   - Go to `/admin/credentials`
   - Select "XYZ Home Health" from dropdown
   - Enter their OMES SOAP credentials
   - Enter their OMES SFTP credentials
   - Enter their Availity credentials (if applicable)
   - Save each section

3. **Client Can Now Use System:**
   - XYZ Home Health users can register accounts
   - They're automatically associated with XYZ organization
   - Their claims are submitted using their configured credentials
   - Their data is isolated from other clients

4. **Monitor & Support:**
   - Track any issues in Support Tickets
   - Monitor logs for errors
   - Update credentials if they change

---

## Security Features

- 🔐 **Super Admin Role:** Only users with `is_admin: true` can access admin panel
- 🔒 **Encrypted Credentials:** All OMES/Availity credentials are encrypted in database
- 👁️ **Password Visibility Toggles:** Credentials hidden by default, can be revealed when needed
- 🚫 **Route Protection:** Admin routes automatically redirect non-admin users
- 📝 **Audit Trail:** All admin actions can be logged (future enhancement)

---

## Quick Reference

### URLs:
- **Login:** `/login`
- **Admin Dashboard:** `/admin`
- **Organizations:** `/admin/organizations`
- **Credentials:** `/admin/credentials`
- **Support:** `/admin/support`
- **Logs:** `/admin/logs`

### Commands:
```bash
# Create super admin
python /app/backend/create_super_admin.py --email EMAIL --password PASSWORD

# Create additional super admin
python /app/backend/create_super_admin.py --email admin2@company.com --password Pass123!
```

---

## Troubleshooting

### Can't Access Admin Panel?
1. Verify you created super admin account
2. Check you're logged in with super admin credentials
3. Verify `is_admin: true` in database for your user
4. Check browser console for JavaScript errors

### Don't See Admin Link?
- Admin link only appears for users with `is_admin: true` flag
- Regular client users won't see this link
- Logout and login with super admin account

### Organizations Not Loading?
- Check backend logs: `tail -n 100 /var/log/supervisor/backend.*.log`
- Verify MongoDB connection
- Check API endpoint `/api/admin/organizations` returns 200

---

## Next Steps

1. ✅ Create your super admin account
2. ✅ Login and access admin panel
3. ✅ Create your first client organization
4. ✅ Configure credentials for that organization
5. ✅ Test the system with a client user account

**Need Help?** Check the system logs in the Admin Panel or contact support.
