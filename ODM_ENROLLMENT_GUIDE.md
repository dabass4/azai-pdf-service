# Ohio Medicaid Trading Partner Enrollment Guide

**Complete Step-by-Step Guide for Electronic Claims Submission**

---

## Overview

This guide walks you through the complete process of becoming an authorized trading partner with the Ohio Department of Medicaid (ODM) for electronic claim submission via 837P files.

**Timeline:** 4-8 weeks  
**Difficulty:** Moderate  
**Cost:** No fees from ODM

---

## Prerequisites

Before starting, ensure you have:
- [ ] Valid Ohio Medicaid Provider ID
- [ ] Business Entity registered with Ohio
- [ ] IT staff or vendor for EDI implementation
- [ ] Technical knowledge of HIPAA X12 837P format
- [ ] Test provider data ready (up to 5 providers)

---

## Step 1: Review ODM Trading Partner Information Guide

**Objective:** Understand ODM's requirements and process

### Actions:
1. Download the Trading Partner Information Guide:
   - URL: https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners
   - File: "Trading Partner Information Guide" (PDF)

2. Review key sections:
   - Trading partner definition
   - Enrollment requirements
   - Testing procedures
   - Production certification process
   - Contact information

3. Familiarize yourself with:
   - ODM's expectations for trading partners
   - Timeline for enrollment and testing
   - Technical requirements
   - Support resources available

**Duration:** 2-4 hours  
**Output:** Understanding of enrollment process

---

## Step 2: Review HIPAA ASC X12 Technical Reports (TR3)

**Objective:** Understand the 837P transaction technical specifications

### Actions:
1. Visit X12.org or Washington Publishing Company (WPC):
   - X12: https://x12.org
   - WPC: https://www.wpc-edi.com

2. Obtain 837P TR3 documentation:
   - HIPAA 5010 version
   - 837 Professional Healthcare Claim (837P)
   - Implementation Guide

3. Study key sections:
   - ISA segment (Interchange Control Header)
   - GS segment (Functional Group Header)
   - ST segment (Transaction Set Header)
   - CLM segment (Claim Information)
   - SV1 segment (Professional Service)
   - Loop structures (2000A, 2000B, 2300, 2400)

**Duration:** 4-8 hours  
**Output:** Technical understanding of 837P format  
**Cost:** ~$100-200 for TR3 documentation (one-time)

---

## Step 3: Begin Trading Partner Enrollment

**Objective:** Register with ODM as a trading partner

### Actions:
1. Access the Trading Partner Management Application:
   - URL: https://ohmits.medicaid.ohio.gov (check current URL with ODM)
   - Login or create account

2. Complete enrollment application:
   - Organization information
   - Contact person details
   - Technical contact information
   - Business entity details
   - Provider information

3. Designate roles:
   - Primary Contact (business decisions)
   - Technical Contact (EDI implementation)
   - Authorized Submitter (who will submit files)

4. Submit application through portal

**Duration:** 1-2 hours  
**Output:** Application submitted to ODM

---

## Step 4: Review ODM Companion Guides

**Objective:** Understand Ohio-specific requirements for 837P

### Actions:
1. Download Ohio Medicaid Companion Guide:
   - URL: https://medicaid.ohio.gov/resources-for-providers/billing/hipaa-5010-implementation/companion-guides/guides
   - File: "837P Companion Guide" (latest version)

2. Review Ohio-specific requirements:
   - Receiver ID format (ODMITS)
   - Sender ID format (your 7-digit ID when assigned)
   - Required vs. optional fields
   - Ohio-specific code sets
   - Edit validation rules
   - Common rejection reasons

3. Note Ohio deviations from standard TR3:
   - Additional required fields
   - Ohio-specific qualifiers
   - Validation criteria
   - Formatting requirements

4. Document implementation notes:
   - Fields your system must populate
   - Data mappings required
   - Changes needed to existing systems

**Duration:** 4-6 hours  
**Output:** Implementation checklist for your development team

---

## Step 5: Coordinate Testing Strategy

**Objective:** Plan internal testing before ODM testing

### Actions:
1. Assemble your team:
   - IT/Development staff
   - Billing staff
   - Compliance officer
   - Project manager

2. Develop testing plan:
   - Internal testing timeline
   - Test data preparation
   - Validation procedures
   - Quality assurance checks

3. Prepare test scenarios:
   - Standard claims (most common)
   - Claims with multiple service lines
   - Claims with diagnosis codes
   - Claims with rendering providers
   - Claims with unusual circumstances

4. Set up testing environment:
   - Test database with sample data
   - 837P file generator
   - File validation tools
   - Internal review process

5. Schedule milestones:
   - Internal testing completion
   - ODM test submission date
   - Production go-live target

**Duration:** 1-2 weeks  
**Output:** Detailed testing plan and timeline

---

## Step 6: Complete Trading Partner Agreement

**Objective:** Sign legal agreement with ODM

### Actions:
1. Receive Trading Partner Agreement from ODM:
   - Typically sent after enrollment application approval
   - May take 1-2 weeks to receive

2. Review agreement terms:
   - Trading partner responsibilities
   - Data security requirements
   - HIPAA compliance obligations
   - Submission standards
   - Liability clauses
   - Termination conditions

3. Obtain necessary signatures:
   - Authorized officer of your organization
   - Legal review (recommended)
   - Compliance review

4. Submit signed agreement:
   - Return to ODM per instructions
   - Keep copy for your records
   - Wait for ODM counter-signature

**Duration:** 1-2 weeks  
**Output:** Executed Trading Partner Agreement  
**Note:** This is a legal requirement - cannot proceed without signed agreement

---

## Step 7: Complete EDI Connectivity Form

**Objective:** Establish secure file transmission method

### Actions:
1. Receive EDI Connectivity Form:
   - Sent by ODM after agreement approval
   - May be part of enrollment portal

2. Choose connectivity method:
   - **Option A: SFTP (Secure File Transfer Protocol)**
     * Most common method
     * Requires SFTP client software
     * ODM provides server details
   - **Option B: AS2 (Applicability Statement 2)**
     * More complex setup
     * Real-time transmission
     * Requires AS2 software

3. Complete connectivity form:
   - Your organization's details
   - Technical contact information
   - Preferred connection method (SFTP/AS2)
   - IP addresses (if required)
   - Security credentials request

4. Submit form to ODM

5. Receive connectivity credentials:
   - SFTP hostname, username, password
   - OR AS2 endpoint and certificates
   - Connection instructions
   - Testing procedures

**Duration:** 1-2 weeks (including ODM response)  
**Output:** Active EDI connectivity  
**Security Note:** Store credentials securely; never share publicly

---

## Step 8: Verify Trading Partner Number

**Objective:** Receive and configure your unique ODM identifier

### Actions:
1. Receive 7-digit Trading Partner ID:
   - ODM assigns unique Sender/Receiver ID
   - Typically sent via email
   - Format: 7 numeric digits (e.g., 1234567)

2. Document your IDs:
   - **Sender ID:** Your organization (7 digits)
   - **Receiver ID:** ODMITS (Ohio Medicaid)
   - Test environment IDs (if different)

3. Configure your system:
   - Update ISA segment with Sender ID
   - Set Receiver ID to ODMITS
   - Test indicator: "T" for test, "P" for production
   - Verify all segments use correct IDs

4. Update application settings:
   - In our app: Navigate to Claims > ODM Enrollment
   - Click "Update Trading Partner ID"
   - Enter your 7-digit ID
   - Save changes

**Duration:** Immediate once received  
**Output:** System configured with correct ODM IDs  
**Important:** Test and production IDs may differ

---

## Step 9: Provide Test Provider List

**Objective:** Identify providers for test claim submission

### Actions:
1. Select up to 5 test providers:
   - Actual providers in your organization
   - Variety of service types
   - Valid NPI numbers
   - Active in Ohio Medicaid

2. Gather required information for each:
   - Provider Name
   - NPI (National Provider Identifier)
   - Ohio Medicaid Provider ID
   - Taxonomy Code
   - Provider Type

3. Submit test provider list to ODM:
   - Format as requested (usually Excel or email)
   - Include all required fields
   - Verify accuracy of all data
   - Send to designated ODM contact

4. Wait for ODM confirmation:
   - ODM will validate providers
   - May request corrections
   - Approval needed before testing

**Duration:** 3-5 business days  
**Output:** Approved test provider list

---

## Step 10: Submit Test Claims

**Objective:** Submit test 837P files to ODM test environment

### Actions:
1. Generate test 837P files:
   - In our app: Navigate to Claims > Generate 837P
   - Select test timesheets
   - Generate EDI files
   - Download .edi files

2. Validate files before submission:
   - Check ISA segment: Sender ID, Test indicator "T"
   - Verify all required loops present
   - Confirm test provider NPI numbers
   - Validate dates and amounts
   - Use validation software if available

3. Submit files to ODM test environment:
   - Use SFTP or AS2 connectivity
   - Follow ODM file naming conventions
   - Place in designated inbound folder
   - Verify successful transmission

4. Submit variety of test scenarios:
   - Single service line claim
   - Multiple service lines
   - Different service codes
   - Various diagnosis codes
   - Different patient scenarios
   - Aim for 10-20 test claims

5. Document all submissions:
   - File names
   - Submission dates/times
   - Claim IDs
   - Expected outcomes

**Duration:** 1-2 weeks (including multiple iterations)  
**Output:** Suite of test claims submitted  
**Tip:** Start simple, add complexity gradually

---

## Step 11: Verify EDI Receipts

**Objective:** Receive and validate ODM response files

### Actions:
1. Monitor for response files in SFTP outbound folder:
   - Check daily (or more frequently)
   - ODM typically responds within 24-48 hours
   - Multiple response types to expect

2. Retrieve and process response files:

   **999 - Implementation Acknowledgment:**
   - Confirms file was received and structurally valid
   - First response you'll receive (usually within hours)
   - Status: Accepted (R), Rejected (R), Partially Accepted (M)
   - Must receive "Accepted" status to proceed

   **824 - Application Advice:**
   - Optional, not always sent
   - Application-level acknowledgment

   **277CA - Claim Acknowledgment:**
   - Confirms individual claims received
   - Status per claim
   - May take 24-48 hours
   - Look for acceptance or rejection reasons

   **835 - Remittance Advice:**
   - Payment/adjustment information
   - May not occur in test environment
   - Production only in most cases

3. Analyze responses:
   - Parse response files
   - Check for errors or rejections
   - Document any issues found
   - Identify patterns in rejections

4. Correct and resubmit:
   - Fix identified errors
   - Regenerate 837P files
   - Resubmit corrected claims
   - Track improvements

5. Iterate until clean submissions:
   - Goal: 100% acceptance rate
   - No structural errors
   - All claims accepted
   - Consistent results

6. Request production certification:
   - Email ODM confirming successful testing
   - Provide test submission summary
   - Request approval for production
   - Wait for ODM authorization

**Duration:** 2-4 weeks (including iterations)  
**Output:** ODM approval for production submission  
**Success Criteria:** Multiple successful test submissions with no errors

---

## Post-Enrollment: Production Setup

### Transitioning to Production

1. **Receive Production Credentials:**
   - New SFTP/AS2 credentials (different from test)
   - Production Sender/Receiver IDs (may differ from test)
   - Production submission instructions

2. **Update System Configuration:**
   - Switch from test ("T") to production ("P") indicator
   - Update SFTP/AS2 connection settings
   - Configure production credentials
   - Update Sender/Receiver IDs if changed

3. **Production Validation:**
   - Submit small batch first (5-10 claims)
   - Monitor responses closely
   - Verify payment posting
   - Gradually increase volume

4. **Ongoing Monitoring:**
   - Daily submission schedules
   - Response file monitoring
   - Rejection rate tracking
   - Reconciliation procedures

---

## Common Issues & Solutions

### Application Delays
**Issue:** Enrollment taking longer than expected  
**Solution:** 
- Contact EDI-TP-Comments@medicaid.ohio.gov
- Reference your application number
- Request status update
- Be patient - process takes time

### 999 Rejections
**Issue:** Receiving rejected 999 responses  
**Solution:**
- Review rejection codes in 999
- Check ISA/GS segment formatting
- Verify Sender/Receiver IDs
- Validate against companion guide
- Use X12 validation tools

### 277CA Rejections
**Issue:** Claims rejected at claim level  
**Solution:**
- Review rejection reason codes
- Check NPI numbers are valid
- Verify procedure codes
- Confirm diagnosis codes
- Ensure patient Medicaid IDs are active
- Review companion guide requirements

### Connectivity Issues
**Issue:** Cannot connect to SFTP server  
**Solution:**
- Verify hostname, username, password
- Check firewall settings
- Confirm your IP is whitelisted (if required)
- Test connection with different client
- Contact ODM technical support

### Missing Responses
**Issue:** Not receiving 999/277 responses  
**Solution:**
- Check outbound folder regularly
- Verify file naming conventions
- Confirm submission was successful
- Contact ODM if delayed >48 hours
- Check spam/junk folders for email notifications

---

## ODM Contact Information

**EDI Trading Partner Support:**
- Email: EDI-TP-Comments@medicaid.ohio.gov
- Response time: 1-3 business days

**Provider Support (General Claims):**
- Phone: (800) 686-1516
- Hours: Monday-Friday, 8:00 AM - 5:00 PM EST

**ODM Website:**
- https://medicaid.ohio.gov

**Trading Partner Portal:**
- https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners

**Companion Guides:**
- https://medicaid.ohio.gov/resources-for-providers/billing/hipaa-5010-implementation/companion-guides/guides

---

## Checklist Summary

Use this checklist to track your progress:

- [ ] Step 1: Reviewed ODM Information Guide
- [ ] Step 2: Studied HIPAA X12 837P TR3
- [ ] Step 3: Submitted enrollment application
- [ ] Step 4: Reviewed Ohio companion guide
- [ ] Step 5: Created internal testing plan
- [ ] Step 6: Signed Trading Partner Agreement
- [ ] Step 7: Completed EDI connectivity setup
- [ ] Step 8: Received Trading Partner ID
- [ ] Step 9: Submitted test provider list
- [ ] Step 10: Submitted test 837P claims
- [ ] Step 11: Received clean 999/277 responses
- [ ] Production approval granted
- [ ] Production credentials configured
- [ ] First production submission successful

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Steps 1-2: Research | 1 week | 1 week |
| Steps 3-4: Application | 1-2 weeks | 2-3 weeks |
| Steps 5-7: Agreements & Setup | 2-3 weeks | 4-6 weeks |
| Steps 8-9: Configuration | 1 week | 5-7 weeks |
| Steps 10-11: Testing | 2-4 weeks | 7-11 weeks |
| Production Setup | 1 week | 8-12 weeks |

**Total Timeline: 8-12 weeks** (varies based on responsiveness and issue resolution)

---

## Tips for Success

✅ **Start Early** - Begin process well before you need production access  
✅ **Be Thorough** - Don't rush through documentation review  
✅ **Test Extensively** - Better to find issues in test than production  
✅ **Document Everything** - Keep records of all communications and submissions  
✅ **Ask Questions** - ODM support is there to help  
✅ **Be Patient** - Process takes time, plan accordingly  
✅ **Stay Organized** - Track all credentials, IDs, and dates  
✅ **Backup Files** - Keep copies of all submissions and responses  

---

**Version:** 1.0  
**Last Updated:** November 2024  
**Maintained By:** Development Team
