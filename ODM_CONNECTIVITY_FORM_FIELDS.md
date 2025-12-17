# OMES EDI Connectivity Form - Required Fields

**Form Version:** April 26, 2024  
**Download:** https://dam.assets.ohio.gov/image/upload/medicaid.ohio.gov/Providers/Billing/TradingPartners/OMES_EDI_TP_Connectivity_Form_04262024.pdf

---

## Section 1: Trading Partner Information

### Company Details
```
Trading Partner Legal Name:          [Exact name as on IRS documents]
Trading Partner DBA Name:            [If different from legal name]
Trading Partner Number:              [Leave blank if new - ODM will assign]
                                     [Format: TPXXXXX - 7 digits]

Physical Business Address:
    Street:                          [Street address - no PO Box]
    Suite/Unit:                      [If applicable]
    City:                            [City]
    State:                           [OH]
    ZIP Code:                        [XXXXX-XXXX]

Mailing Address (if different):
    Street:                          [Street or PO Box]
    City:                            [City]
    State:                           [State]
    ZIP Code:                        [XXXXX-XXXX]

Main Phone:                          [(XXX) XXX-XXXX]
Fax:                                 [(XXX) XXX-XXXX] (if applicable)
Company Website:                     [https://yourwebsite.com]
```

### Primary Business Contact
```
Contact Name:                        [First and Last Name]
Title:                               [President/Owner/CEO/Manager]
Email:                               [primary@company.com]
Direct Phone:                        [(XXX) XXX-XXXX]
```

### Technical Contact (Person who will handle EDI setup)
```
Contact Name:                        [First and Last Name]
Title:                               [IT Manager/System Administrator]
Email:                               [technical@company.com]
Direct Phone:                        [(XXX) XXX-XXXX]
Available Hours:                     [e.g., M-F 9AM-5PM EST]
```

### EDI/Billing Contact
```
Contact Name:                        [First and Last Name]
Title:                               [EDI Coordinator/Billing Manager]
Email:                               [edi@company.com]
Direct Phone:                        [(XXX) XXX-XXXX]
```

---

## Section 2: Business Identification

### Tax Information
```
Federal Tax ID (EIN):                [XX-XXXXXXX]
    ☐ EIN (Employer Identification Number)
    ☐ SSN (Social Security Number - sole proprietor only)

State of Ohio Tax ID:                [If applicable]
DUNS Number:                         [Optional - 9 digits]
```

### Provider Information
```
Organizational NPI (Type 2):         [10-digit number]
NPI Enumeration Date:                [MM/DD/YYYY]

Primary ODM Provider Number(s):      [List all provider IDs]
    Provider #1:                     [XXXXXXXXX]
    Provider Type:                   [e.g., Home Health Agency]
    
    Provider #2:                     [If applicable]
    Provider Type:                   [Type]
    
    (Add additional as needed)

Test Provider Numbers:               [ODM will assign for testing]
    Test #1:                         [To be provided by ODM]
    Test #2:                         [To be provided by ODM]
    (Maximum 5 for initial testing)
```

---

## Section 3: Transaction Types

### Select All That Apply:

**Claims Submission:**
```
☐ 837P - Professional Claims
    Used for: Home health services, personal care, therapy
    AZAI Needs: ✅ YES - CHECK THIS

☐ 837I - Institutional Claims
    Used for: Hospital, facility services
    AZAI Needs: ❌ NO (unless you bill for facilities)

☐ 837D - Dental Claims
    Used for: Dental services only
    AZAI Needs: ❌ NO
```

**Payment/Remittance:**
```
☐ 835 - Remittance Advice (Payment Information)
    Used for: Receive payment details, EOB information
    AZAI Needs: ✅ YES - CHECK THIS
```

**Claim Status:**
```
☐ 276 - Claim Status Inquiry
    Used for: Check status of submitted claims
    AZAI Needs: ⚠️ OPTIONAL but recommended

☐ 277 - Claim Status Response
    Used for: Receive claim status updates
    AZAI Needs: ⚠️ OPTIONAL but recommended
```

**Eligibility:**
```
☐ 270 - Eligibility Inquiry
    Used for: Check patient eligibility
    AZAI Needs: ⚠️ OPTIONAL

☐ 271 - Eligibility Response
    Used for: Receive eligibility information
    AZAI Needs: ⚠️ OPTIONAL
```

**Prior Authorization:**
```
☐ 278 - Prior Authorization Request/Response
    Used for: Services requiring prior auth
    AZAI Needs: ⚠️ OPTIONAL (if your services need prior auth)
```

**Enrollment:**
```
☐ 834 - Benefit Enrollment
    Used for: Health plan enrollment
    AZAI Needs: ❌ NO (MCE use only)
```

---

## Section 4: Connectivity Method

### Choose ONE Primary Method:

**Option A: SFTP (Recommended for AZAI)**
```
☐ SFTP (Secured File Transfer Protocol)

✅ Why choose SFTP:
    - Automated batch processing
    - 24/7 availability
    - High volume support
    - Standard for billing services

Required Technical Information:

Company Static IP Address(es):
    Primary IP:                      [XXX.XXX.XXX.XXX]
    Secondary IP (if applicable):    [XXX.XXX.XXX.XXX]
    
    ⚠️ MUST be static (not dynamic)
    ⚠️ Obtain from your ISP or hosting provider

Firewall Configuration:
    ☐ Firewall exceptions needed: Yes/No
    ☐ Outbound connections allowed: Yes/No
    
Server/System Information:
    Operating System:                [e.g., Linux, Windows Server]
    SFTP Client Software:            [e.g., FileZilla, WinSCP, custom]
    
Connection Preference:
    ☐ Inbound (ODM connects to you) - Not typical
    ☐ Outbound (You connect to ODM) - ✅ RECOMMENDED
    
File Transfer Schedule:
    Submission Time:                 [e.g., Daily at 8:00 PM EST]
    Expected Volume:                 [e.g., 50 claims per day]
    File Naming Convention:          [Per companion guide]
```

**Option B: Web Services (SOAP)**
```
☐ CAQH/CORE Compliant Web Services

✅ Why choose Web Services:
    - Real-time submission
    - Immediate response
    - Synchronous processing

Required Technical Information:

Your Web Service Endpoint:
    URL:                             [https://your-endpoint.com/soap]
    Port:                            [Usually 443]
    
WSDL Location:
    URL:                             [https://your-site.com/service.wsdl]
    
Authentication Method:
    ☐ Username/Password
    ☐ Certificate-based
    ☐ OAuth
    ☐ API Key
    
SSL Certificate Information:
    Certificate Authority:           [e.g., DigiCert, Let's Encrypt]
    Expiration Date:                [MM/DD/YYYY]
    
Request/Response Format:
    ☐ XML
    ☐ JSON
    ☐ Other: ________________
```

**Option C: HTTPS Browser (Manual)**
```
☐ HTTPS Browser (EDI Web Application)

✅ Why choose Browser:
    - No technical setup
    - Good for testing
    - Manual submission

⚠️ Limitations:
    - Manual only
    - Low volume
    - Not suitable for automated systems

No additional technical information required
```

---

## Section 5: Security & Compliance

### Encryption & Security
```
Data Encryption in Transit:
    ☐ TLS 1.2 or higher: Yes/No
    ☐ SSL Certificate: Yes/No
    
Data Encryption at Rest:
    ☐ Files encrypted on server: Yes/No
    ☐ Encryption method: [AES-256, etc.]

File Encryption (optional):
    ☐ PGP/GPG encryption: Yes/No
    ☐ Public key provided: Yes/No
```

### Network Security
```
Firewall Configuration:
    Firewall Brand/Model:            [e.g., Cisco, Fortinet]
    Inbound Rules:                   [Describe]
    Outbound Rules:                  [Describe]
    
    Ports to be opened:
    ☐ Port 22 (SFTP)
    ☐ Port 443 (HTTPS/SOAP)
    ☐ Other: ________________

VPN Requirements:
    ☐ VPN connection required: Yes/No
    ☐ VPN Type: [If yes]
```

### HIPAA Compliance Attestation
```
☐ I attest that our organization is HIPAA compliant
☐ We have completed HIPAA Security Risk Assessment
☐ We have Business Associate Agreements in place
☐ We have incident response procedures
☐ We maintain audit logs of all EDI transactions
```

---

## Section 6: Testing Information

### Test Environment Specifications
```
Test Start Date (desired):          [MM/DD/YYYY]

Testing Contact Person:
    Name:                            [First and Last Name]
    Email:                           [testing@company.com]
    Phone:                           [(XXX) XXX-XXXX]

Testing Plan:
    Expected Test Duration:          [e.g., 2-3 weeks]
    Test Scenarios:                  [List key scenarios]
    
Test Volume Estimates:
    Test Claims per Week:            [Number]
    Test File Size:                  [KB/MB]

Technical Test Details:
    ☐ Syntax testing (SNIP Type 1)
    ☐ Balance testing (SNIP Type 2)
    ☐ Situational testing (SNIP Type 3)
    ☐ Payer-specific rules (SNIP Type 4)
    ☐ Code validation (SNIP Type 5)
    ☐ Implementation guide compliance (SNIP Type 7)
```

### Production Estimates
```
Expected Production Go-Live Date:    [MM/DD/YYYY]

Production Volume Estimates:
    Daily Claims:                    [Number]
    Weekly Claims:                   [Number]
    Monthly Claims:                  [Number]
    
Peak Processing Times:
    Day of Week:                     [e.g., Mondays]
    Time of Day:                     [e.g., 6-8 PM EST]
    
Expected File Sizes:
    Average File Size:               [MB]
    Maximum File Size:               [MB]
```

---

## Section 7: Companion Guides Acknowledgment

### Required Attestations (Check all):

```
☐ I have downloaded and reviewed the following guides:

    ☐ 837P Professional Claim Companion Guide
    ☐ 835 Remittance Advice Companion Guide
    ☐ 276/277 Claim Status Companion Guide (if applicable)
    ☐ 270/271 Eligibility Companion Guide (if applicable)
    ☐ OMES EDI Trading Partner User Guide
    ☐ HIPAA 5010 Implementation Guide

☐ I understand SNIP validation requirements (Types 1-7)

☐ I understand ODM-specific payer rules

☐ I will test all transactions in test environment before production

☐ I will submit test claims using only test provider numbers

☐ I will not submit test data in production environment
```

---

## Section 8: Additional Information

### Clearinghouse Information (if applicable)
```
Using a Clearinghouse:              ☐ Yes  ☐ No

If Yes:
    Clearinghouse Name:              [Name]
    Clearinghouse TP Number:         [If known]
    Relationship:                    [Direct client, sub-contractor, etc.]
    
    Authorization:
    ☐ Letter of authorization attached
    ☐ Clearinghouse contact information provided
```

### Software Vendor Information
```
Billing Software Used:               [Software name]
Software Version:                    [Version number]
Vendor Name:                         [Vendor name]
Vendor Contact:                      [Phone/Email]

Custom Development:
    ☐ In-house development
    ☐ Third-party vendor
    ☐ Hybrid approach
```

### Special Circumstances (if any)
```
Describe any special requirements or circumstances:

[Free text field]

Examples:
- High volume submission needs
- Multiple entities under one trading partner
- Specific connectivity requirements
- Timeline constraints
```

---

## Section 9: Authorized Signature

### Required Signatures

**Primary Signatory (Business Owner/Officer):**
```
Printed Name:                        [Full name]
Title:                               [President/CEO/Owner/Authorized Officer]
Signature:                           [Signature]
Date:                                [MM/DD/YYYY]

☐ I certify that I am authorized to sign on behalf of this organization
☐ All information provided is accurate and complete
☐ I agree to notify ODM of any changes to this information
```

**Technical Contact (Optional but Recommended):**
```
Printed Name:                        [Full name]
Title:                               [IT Manager/Technical Lead]
Signature:                           [Signature]
Date:                                [MM/DD/YYYY]
```

---

## Section 10: Attachments Checklist

### Required Attachments (Check all that apply):

**Business Documentation:**
```
☐ W-9 Form (IRS) - current year
☐ Certificate of Good Standing (Ohio Secretary of State - last 90 days)
☐ Business License (copy)
☐ Professional/Healthcare Agency License (copy)
☐ Articles of Incorporation OR Operating Agreement
☐ Liability Insurance Certificate
☐ NPI Registry printout (showing organizational NPI)
☐ ODM Provider enrollment confirmation
```

**Technical Documentation (for SFTP/Web Services):**
```
☐ Network diagram showing connection architecture
☐ IP address documentation/verification
☐ Firewall configuration details
☐ SSL certificate (if applicable)
☐ Public PGP/GPG key (if using encryption)
☐ WSDL file (if using Web Services)
☐ Sample file formats (optional but helpful)
```

**Authorization Documents (if applicable):**
```
☐ Clearinghouse authorization letter
☐ Business Associate Agreement (if not already on file)
☐ Third-party vendor authorization (if applicable)
```

---

## Quick Reference: AZAI Application Recommended Settings

### For AZAI Healthcare Timesheet Application:

**Section 1 - Company Info:**
```
Legal Name:        [Your registered business name]
DBA:              AZAI Healthcare Solutions (or your DBA)
```

**Section 3 - Transaction Types:**
```
✅ CHECK: 837P (Professional Claims)
✅ CHECK: 835 (Remittance Advice)
⚠️  OPTIONAL: 276/277 (Claim Status)
```

**Section 4 - Connectivity:**
```
✅ SELECT: SFTP (Secured File Transfer Protocol)
    - Reason: Automated batch processing
    - Your static IP: [Obtain from your host/ISP]
    - Connection: Outbound (you connect to ODM)
    - Schedule: Daily evening batch
```

**Section 5 - Security:**
```
✅ TLS 1.2+: Yes
✅ Encryption at rest: Yes
✅ HIPAA compliant: Yes
```

**Section 6 - Testing:**
```
Start Date: [2-3 weeks after submission]
Duration: 2-3 weeks
Volume: 10-20 test claims
```

---

## Form Submission

### How to Submit:

**Preferred Method: Online Portal**
1. Log in to Trading Partner Management Application
2. Navigate to "Documents" or "Forms"
3. Upload completed PDF form
4. Upload all required attachments
5. Submit

**Alternative: Email**
- To: EDI-TP-Comments@medicaid.ohio.gov
- Subject: "EDI Connectivity Form - [Your Company Name]"
- Attach: Completed form + all required documents
- Body: Brief cover letter explaining submission

**Confirmation:**
- You should receive confirmation within 1-2 business days
- Follow up if no response within 3 business days

---

## Important Notes

**Before You Submit:**
- ✅ All fields completed (no blanks in required sections)
- ✅ All checkboxes marked appropriately
- ✅ All signatures obtained
- ✅ All attachments included
- ✅ Contact information verified
- ✅ IP addresses confirmed static
- ✅ Test dates realistic

**After Submission:**
- Save copy of submitted form
- Note submission date
- Wait for ODM confirmation email
- Respond promptly to any questions
- Prepare for testing phase

---

**Estimated Time to Complete Form:** 1-2 hours  
**Required Level:** Must be completed by authorized officer with technical input

**Need Help?**
- Email: EDI-TP-Comments@medicaid.ohio.gov
- Phone: 800-686-1516
- Hours: M-F 8AM-5PM EST
