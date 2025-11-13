# Healthcare Timesheet Scanner - User Guide

**Version:** 2.0  
**Last Updated:** November 2024

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication & Account Setup](#authentication--account-setup)
3. [Dashboard Overview](#dashboard-overview)
4. [Timesheet Management](#timesheet-management)
5. [Patient Management](#patient-management)
6. [Employee Management](#employee-management)
7. [Payer & Insurance Management](#payer--insurance-management)
8. [Ohio Medicaid 837P Claims](#ohio-medicaid-837p-claims)
9. [EVV (Electronic Visit Verification)](#evv-electronic-visit-verification)
10. [Service Codes Configuration](#service-codes-configuration)
11. [Search & Filter Features](#search--filter-features)
12. [Bulk Operations](#bulk-operations)
13. [Subscription & Billing](#subscription--billing)
14. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements
- **Browser:** Chrome, Firefox, Safari, or Edge (latest version)
- **Internet Connection:** Stable broadband connection
- **Screen Resolution:** Minimum 1024x768 (responsive for mobile/tablet)

### Quick Start Guide
1. Visit the application URL
2. Click "Sign Up" to create an account
3. Choose your subscription plan
4. Complete organization setup
5. Start uploading timesheets

---

## Authentication & Account Setup

### Creating an Account

1. **Navigate to Landing Page**
   - Click "Get Started" or "Sign Up"

2. **Fill Registration Form**
   - Organization Name
   - Email Address
   - Password (minimum 8 characters)
   - Confirm Password

3. **Choose Subscription Plan**
   - **Basic Plan** ($49/month): Up to 50 timesheets/month
   - **Professional Plan** ($149/month): Up to 500 timesheets/month
   - **Enterprise Plan** (Custom pricing): Unlimited timesheets

4. **Complete Payment**
   - Enter payment details (Stripe secure checkout)
   - Review and confirm subscription

5. **Email Verification**
   - Check your email for verification link
   - Click link to verify account

### Logging In

1. Click "Sign In" button
2. Enter email and password
3. Click "Login"

**Forgot Password?**
- Click "Forgot Password" link
- Enter your email
- Follow reset instructions sent to your email

---

## Dashboard Overview

### Main Navigation

**Left Sidebar Menu:**
- **Dashboard** - Overview and quick stats
- **Timesheets** - Upload and manage timesheets
- **Patients** - Patient profiles and information
- **Employees** - Employee/caregiver profiles
- **Payers** - Insurance contracts and payer information
- **Claims** - Ohio Medicaid 837P claim generation
- **EVV Management** - Electronic Visit Verification
- **Service Codes** - Configure billing codes
- **Settings** - Account and organization settings

### Dashboard Widgets
- Total timesheets processed
- Recent uploads
- Pending claims
- Upcoming tasks

---

## Timesheet Management

### Uploading Timesheets

**Supported Formats:**
- PDF files (.pdf)
- Image files (.jpg, .jpeg, .png)

**Upload Process:**

1. **Navigate to Timesheets Page**
   - Click "Timesheets" in sidebar

2. **Click "Upload Timesheet" Button**
   - Select file from your computer
   - Drag and drop also supported

3. **AI Processing**
   - System automatically scans document
   - Extracts:
     * Patient/Client name
     * Employee/Caregiver name
     * Service dates and times
     * Service codes
     * Total hours and units
     * Signatures (verification)

4. **Review Extracted Data**
   - Check extracted information for accuracy
   - Edit any fields if needed
   - Verify completion status

5. **Save or Submit**
   - Click "Save" to store data
   - Click "Submit" to send to payroll systems

### Timesheet Editor

**Manual Editing:**
- Click "Edit" button on any timesheet
- Modify extracted fields
- Add missing information
- Update service entries

**Fields Available:**
- Week of date
- Patient information
- Employee information
- Multiple service entries per timesheet
- Service codes and units
- Notes and comments

### Timesheet Status

- **Pending** - Uploaded, awaiting processing
- **Processing** - AI extraction in progress
- **Completed** - Extraction complete, ready for review
- **Submitted** - Sent to external systems
- **Failed** - Processing error occurred

---

## Patient Management

### Adding a New Patient

1. **Click "Add Patient" Button**

2. **Fill Patient Information** (Multi-Step Wizard):

   **Step 1: Basic Information**
   - First Name
   - Last Name
   - Date of Birth
   - Gender
   - SSN (optional)

   **Step 2: Contact & Address**
   - Phone numbers (primary, secondary)
   - Email address
   - Street address
   - City, State, ZIP
   - Address type (Home, Work, etc.)

   **Step 3: Medical & Insurance**
   - Medicaid Number (12 digits)
   - Medicare Number (if applicable)
   - Insurance contracts
   - Diagnosis codes

   **Step 4: EVV Information** (Ohio Medicaid)
   - Patient Other ID
   - PIMS ID (for ODA payers)
   - Timezone
   - Coordinates (for location verification)
   - Responsible party information

3. **Click "Save" or "Save & Add Another"**

### Editing Patient Information

1. Find patient using search
2. Click "Edit" button
3. Update necessary fields
4. Click "Save Changes"

### Patient Profile Includes:
- Demographics
- Contact information
- Insurance/Medicaid details
- Service history
- EVV compliance data
- Associated timesheets

---

## Employee Management

### Adding a New Employee

1. **Click "Add Employee" Button**

2. **Fill Employee Information**:

   **Basic Information:**
   - First Name
   - Last Name
   - Employee ID (unique identifier)
   - Date of Birth
   - Gender

   **Contact Information:**
   - Phone number
   - Email address
   - Mailing address

   **Employment Details:**
   - Hire Date
   - Employment Status (Active, Inactive, Terminated)
   - Department
   - Position/Title

   **Direct Care Worker (DCW) Information:**
   - NPI Number (National Provider Identifier)
   - Staff PIN
   - Staff Other ID
   - Staff Position Code (3 characters)
   - SSN
   - Training certifications
   - License numbers

3. **Click "Save"**

### Employee Status
- **Active** - Currently employed
- **Inactive** - On leave or temporary status
- **Terminated** - No longer employed

---

## Payer & Insurance Management

### Adding Insurance Contract

1. **Navigate to Payers Page**
2. **Click "Add Insurance Contract"**

3. **Enter Contract Details**:
   - Payer Name (e.g., Ohio Medicaid)
   - Contract Number
   - Effective Date
   - Expiration Date
   - Contract Type
   - Coverage details
   - Billing information

4. **Link to Patients**
   - Associate contract with specific patients
   - Set as primary or secondary insurance

### Managing Contracts
- View all active contracts
- Update contract information
- Track expiration dates
- Generate reports

---

## Ohio Medicaid 837P Claims

### Overview
Generate HIPAA 5010-compliant 837 Professional claims for submission to Ohio Department of Medicaid.

### Tab 1: Generate 837P Claims

**Process:**

1. **Select Timesheets**
   - View list of all completed timesheets
   - Check individual timesheets or use "Select All"
   - Selection counter shows: "X of Y timesheets selected"

2. **Generate EDI File**
   - Click "Generate 837P File" button
   - System creates HIPAA-compliant EDI file
   - File automatically downloads (.edi format)

3. **File Contents**
   - ISA (Interchange Control Header)
   - GS (Functional Group Header)
   - ST (Transaction Set Header)
   - CLM (Claim Information)
   - SV1 (Service Line Items)
   - All patient and provider data

**Important Notes:**
- Generated files are for testing and manual submission
- Real production submission requires ODM enrollment
- Files comply with Ohio Medicaid companion guide specifications

### Tab 2: Generated Claims History

**View Previous Claims:**
- List of all generated 837P claims
- Claim ID and creation date
- Patient information
- Number of service lines
- Status (Generated, Submitted)

**Download Claims:**
- Click "Download EDI" button
- Retrieve previously generated files
- Review claim data

### Tab 3: ODM Enrollment Checklist

**11-Step Enrollment Process:**

1. ✅ Review ODM Trading Partner Information Guide
2. ✅ Review HIPAA ASC X12 Technical Reports
3. ✅ Begin Trading Partner Enrollment
4. ✅ Review ODM Companion Guides
5. ✅ Coordinate Testing Strategy
6. ✅ Complete Trading Partner Agreement
7. ✅ Complete EDI Connectivity Form
8. ✅ Verify Trading Partner Number
9. ✅ Provide Test Provider List
10. ✅ Submit Test Claims
11. ✅ Verify EDI Receipts

**Track Your Progress:**
- Mark each step as complete
- View completion percentage (e.g., 5/11)
- Add notes to each step
- Track trading partner ID once received

**Resources:**
- [ODM Enrollment Guide](https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners/content/enrollment-testing)
- [Ohio Medicaid Companion Guides](https://medicaid.ohio.gov/resources-for-providers/billing/hipaa-5010-implementation/companion-guides/guides)
- Contact: EDI-TP-Comments@medicaid.ohio.gov

---

## EVV (Electronic Visit Verification)

### What is EVV?
Electronic Visit Verification is required by Ohio Medicaid for personal care services. It captures:
- Individual receiving service
- Direct care worker providing service
- Type of service
- Date of service
- Location of service
- Time service begins and ends

### EVV Configuration

1. **Navigate to EVV Management**
2. **Configure Business Entity**
   - Business Entity ID
   - Business Entity Medicaid Identifier
   - Agency Name
   - Contact Information

3. **Set Up Reference Data**
   - Service types
   - Visit types
   - Location types

### EVV Exports

**Three Export Types:**

1. **Individuals Export**
   - Patient/client information
   - Demographics
   - Addresses with coordinates
   - Payer information
   - JSON format compliant with Ohio EVV specs

2. **Direct Care Workers Export**
   - Employee/caregiver information
   - Credentials and certifications
   - Contact details
   - Staff identifiers

3. **Visits Export**
   - Service visit records
   - Date and time (UTC format)
   - Check-in/check-out times
   - Service location
   - Service type and codes

### Submitting EVV Data

**Current:** Mock submission for testing  
**Production:** Requires Ohio EVV aggregator credentials

1. Navigate to EVV Management
2. Select data type (Individuals, DCW, or Visits)
3. Click "Submit to EVV"
4. Review transmission results

---

## Service Codes Configuration

### Managing Service Codes

1. **Navigate to Service Codes Page**
2. **Click "Add Service Code"**

3. **Enter Code Information**:
   - Service Code (e.g., T1019)
   - Description (e.g., Personal Care Services)
   - Unit Rate
   - Unit Type (15 minutes, hourly, etc.)
   - Effective Date
   - Status (Active/Inactive)

4. **Configure Billing Rules**
   - Rounding rules (>= 35 minutes = 3 units)
   - Maximum units per day
   - Authorization requirements

---

## Search & Filter Features

### Global Search
- Search bar available on all major pages
- Search by:
  * Patient name
  * Employee name
  * Medicaid ID
  * Date range

### Advanced Filters

**Patients:**
- Completion status (Complete/Incomplete)
- Insurance type
- Date added
- Service codes

**Employees:**
- Employment status
- Department
- Hire date range

**Timesheets:**
- Status (Pending, Completed, Submitted)
- Date range
- Patient or employee
- Service codes

### Using Filters

1. Click "Filter" button
2. Select filter criteria
3. Apply filters
4. Results update automatically
5. Clear filters to reset

---

## Bulk Operations

### Bulk Actions Available

**Select Multiple Records:**
1. Check individual item checkboxes
2. OR click "Select All" checkbox
3. Selection counter shows: "X items selected"

**Available Bulk Actions:**

**For Patients:**
- Mark as Complete
- Mark as Incomplete
- Delete Selected
- Export to CSV

**For Employees:**
- Update Status (Active/Inactive)
- Delete Selected
- Export to CSV

**For Timesheets:**
- Mark as Complete
- Submit to Sandata
- Delete Selected
- Export to CSV
- Generate 837P Claims

### Performing Bulk Operations

1. **Select Items**
   - Check boxes next to items
   - Use "Select All" for all items

2. **Choose Action**
   - Click desired bulk action button
   - Confirm action in dialog

3. **Review Results**
   - Success message shows count
   - Failed items listed with reasons

---

## Subscription & Billing

### Plan Management

**Current Plans:**
- **Basic** - $49/month (50 timesheets)
- **Professional** - $149/month (500 timesheets)
- **Enterprise** - Custom pricing (unlimited)

### Upgrading Your Plan

1. Navigate to Settings > Subscription
2. Click "Change Plan"
3. Select new plan
4. Confirm upgrade
5. Billing adjusted pro-rata

### Billing History
- View past invoices
- Download receipts
- Update payment method

### Usage Tracking
- Current month's usage
- Timesheets processed
- Remaining quota
- Usage trends

---

## Troubleshooting

### Common Issues

#### "PDF Conversion Failed"
**Problem:** PDF timesheet upload fails  
**Solution:**
- Check PDF is not password-protected
- Ensure PDF is not corrupted
- Try converting to image format
- Contact support if persists

#### "Network Error" During Login
**Problem:** Cannot connect to server  
**Solutions:**
- Check internet connection
- Clear browser cache
- Try different browser
- Verify credentials are correct
- Wait a few minutes and retry

#### Timesheet Data Not Extracting
**Problem:** OCR not detecting information  
**Solutions:**
- Ensure document is clear and legible
- Check document is right-side up
- Verify contrast is sufficient
- Try uploading higher resolution image
- Use manual entry as backup

#### Claims Generation Fails
**Problem:** 837P file generation error  
**Solutions:**
- Verify all timesheets have patient data
- Check employee NPI numbers are present
- Ensure service codes are configured
- Review extraction completeness
- Check browser console for errors

#### Multi-Tenant Data Issues
**Problem:** Seeing wrong organization's data  
**Solution:**
- Log out and log back in
- Clear browser cookies
- Contact support immediately
- **This should not happen** - report as critical bug

---

## Best Practices

### Data Entry
- ✅ Always verify OCR-extracted data
- ✅ Keep patient/employee profiles updated
- ✅ Use consistent naming conventions
- ✅ Complete all required EVV fields
- ✅ Maintain accurate service codes

### Claims Management
- ✅ Generate 837P claims weekly
- ✅ Keep copies of all EDI files
- ✅ Track ODM enrollment progress
- ✅ Test files before production submission
- ✅ Monitor claim statuses

### Security
- ✅ Use strong passwords
- ✅ Never share login credentials
- ✅ Log out when done
- ✅ Report suspicious activity
- ✅ Keep payment methods updated

### Compliance
- ✅ Complete EVV data for all visits
- ✅ Submit EVV data within 24 hours
- ✅ Verify Medicaid IDs are accurate
- ✅ Keep documentation for audits
- ✅ Stay updated on ODM changes

---

## Getting Help

### Support Resources

**In-App Help:**
- Hover over ⓘ icons for tooltips
- Check information alert boxes
- Review error messages

**Documentation:**
- This User Guide
- API documentation
- Integration requirements
- Pending actions list

**Contact Support:**
- **Email:** support@yourdomain.com
- **Phone:** (800) 555-1234
- **Hours:** Monday-Friday, 9 AM - 5 PM EST
- **Emergency:** 24/7 for critical issues

### Reporting Bugs
1. Document the issue
2. Include screenshots
3. Note steps to reproduce
4. Email support with details

### Feature Requests
- Submit via support email
- Describe use case
- Explain business value
- Include mockups if possible

---

## Appendix

### Glossary

**837P** - HIPAA X12 837 Professional claim transaction  
**DCW** - Direct Care Worker  
**EDI** - Electronic Data Interchange  
**EVV** - Electronic Visit Verification  
**NPI** - National Provider Identifier  
**ODM** - Ohio Department of Medicaid  
**OCR** - Optical Character Recognition  
**PIMS** - Provider Information Management System  

### Keyboard Shortcuts

- `Ctrl/Cmd + S` - Save form
- `Ctrl/Cmd + K` - Focus search
- `Esc` - Close dialog/modal
- `Tab` - Navigate form fields

### System Status
- Check application status: status.yourdomain.com
- Scheduled maintenance notifications
- Service health dashboard

---

**Version History:**
- v2.0 (Nov 2024) - Added 837P claims and ODM enrollment
- v1.5 (Oct 2024) - Added EVV export functionality
- v1.0 (Sep 2024) - Initial release

**Document maintained by:** Development Team  
**Last reviewed:** November 2024
