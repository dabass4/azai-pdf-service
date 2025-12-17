# Ohio Medicaid Connectivity - Quick Reference

**Quick checklist for completing ODM enrollment**

---

## Documents You Need (Print This List)

### Core Business Documents
```
☐ W-9 Form (IRS) - current year
☐ Certificate of Good Standing (Ohio Secretary of State - last 90 days)
☐ Business License (Ohio)
☐ Articles of Incorporation OR Operating Agreement
☐ Professional/Healthcare Agency License
☐ Liability Insurance Certificate
```

### Identification Numbers
```
☐ Federal Tax ID (EIN): ___-_______
☐ National Provider Identifier (NPI): __________
☐ ODM Provider Number(s): _________________
☐ Social Security Number (if sole proprietor): ___-__-____
```

### Contact Information Needed
```
Business Legal Name:     _______________________________
DBA Name:               _______________________________
Address:                _______________________________
Phone:                  _______________________________
Email:                  _______________________________

Primary Contact:        _______________________________
Technical Contact:      _______________________________
EDI Contact:           _______________________________
```

### Technical Information (if using SFTP)
```
☐ Static Public IP Address: ___.___.___.___
☐ Server hostname/details
☐ Preferred connection schedule
☐ Expected monthly volume: _______ claims
```

---

## Forms to Complete

### 1. Trading Partner Management Application
**Access:** https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners  
**Login Required:** OH|ID (State of Ohio account)  
**Time:** 30-60 minutes

### 2. OMES EDI Connectivity Form
**Download:** https://dam.assets.ohio.gov/image/upload/medicaid.ohio.gov/Providers/Billing/TradingPartners/OMES_EDI_TP_Connectivity_Form_04262024.pdf  
**Time:** 15-30 minutes  
**Submit:** Via portal or email to EDI-TP-Comments@medicaid.ohio.gov

---

## Transaction Types (Check What You Need)

```
☐ 837P - Professional Claims (HOME HEALTH - YES!)
☐ 837I - Institutional Claims
☐ 835 - Remittance Advice (PAYMENT INFO - YES!)
☐ 276 - Claim Status Inquiry (OPTIONAL - Recommended)
☐ 277 - Claim Status Response (OPTIONAL - Recommended)
☐ 270 - Eligibility Inquiry (OPTIONAL)
☐ 271 - Eligibility Response (OPTIONAL)
```

**For AZAI: Check 837P and 835 at minimum**

---

## Connection Method (Choose One)

### ✅ SFTP (Recommended for AZAI)
```
Pros:
- Automated batch processing
- 24/7 access
- High volume capable
- Standard for billing

Requirements:
- Static public IP
- SFTP client software
- Automated scripts
```

### Web Services (SOAP)
```
Pros:
- Real-time submission
- Immediate response

Requirements:
- SOAP integration
- Web service endpoint
- More complex development
```

### HTTPS Browser (Manual)
```
Pros:
- No technical setup
- Good for testing

Cons:
- Manual only
- Low volume
- Not automated
```

---

## Required Online Accounts

### 1. OH|ID (State of Ohio)
**Create:** https://innovateohio.gov  
**Required For:** All ODM portal access  
**Setup:** 15 minutes + MFA

### 2. NPI Registry
**Apply:** https://nppes.cms.hhs.gov  
**Required:** Before Trading Partner application  
**Time:** Immediate to 24 hours

### 3. Provider Network Management (PNM)
**Access:** Via ODM provider enrollment portal  
**Required:** Must be enrolled provider  
**Time:** 30-60 days processing

---

## Timeline

```
Week 1-2:   Prerequisites (NPI, OH|ID, PNM)
Week 3-4:   Submit Applications & Forms
Week 4-5:   ODM Review & Approval
Week 5-6:   Receive Trading Partner Number
Week 6-8:   Technical Setup & Testing
Week 8-10:  Production Certification
Week 10+:   Go Live

Total: 10-12 weeks
```

---

## Cost

**Everything is FREE from Ohio Medicaid:**
- ✅ NPI Application: $0
- ✅ OH|ID Account: $0
- ✅ Provider Enrollment: $0
- ✅ Trading Partner Registration: $0
- ✅ EDI Connectivity: $0
- ✅ Transaction Processing: $0

**Optional Costs:**
- Clearinghouse (if used): $50-500/month
- Development time: Your cost
- Testing: Your cost

---

## Support Contacts

**EDI Technical Support:**
- Email: omesedisupport@medicaid.ohio.gov
- Phone: 800-686-1516
- Hours: M-F 8am-5pm EST

**Trading Partner Questions:**
- Email: EDI-TP-Comments@medicaid.ohio.gov

**Provider Enrollment:**
- Use PNM portal help desk
- Phone: 800-686-1516

---

## Key Links

**Trading Partners Page:**
https://medicaid.ohio.gov/resources-for-providers/billing/trading-partners

**Provider Enrollment:**
https://medicaid.ohio.gov/resources-for-providers/enrollment-and-support/provider-enrollment

**Connectivity Form (PDF):**
https://dam.assets.ohio.gov/image/upload/medicaid.ohio.gov/Providers/Billing/TradingPartners/OMES_EDI_TP_Connectivity_Form_04262024.pdf

**NPI Registry:**
https://nppes.cms.hhs.gov

**OH|ID Registration:**
https://innovateohio.gov

---

## For AZAI Application Specifically

**Your Service Type:** Healthcare Software / Billing Service

**Transactions Needed:**
1. 837P (Claims) - Primary
2. 835 (Payments) - Essential
3. 276/277 (Status) - Optional but recommended

**Recommended Setup:**
- Connection: SFTP
- Server: Dedicated or cloud-based
- IP: Static public IP required
- Schedule: Daily batch uploads

**What to Tell ODM:**
- You are a software vendor
- You process timesheets for home health agencies
- You generate and submit 837P claims on behalf of providers
- You need automated batch processing

---

## Red Flags to Avoid

**DON'T:**
- ❌ Use fake/test data in production
- ❌ Submit without all required documents
- ❌ Rush the testing phase
- ❌ Skip companion guide review
- ❌ Use dynamic/shared IP addresses
- ❌ Hardcode production credentials in code

**DO:**
- ✅ Read all companion guides
- ✅ Test thoroughly in test environment
- ✅ Keep all credentials secure
- ✅ Document your setup
- ✅ Plan for error handling
- ✅ Monitor submissions closely

---

## Next Immediate Steps

**TODAY:**
1. Create OH|ID account (30 min)
2. Verify you have/apply for NPI (30 min)
3. Gather business documents (1-2 hours)

**THIS WEEK:**
4. Start PNM provider enrollment (2 hours)
5. Download and read companion guides (4 hours)
6. Plan technical implementation (2 hours)

**NEXT WEEK:**
7. Complete Trading Partner application (2 hours)
8. Submit connectivity form (1 hour)
9. Await ODM approval (1-2 weeks)

---

**Print this checklist and keep it handy during enrollment!**

**For detailed instructions, see:**
`/app/OHIO_MEDICAID_CONNECTIVITY_REQUIREMENTS.md`
