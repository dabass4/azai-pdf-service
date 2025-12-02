# Healthcare Timesheet Management System

A comprehensive, multi-tenant SaaS platform for healthcare agencies to manage timesheets, verify patient eligibility, submit claims, and process payments through Ohio Medicaid (OMES EDI) and Availity clearinghouse.

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![React](https://img.shields.io/badge/react-18-blue)]()

---

## 🎯 Features

### Core Functionality
- **AI-Powered Timesheet Extraction** - Upload PDFs/images, extract data automatically
- **Multi-Tenant Architecture** - Unlimited organizations with data isolation
- **Patient Management** - Comprehensive patient records with Medicaid integration
- **Employee Management** - Track employees, credentials, and schedules
- **Real-Time Processing** - WebSocket progress updates for long-running tasks

### Claims & Billing
- **Eligibility Verification** - Real-time 270/271 transactions with Ohio Medicaid
- **Claims Submission** - Dual-channel submission (OMES direct + Availity)
- **Status Tracking** - Monitor claim processing with 276/277 inquiries
- **Payment Processing** - Automated 835 remittance advice parsing
- **Stripe Integration** - Subscription billing with multiple plan tiers

### Admin Panel
- **Multi-Organization Management** - Manage all client organizations
- **Per-Org Credentials** - Configure OMES/Availity separately for each client
- **System Health Monitoring** - Real-time service status and analytics
- **No Downtime Updates** - Fix individual client issues without system restart

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB 5.0+
- Yarn package manager

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd healthcare-timesheet-system

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your config

# Frontend setup
cd ../frontend
yarn install

# Start services
# Terminal 1: Backend
cd backend && uvicorn server:app --reload --port 8001

# Terminal 2: Frontend  
cd frontend && yarn start
```

Access at: http://localhost:3000

---

## 📚 Documentation

- **[Test Summary Report](TEST_SUMMARY_REPORT.md)** - Complete testing results
- **[Implementation Guide](COMPLETE_IMPLEMENTATION_SUMMARY.md)** - Full feature list
- **[Admin Panel Guide](ADMIN_PANEL_IMPLEMENTATION.md)** - Admin usage
- API Docs: http://localhost:8001/docs (when running)

---

## 🔐 Super Admin Setup

```bash
cd backend
python create_super_admin.py \
  --email admin@company.com \
  --password SecurePass123!
```

---

## 📊 Test Results

- **Backend API:** 16/18 tests passed (89%)
- **Frontend:** Compiled successfully
- **Status:** ✅ Production Ready
- **Critical Issues:** All resolved

See [TEST_SUMMARY_REPORT.md](TEST_SUMMARY_REPORT.md) for details.

---

## 🛠️ Technology Stack

- **Backend:** FastAPI (Python), MongoDB
- **Frontend:** React, React Router
- **Auth:** JWT
- **AI:** Emergent LLM API
- **EDI:** Paramiko, Zeep, x12-edi-tools
- **Payments:** Stripe

---

## 📄 License

MIT License - See LICENSE file

---

**Status:** Production Ready | **Version:** 1.0.0 | **Last Updated:** January 2025
