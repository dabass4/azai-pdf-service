# Integration Requirements & Mocked APIs

## Overview
This Timesheet Scanner SaaS application has several integrations. Some are fully functional, while others are mocked for testing purposes and require real credentials for production use.

---

## ✅ FULLY FUNCTIONAL INTEGRATIONS

### 1. **Stripe Payment Processing**
- **Status**: ✅ FULLY IMPLEMENTED
- **Features**:
  - Checkout session creation
  - Webhook handling for subscription events
  - Plan management (Basic, Professional, Enterprise)
  - Subscription upgrades/downgrades
- **Configuration**:
  - Environment variables in `/app/backend/.env`:
    - `STRIPE_API_KEY=sk_test_...` (currently using test mode)
    - `STRIPE_WEBHOOK_SECRET=whsec_...` (for webhook verification)
- **Test Mode**: Currently configured with test keys
- **Production Setup**:
  1. Replace test keys with live keys in `.env`
  2. Configure Stripe webhook endpoint: `https://your-domain.com/api/payments/webhook`
  3. Subscribe to events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

### 2. **JWT Authentication**
- **Status**: ✅ FULLY IMPLEMENTED
- **Features**:
  - User signup/login
  - JWT token generation and verification
  - Organization-based multi-tenancy
  - Secure password hashing (bcrypt)
- **Configuration**:
  - `JWT_SECRET` in `/app/backend/.env`
  - Token expiration: 7 days

### 3. **MongoDB Database**
- **Status**: ✅ FULLY IMPLEMENTED
- **Configuration**:
  - `MONGO_URL=mongodb://localhost:27017`
  - `DB_NAME=timesheet_scanner`
- **Collections**: organizations, users, patients, employees, timesheets, claims, insurance_contracts, service_codes, evv_visits, evv_transmissions

### 4. **OpenAI Vision API (OCR)**
- **Status**: ✅ FULLY IMPLEMENTED
- **Purpose**: Extracts data from timesheet PDFs and images
- **Configuration**:
  - Uses `EMERGENT_LLM_KEY` in `.env` (universal key for OpenAI, Anthropic, Google)
- **Library**: `emergentintegrations` package

---

## ⚠️ MOCKED INTEGRATIONS (Require Real Implementation)

### 1. **Sandata API Integration**
- **Status**: ⚠️ MOCKED FOR TESTING
- **Endpoint**: `POST /api/timesheets/{timesheet_id}/submit-sandata`
- **Current Behavior**:
  - Logs submission data
  - Updates timesheet status to "submitted"
  - Returns mock success response
- **What's Needed for Production**:
  - **Sandata Account**: Create account at https://www.sandata.com
  - **API Credentials**:
    - API Key
    - Auth Token
    - Base URL (typically `https://api.sandata.com/v1`)
  - **Configuration**: Update in `/app/backend/.env`:
    ```
    SANDATA_API_URL=https://api.sandata.com/v1
    SANDATA_API_KEY=your_real_api_key
    SANDATA_AUTH_TOKEN=your_real_auth_token
    ```
  - **Implementation File**: `/app/backend/server.py` lines 1008-1055
  - **Documentation**: https://www.sandata.com/api-documentation
  - **Real Implementation Steps**:
    1. Replace mock logic with actual HTTP POST to Sandata API
    2. Handle authentication (OAuth or API key-based)
    3. Format payload according to Sandata specifications
    4. Handle API responses and errors
    5. Implement retry logic for failed submissions

### 2. **Ohio Medicaid Claims Submission**
- **Status**: ⚠️ MOCKED FOR TESTING
- **Endpoints**:
  - `POST /api/claims/{claim_id}/submit` (single claim)
  - `POST /api/claims/bulk-submit` (multiple claims)
- **Current Behavior**:
  - Logs claim data
  - Updates claim status to "submitted"
  - Returns mock reference IDs
- **What's Needed for Production**:
  - **MITS Access**: Ohio Medicaid Information Technology System
  - **Trading Partner Agreement**: Required for electronic claim submission
  - **EDI 837 Format**: Claims must be formatted in EDI 837 (Healthcare Claim) format
  - **Portal Credentials**:
    - Provider ID
    - Trading Partner ID
    - Login credentials
  - **Resources**:
    - Ohio Medicaid Provider Portal: https://medicaid.ohio.gov/providers-partners/providers/billing-and-claims
    - EDI 837 Specifications: HIPAA X12 837 Professional (837P) or Institutional (837I)
  - **Implementation Files**:
    - Single: `/app/backend/server.py` lines 2226-2265
    - Bulk: `/app/backend/server.py` lines 2269-2338
  - **Real Implementation Steps**:
    1. Register as Electronic Data Interchange (EDI) submitter
    2. Obtain trading partner agreement
    3. Implement EDI 837 claim formatting
    4. Set up secure file transfer (SFTP/HTTPS)
    5. Implement claim status tracking
    6. Handle rejections and resubmissions

### 3. **Ohio Medicaid EVV Submission**
- **Status**: ⚠️ MOCK AGGREGATOR FOR TESTING
- **Endpoints**:
  - `POST /api/evv/submit/individuals`
  - `POST /api/evv/submit/dcw`
  - `POST /api/evv/submit/visits`
- **Current Behavior**:
  - Uses mock aggregator in `/app/backend/evv_submission.py`
  - Validates data format
  - Generates mock transaction IDs
  - Simulates acknowledgments
- **What's Needed for Production**:
  - **Ohio EVV Aggregator Access**:
    - Register with Ohio Department of Medicaid
    - Obtain EVV vendor certification
    - Get aggregator credentials
  - **Business Entity Registration**:
    - Register business entity with Ohio EVV system
    - Obtain Business Entity ID
    - Configure in app: Settings > EVV Management > Configuration
  - **API Endpoint**: Replace mock aggregator URL with real Ohio EVV API
  - **Documentation**:
    - Ohio EVV Portal: https://evv.medicaid.ohio.gov
    - Technical specifications available from Ohio Department of Medicaid
  - **Implementation File**: `/app/backend/evv_submission.py`
  - **Real Implementation Steps**:
    1. Complete EVV vendor certification process
    2. Obtain production API endpoint and credentials
    3. Replace `OhioEVVAggregatorMock` with real API client
    4. Implement proper authentication
    5. Handle transaction tracking and status queries
    6. Implement error handling and resubmission logic

---

## 📋 REQUIRED CREDENTIALS SUMMARY

### Production Checklist

**Stripe (Payment Processing)**
- [ ] Live Stripe API Key
- [ ] Live Stripe Webhook Secret
- [ ] Webhook endpoint configured

**Sandata (Payroll/Billing)**
- [ ] Sandata account created
- [ ] API Key obtained
- [ ] Auth Token obtained
- [ ] Base URL configured

**Ohio Medicaid Claims**
- [ ] Trading partner agreement signed
- [ ] Provider ID obtained
- [ ] MITS access credentials
- [ ] EDI submitter ID
- [ ] Secure file transfer setup

**Ohio EVV System**
- [ ] EVV vendor certification complete
- [ ] Business Entity registered
- [ ] EVV API credentials obtained
- [ ] Aggregator endpoint configured

---

## 🔧 CONFIGURATION FILES

### Backend Environment Variables (`/app/backend/.env`)
```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=timesheet_scanner

# Authentication
JWT_SECRET=your_secret_key_here
CORS_ORIGINS=*

# AI/OCR
EMERGENT_LLM_KEY=sk-emergent-...

# Sandata (MOCKED - Replace with real credentials)
SANDATA_API_URL=https://api.sandata.com/v1
SANDATA_API_KEY=mock_api_key_replace_later
SANDATA_AUTH_TOKEN=mock_auth_token_replace_later

# Stripe (Currently Test Mode)
STRIPE_API_KEY=sk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...

# Ohio Medicaid (Add for production)
OHIO_MEDICAID_PROVIDER_ID=your_provider_id
OHIO_MEDICAID_TRADING_PARTNER_ID=your_tp_id
OHIO_EVV_API_URL=https://evv-api.medicaid.ohio.gov
OHIO_EVV_API_KEY=your_evv_api_key
```

### Frontend Environment Variables (`/app/frontend/.env`)
```env
REACT_APP_BACKEND_URL=https://your-domain.com
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

---

## 🚀 DEPLOYMENT STEPS

### 1. Development/Testing (Current State)
- ✅ All features functional with mocked external APIs
- ✅ Stripe in test mode
- ✅ Can test complete workflows end-to-end

### 2. Staging Environment
- Configure Stripe test mode webhook
- Test complete user flows
- Verify multi-tenancy data isolation
- Test subscription upgrades

### 3. Production Deployment
1. **Update Stripe to Live Mode**:
   - Replace test keys with live keys
   - Configure production webhook
   - Test payment flows with small amounts

2. **Sandata Integration** (if needed):
   - Obtain production credentials
   - Replace mock implementation
   - Test with small batch first
   - Monitor submission success rates

3. **Ohio Medicaid Claims** (if needed):
   - Complete trading partner agreement
   - Set up EDI formatting
   - Test with test claims
   - Go live after approval

4. **Ohio EVV System** (if needed):
   - Complete vendor certification
   - Register business entities
   - Replace mock aggregator
   - Test with sample data
   - Go live after approval

---

## 📞 SUPPORT CONTACTS

### Stripe
- Dashboard: https://dashboard.stripe.com
- Support: https://support.stripe.com

### Sandata
- Website: https://www.sandata.com
- Support: support@sandata.com

### Ohio Medicaid
- Provider Portal: https://medicaid.ohio.gov
- EVV Support: evv@medicaid.ohio.gov
- Claims Support: (800) 686-1516

---

## ⚠️ IMPORTANT NOTES

1. **Never commit real credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Test thoroughly in staging before production deployment**
4. **Keep backup of configuration before making changes**
5. **Monitor logs for errors after going live**
6. **Have rollback plan ready**
7. **Document any customizations made to mocked implementations**

---

## 🛠️ CURRENT TEST DATA

The application includes test accounts and data for development:
- Test organizations with sample patients, employees, timesheets
- Mock transaction IDs for EVV submissions
- Sample claims data
- Test Stripe checkout flows

**To reset test data**: Run `/app/backend/clear_test_data.py`

---

Last Updated: 2025-11-07
Version: 1.0
