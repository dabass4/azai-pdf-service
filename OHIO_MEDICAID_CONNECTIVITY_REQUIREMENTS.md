# Ohio Medicaid (ODM) Connectivity Form - Complete Requirements Guide

**Last Updated:** December 2024  
**Application:** AZAI Healthcare Timesheet  
**Purpose:** Submit 837P (Professional) claims for home healthcare services

---

## Executive Summary

To connect your AZAI application to Ohio Medicaid for electronic claims submission, you must complete the **OMES EDI Connectivity Form** and enroll as a Trading Partner. This document provides all required information and documents needed.

---

## Required Forms & Documents Checklist

### ✅ Primary Form
- **OMES EDI Trading Partner Connectivity Form**
  - Download: https://dam.assets.ohio.gov/image/upload/medicaid.ohio.gov/Providers/Billing/TradingPartners/OMES_EDI_TP_Connectivity_Form_04262024.pdf
  - Version: April 26, 2024 (latest)
  - Submit to: Via Trading Partner Management Application

### ✅ Required Business Documents

#### 1. **Business Entity Information**
```
✅ Legal Business Name
✅ Doing Business As (DBA) name (if applicable)
✅ Business Address (physical location)
✅ Mailing Address (if different)
✅ Phone Number
✅ Email Address (for technical contact)
```

#### 2. **Tax Identification**
```
✅ Federal Tax ID Number (EIN)
   - Employer Identification Number issued by IRS
   - Format: XX-XXXXXXX
   
OR

✅ Social Security Number (SSN)
   - Only if operating as individual/sole proprietor
   - Format: XXX-XX-XXXX
```

#### 3. **Business License Documentation**
```
✅ Business License (copy)
   - State of Ohio business license
   - OR Certificate of Good Standing from Ohio Secretary of State
   - OR Articles of Incorporation

✅ Professional Licenses (if applicable)
   - Healthcare agency license
   - Home health agency license
   - Any relevant professional certifications
```

#### 4. **National Provider Identifier (NPI)**
```
✅ NPI Type 2 (Organizational NPI)
   - 10-digit number issued by CMS
   - Required for billing entity
   - Obtain at: https://nppes.cms.hhs.gov

✅ NPI for Individual Providers (if billing directly)
   - NPI Type 1 for individual practitioners
```

#### 5. **Provider Enrollment Verification**
```
✅ ODM Provider Number(s)
   - Must be enrolled in Ohio Medicaid Provider Network Management (PNM)
   - Each provider number must be active and eligible
   - Maximum 5 provider numbers for initial testing
   
✅ Provider Type Documentation
   - Specify: Home Health Agency, Personal Care, etc.
   - Include Medicaid provider type code
```

#### 6. **Trading Partner Information**
```
✅ ODM Trading Partner Number (if already assigned)
   - 7-digit Sender/Receiver ID
   - Format: TPXXXXX
   - If new: Will be assigned after application

✅ Clearinghouse Information (if using one)
   - Clearinghouse name
   - Clearinghouse Trading Partner ID
   - Relationship documentation
```

---

## Enrollment Process - Step by Step

### Phase 1: Prerequisites (Before Form Submission)

#### Step 1: Obtain State of Ohio ID (OH|ID)
**Purpose:** Required to access ODM systems and applications

**How to Get:**
1. Go to: https://innovateohio.gov
2. Click "Create Account" or "Get OH|ID"
3. Complete registration:
   - Personal information
   - Email verification
   - Multi-Factor Authentication (MFA) setup
4. **Save your OH|ID credentials securely**

**Time:** 15-30 minutes  
**Cost:** FREE

---

#### Step 2: Enroll in Provider Network Management (PNM)
**Purpose:** Must be enrolled as Ohio Medicaid provider before EDI connectivity

**Required for:**
- All providers who will bill Ohio Medicaid
- Home health agencies
- Personal care providers

**How to Enroll:**
1. Go to: https://medicaid.ohio.gov/resources-for-providers/enrollment-and-support/provider-enrollment
2. Access "Provider Enrollment Portal"
3. Complete enrollment application:
   - Business information
   - Tax ID / NPI
   - Service types offered
   - Provider type codes

**Documents Needed for PNM:**
```
✅ Completed Provider Enrollment Application
✅ W-9 Form (IRS)
✅ Copy of Business License
✅ Copy of Professional Licenses
✅ Proof of liability insurance
✅ Organizational chart (if applicable)
✅ Background check documentation (for owners/principals)
```

**Processing Time:** 30-60 days  
**Status Check:** Via PNM portal

---

#### Step 3: Obtain NPI (if not already done)
**Purpose:** Required identifier for all healthcare entities

**For Organizations (NPI Type 2):**
1. Go to: https://nppes.cms.hhs.gov
2. Click "NPI Application/Update"
3. Select "Organization (Type 2)"
4. Complete application:
   - Business name and address
   - Tax ID
   - Service type
   - Contact information

**Documents Needed:**
```
✅ Articles of Incorporation OR Business License
✅ W-9 Form
✅ Proof of business address
```

**Processing Time:** Immediate to 24 hours  
**Cost:** FREE

---

### Phase 2: Trading Partner Application

#### Step 4: Access Trading Partner Management Application
**Purpose:** Start the official ODM trading partner enrollment

**How to Access:**
1. Go to: https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners
2. Click "Trading Partner Management Application"
3. Login with your OH|ID credentials
4. Complete Multi-Factor Authentication

**User Guide:**
- Download: OMES EDI TP Management Application User Guide (PDF)
- Link available on Trading Partners page

---

#### Step 5: Complete Trading Partner Application
**Purpose:** Register as authorized trading partner

**Information Required:**

**A. Company Information:**
```
Legal Name:                    [Your Company Name]
DBA Name:                      AZAI Healthcare Solutions (or your DBA)
Business Address:              [Street, City, State, ZIP]
Mailing Address:               [If different from above]
Phone:                         [Main business number]
Fax:                          [If applicable]
Website:                       [Your website]
```

**B. Primary Contact Information:**
```
Contact Name:                  [Primary business contact]
Title:                        [Owner/CEO/Manager]
Email:                        [Primary email]
Phone:                        [Direct line]
```

**C. Technical Contact Information:**
```
Contact Name:                  [IT/Technical person]
Title:                        [System Administrator/Developer]
Email:                        [Technical support email]
Phone:                        [Technical support line]
Available Hours:               [Business hours]
```

**D. EDI Contact Information:**
```
Contact Name:                  [EDI specialist]
Email:                        [EDI-related inquiries]
Phone:                        [EDI support line]
```

**E. Tax & Identification:**
```
Federal Tax ID (EIN):         [XX-XXXXXXX]
State Tax ID:                 [If applicable]
DUNS Number:                  [Optional but recommended]
```

**F. Provider Information:**
```
ODM Provider Number(s):       [List up to 5 for testing]
NPI (Organization):           [10-digit NPI Type 2]
Provider Type:                [Home Health Agency, etc.]
Service Location(s):          [List all locations]
```

**G. Transaction Types:**
```
☐ 837P (Professional Claims) - ✅ SELECT THIS
☐ 837I (Institutional Claims)
☐ 835 (Remittance Advice) - ✅ SELECT THIS (to receive payment info)
☐ 276/277 (Claim Status Inquiry/Response)
☐ 270/271 (Eligibility Inquiry/Response)
☐ 278 (Prior Authorization)
```

**Recommended for AZAI:** Check 837P and 835 at minimum

---

#### Step 6: Complete EDI Connectivity Form
**Purpose:** Specify technical connection method and parameters

**Download Form:**
- https://dam.assets.ohio.gov/image/upload/medicaid.ohio.gov/Providers/Billing/TradingPartners/OMES_EDI_TP_Connectivity_Form_04262024.pdf

**Form Sections:**

**Section 1: Trading Partner Information**
```
Trading Partner Name:          [Your company name]
Trading Partner Number:        [Leave blank if new - will be assigned]
Contact Person:                [Technical contact name]
Email:                        [Technical email]
Phone:                        [Technical phone]
```

**Section 2: Connectivity Method** (Choose ONE)

**Option A: SFTP (Recommended for AZAI)**
```
☐ SFTP (Secured File Transfer Protocol)

Why SFTP is recommended:
- Most common for automated claims submission
- Works well with batch processing
- Your application can automate file uploads
- 24/7 access
- Reliable and secure

Required Information:
- Company IP Address(es):      [Public IP of your server]
- Firewall Rules Needed:       Yes
- Preferred Connection:        Outbound (you connect to ODM)
- File Transfer Schedule:      [e.g., Daily at 8 PM EST]
```

**Option B: CAQH/CORE Web Services**
```
☐ CAQH/CORE Compliant Web Services (SOAP)

Use if:
- You need real-time claim submission
- You're integrating with clearinghouse
- You need immediate response

Required Information:
- Web Service Endpoint:        [Your SOAP endpoint URL]
- WSDL Location:              [URL to your WSDL]
- Authentication Method:       [Username/Password, Certificate, etc.]
```

**Option C: HTTPS Browser (Manual)**
```
☐ HTTPS Browser (EDI Web Application)

Use if:
- Manual submission only
- Low volume
- No automated system yet

No technical setup required - just web browser access
```

**Section 3: Security Information**
```
Company Public IP Address(es):  [Required for SFTP]
Firewall Exceptions Needed:     Yes/No
SSL Certificate:                [If using HTTPS/Web Services]
PGP/GPG Encryption:             [If applicable]
```

**Section 4: Testing Information**
```
Test Provider Numbers:          [List up to 5 Medicaid provider IDs]
Test Start Date:               [Desired date]
Expected Transaction Volume:    [Claims per month]
Testing Contact:               [Name and email]
```

**Section 5: Production Readiness**
```
Go-Live Date (target):         [Your target date]
Estimated Monthly Volume:      [Number of claims]
Peak Processing Times:         [If applicable]
```

**Section 6: Companion Guides Review**
```
☐ I have reviewed the 837P Companion Guide
☐ I have reviewed the 835 Companion Guide
☐ I have reviewed HIPAA compliance requirements
☐ I understand SNIP validation edits (Types 1-7)
```

**Section 7: Signature**
```
Authorized Representative:     [Name]
Title:                        [Title]
Signature:                    [Signature]
Date:                         [Date]
```

---

### Phase 3: Documentation Submission

#### Required Attachments Checklist

**Business Documentation:**
```
✅ 1. W-9 Form (IRS)
   - Completed and signed
   - Matches Tax ID on application

✅ 2. Certificate of Good Standing
   - From Ohio Secretary of State
   - Dated within last 90 days
   - Shows business is active and compliant

✅ 3. Business License
   - Ohio business license (copy)
   - Current and not expired
   - Shows business is authorized to operate

✅ 4. Professional/Healthcare License
   - Home health agency license (if applicable)
   - Personal care provider license
   - Any relevant certifications
   - Must be current

✅ 5. Proof of Liability Insurance
   - Certificate of Insurance
   - Shows adequate coverage
   - Names Ohio Medicaid as certificate holder (if required)
   - Minimum coverage amounts met

✅ 6. NPI Verification
   - NPI Registry printout
   - Shows organization NPI
   - Confirms active status

✅ 7. ODM Provider Enrollment Confirmation
   - Printout from PNM portal
   - Shows provider number(s)
   - Confirms active enrollment status

✅ 8. Authorization Letter (if using agent/clearinghouse)
   - Letter authorizing third party
   - Signed by business owner/officer
   - Specifies scope of authorization
```

**Technical Documentation (for SFTP/Web Services):**
```
✅ 9. Network Diagram
   - Shows your system architecture
   - Connection flow to ODM
   - Security components (firewall, encryption)

✅ 10. Technical Specifications
   - Server specifications
   - Security protocols used
   - File formats and standards
   - Error handling procedures

✅ 11. IP Address Documentation
   - Public IP address(es)
   - Certificate from ISP (if requested)
   - Confirmation of static IP

✅ 12. Testing Plan (optional but helpful)
   - Test scenarios
   - Test timeline
   - Success criteria
   - Contact information for testing
```

---

## Where to Submit

### Submission Methods:

**1. Online (Preferred):**
- Via Trading Partner Management Application portal
- Upload documents directly
- Track application status online

**2. Email:**
- To: EDI-TP-Comments@medicaid.ohio.gov
- Subject: "Trading Partner Application - [Your Company Name]"
- Attach all documents as PDFs
- Include cover letter with summary

**3. Mail (if required):**
```
Ohio Department of Medicaid
EDI Trading Partner Unit
50 West Town Street, Suite 400
Columbus, OH 43215
```

---

## Information Specific to AZAI Application

### Your Application Details:

**Business Type:** Healthcare Software / Billing Service

**Services Provided:**
- Electronic timesheet processing
- Claims generation for home healthcare services
- EDI 837P claim submission
- Electronic remittance (835) receipt

**Transaction Types Needed:**
- ✅ **837P (Professional Claims)** - PRIMARY
  - For home health aide services
  - Personal care services
  - Homemaker services
  
- ✅ **835 (Remittance Advice)** - ESSENTIAL
  - Receive payment information
  - Post payments to accounts
  - Track claim status

- ⚠️ **276/277 (Claim Status)** - OPTIONAL but recommended
  - Check claim status programmatically
  - Automate status updates

**Recommended Connection Method:**
**SFTP (Secured File Transfer Protocol)**

**Why SFTP for AZAI:**
1. Automated batch processing
2. Your application can schedule uploads
3. No manual intervention needed
4. Supports high volume
5. Standard for billing services
6. 24/7 availability

**Technical Requirements for SFTP:**
```
Your Server Needs:
- Static public IP address
- SSH/SFTP client software
- Secure file storage
- Automated upload scripts
- Error logging and monitoring
- Firewall configured to allow outbound SFTP

ODM Will Provide:
- SFTP server hostname
- Port number (typically 22)
- Authentication credentials
- Connection instructions
- Testing endpoint
```

---

## Timeline & Expectations

### Enrollment Timeline:

```
Week 1-2:   Complete PNM Provider Enrollment
            └─ Submit all documents
            └─ Wait for provider number assignment

Week 2:     Obtain NPI (if not already done)
            └─ Apply online
            └─ Receive immediately

Week 2-3:   Complete Trading Partner Application
            └─ Access OH|ID portal
            └─ Fill out application
            └─ Upload documents

Week 3-4:   ODM Reviews Application
            └─ Background checks
            └─ Document verification
            └─ Compliance review

Week 4:     Receive Trading Partner Number
            └─ 7-digit TPXXXXX ID
            └─ Connectivity instructions

Week 5-6:   Technical Setup & Testing
            └─ Configure SFTP connection
            └─ Submit test claims
            └─ Validate responses
            └─ Fix any issues

Week 7:     Certification Testing
            └─ End-to-end testing
            └─ All transaction types
            └─ Error handling
            └─ Performance testing

Week 8:     Production Authorization
            └─ ODM approves for production
            └─ Switch from test to prod
            └─ Begin live claims

Total: 8-10 weeks from start to production
```

---

## Testing Requirements

### Test Environment:

**What You Must Test:**
```
✅ 837P Claim Submission
   - Valid claims accepted
   - Invalid claims rejected with appropriate errors
   - All required fields present
   - Proper formatting

✅ 835 Remittance Receipt
   - Receive payment files
   - Parse correctly
   - Match to claims

✅ Error Handling
   - Syntax errors caught
   - Payer-specific edits
   - Missing data identified
   - Clear error messages

✅ Volume Testing
   - Multiple claims in batch
   - Large file handling
   - Performance acceptable
```

**Test Provider Numbers:**
- ODM will provide test provider IDs
- Use only these for testing
- Maximum 5 initially
- Do not use real provider numbers in test

**Test Data:**
- Use fictitious patient information
- Use test NPIs provided by ODM
- Use test dates of service
- Do not submit real claims in test

---

## HIPAA Compliance Requirements

### Required Compliance:

**✅ SNIP Validation (Must Pass):**
```
Type 1: Syntax Errors
  - Proper EDI format
  - All required segments
  - Correct data types

Type 2: Balance Errors
  - Financial calculations correct
  - Amounts balance

Type 3: Situational Errors
  - Required data present when needed
  - Conditional logic correct

Type 4: Payer-Specific Edits
  - Ohio Medicaid rules
  - Companion guide requirements

Type 5: Code Set Validation
  - Valid diagnosis codes (ICD-10)
  - Valid procedure codes (HCPCS)
  - Valid place of service

Type 7: Implementation Guide
  - HIPAA 5010 compliance
  - Proper transaction structure
```

**✅ Security Requirements:**
```
- HIPAA Security Rule compliance
- Encryption in transit (TLS 1.2+)
- Encryption at rest
- Access controls
- Audit logging
- Disaster recovery plan
- Business Associate Agreements
```

---

## Support & Contact Information

### ODM EDI Support:
```
Email:    omesedisupport@medicaid.ohio.gov
Phone:    800-686-1516
Hours:    Monday-Friday, 8:00 AM - 5:00 PM EST
Website:  https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners
```

### Trading Partner Questions:
```
Email:    EDI-TP-Comments@medicaid.ohio.gov
```

### Technical Issues:
```
Email:    omesedisupport@medicaid.ohio.gov
Subject:  "Technical Issue - TP#[Your TP Number]"
```

---

## Cost Information

### Fees:

**Ohio Medicaid EDI Connectivity:**
- ✅ **FREE** - No fees charged by ODM

**Other Potential Costs:**
```
NPI Application:           $0 (FREE)
PNM Provider Enrollment:   $0 (FREE - for most providers)
OH|ID Account:            $0 (FREE)
Trading Partner Enrollment: $0 (FREE)

Potential Costs:
- Clearinghouse fees (if using one): $50-500/month
- Technical implementation: Development time
- Testing: Development time
- Ongoing maintenance: Minimal
```

---

## Next Steps for AZAI

### Immediate Actions (This Week):

1. **Create OH|ID Account**
   - Go to InnovateOhio Platform
   - Complete registration
   - Enable MFA
   - **Time: 30 minutes**

2. **Verify NPI**
   - Check if you have organizational NPI
   - If not, apply at NPPES
   - **Time: 30 minutes to 24 hours**

3. **Start PNM Enrollment**
   - Access provider enrollment portal
   - Begin application
   - Gather required documents
   - **Time: 2-4 hours to complete**

4. **Gather Business Documents**
   - W-9 form
   - Business license
   - Certificate of Good Standing
   - Professional licenses
   - Insurance certificate
   - **Time: 1-2 days to collect**

### Short Term (Next 2 Weeks):

5. **Complete PNM Enrollment**
   - Submit all documents
   - Follow up as needed
   - **Wait time: 30-60 days**

6. **Download and Review Companion Guides**
   - 837P Companion Guide
   - 835 Companion Guide
   - Trading Partner User Guide
   - **Time: 4-8 hours to review**

7. **Plan Technical Implementation**
   - Decide on SFTP vs Web Services
   - Identify server for SFTP
   - Confirm static IP address
   - **Time: 1-2 days**

### Medium Term (Weeks 3-6):

8. **Complete Trading Partner Application**
   - Access portal with OH|ID
   - Fill out application
   - Submit documents
   - **Time: 2-4 hours**

9. **Complete EDI Connectivity Form**
   - Choose connection method
   - Provide technical details
   - Submit form
   - **Time: 1-2 hours**

10. **Receive Trading Partner Number**
    - Wait for ODM approval
    - Receive TPXXXXX ID
    - Get connectivity instructions
    - **Wait time: 1-2 weeks**

### Long Term (Weeks 7-10):

11. **Technical Setup**
    - Configure SFTP connection
    - Test connectivity
    - Implement file generation
    - **Time: 1-2 weeks development**

12. **Testing Phase**
    - Submit test claims
    - Validate responses
    - Fix issues
    - **Time: 2-3 weeks**

13. **Certification**
    - Complete all test scenarios
    - Pass ODM validation
    - Receive production approval
    - **Time: 1 week**

14. **Go Live**
    - Switch to production
    - Submit first real claims
    - Monitor closely
    - **Time: 1 day + ongoing monitoring**

---

## Checklist Summary

Use this as your master checklist:

### ☐ Prerequisites
- [ ] OH|ID account created
- [ ] MFA enabled
- [ ] NPI obtained (Type 2 - Organization)
- [ ] PNM provider enrollment submitted

### ☐ Documents Gathered
- [ ] W-9 Form
- [ ] Certificate of Good Standing
- [ ] Business License
- [ ] Professional Healthcare License
- [ ] Liability Insurance Certificate
- [ ] NPI Registry printout
- [ ] Tax ID documentation

### ☐ Applications Submitted
- [ ] Trading Partner Management Application
- [ ] EDI Connectivity Form
- [ ] All supporting documents attached

### ☐ Technical Preparation
- [ ] Connection method selected (SFTP recommended)
- [ ] Static IP address confirmed
- [ ] Server specifications documented
- [ ] Development timeline planned

### ☐ Testing Preparation
- [ ] Companion Guides reviewed
- [ ] Test provider numbers obtained
- [ ] Test plan created
- [ ] Test environment configured

### ☐ Production Readiness
- [ ] All tests passed
- [ ] ODM certification received
- [ ] Production credentials obtained
- [ ] Go-live date scheduled
- [ ] Monitoring plan in place

---

**Document Created:** December 2024  
**For:** AZAI Healthcare Timesheet Application  
**Purpose:** Ohio Medicaid EDI Connectivity Enrollment

**Keep this document updated as you progress through the enrollment process!**
