# Brightloop Software — Subscription Management System
> **Odoo Hackathon Complete Production Deliverable**  
> A centralized, production-quality Subscription Management System automating customer onboarding, role-based workflows, dynamic product variants, subscription state machines, recurring billing runs, tax calculations, promotional discounts, invoice PDF generation, partial payments, and executive revenue analytics.

---

## 🌟 Table of Contents
1. [Project Overview & Key Capabilities](#-project-overview--key-capabilities)
2. [Technology Stack](#-technology-stack)
3. [Architecture Overview](#-architecture-overview)
4. [Demo Login Credentials](#-demo-login-credentials)
5. [Local Setup & Installation](#-local-setup--installation)
6. [Database Schema & Migrations](#-database-schema--migrations)
7. [Automated Testing Suite](#-automated-testing-suite)
8. [Hackathon Demo Workflow (8 Live Scenarios)](#-hackathon-demo-workflow-8-live-scenarios)
9. [API Architecture & Documentation](#-api-architecture--documentation)

---

## 🚀 Project Overview & Key Capabilities

Brightloop Software transitioned from spreadsheets and manual invoicing to this centralized subscription engine.

- **Role-Based Access Control**: Strict segregation between **ADMIN** (full system governance), **STAFF** (day-to-day sales, quotations, invoices, payments), and **CUSTOMER** (strict data isolation to their own subscriptions, invoices, and payment receipts).
- **Product & Variant Pricing**: Base product catalog with dynamic brand variants (e.g. *Odoo Enterprise Edition* +₹560 surcharge).
- **Flexible Plans**: Daily, Weekly, Monthly, and Yearly billing frequencies with automated cycle calculations and policy toggles (pause, renewal, early closure).
- **Subscription Lifecycle State Machine**: Enforces strict transitions `DRAFT` ➔ `QUOTATION` ➔ `CONFIRMED` ➔ `ACTIVE` ➔ `PAUSED` ➔ `CLOSED` ➔ `RENEWED` with immutable audit trail.
- **Sales Quotations**: Quotation drafting, tax/discount calculation, validity checks, and conversion into active subscriptions.
- **Automated Billing Engine & Duplicate Prevention**: Database uniqueness constraints (`subscription_id` + `billing_period_start` + `billing_period_end`) guarantee that eligible billing periods are never skipped and never double-billed.
- **Real-Time Revenue Analytics**: Non-hardcoded, live SQL calculations for **MRR** (Monthly Recurring Revenue), **ARR** (Annual Recurring Revenue), recognized cash collections, and outstanding receivables.
- **Automated Invoices & PDF Generation**: Instant generation of professional PDF invoices via ReportLab.
- **Payment Reconciliation**: Support for partial payments, full settlement, overpayment guardrails, and auditable payment reversals.
- **Customer Self-Service Hub**: Dedicated customer portal with subscription renewal, invoice downloads, and balance tracking.

---

## 🛠 Technology Stack

### Backend
- **Framework**: Python 3.14+ FastAPI (Async ASGI)
- **Database ORM**: SQLAlchemy 2.0 with connection pooling
- **Databases Supported**: PostgreSQL & SQLite (auto-fallback for seamless local testing)
- **Authentication**: JWT (JSON Web Tokens) with HS256 + direct `bcrypt` password hashing (8+ chars, upper, lower, numbers, special)
- **Background Jobs**: APScheduler running hourly recurring billing & overdue checks
- **PDF Generation**: ReportLab
- **Testing**: PyTest with in-memory SQLite isolation

### Frontend
- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS + Shadcn design tokens + Lucide React Icons
- **Data Visualization**: Recharts (Monthly Revenue BarChart, Subscription Trajectory AreaChart, Status & Payment Donut Charts, Product Horizontal BarChart)
- **Routing**: React Router DOM (protected routes, role-based navigation)

---

## 🔐 Demo Login Credentials

The system is pre-seeded with realistic enterprise data. You can log in using the **1-Click Quick Demo Login** buttons on the login screen or enter:

| Role | Email Address | Password | Permissions |
|------|---------------|----------|-------------|
| **Admin** | `admin@brightloop.com` | `Admin@123!` | Full system governance, products, plans, taxes, discounts, analytics |
| **Staff** | `staff1@brightloop.com` | `Staff@123!` | Quotations, subscriptions, invoices, payment recording, reversals |
| **Staff 2** | `staff2@brightloop.com` | `Staff@123!` | Secondary sales & operations staff |
| **Customer** | `customer1@brightloop.com` | `Customer@123!` | Self-service portal (Ananya Verma - Acme Technologies) |
| **Customer** | `customer2@brightloop.com` | `Customer@123!` | Self-service portal (Vikram Singh - Zenith Logistics) |

---

## 💻 Local Setup & Installation

### Prerequisites
- Python 3.10+ (Python 3.14 verified)
- Node.js 18+ & npm (Node v24 verified)

### 1. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
pip install email-validator

# Run seed script (creates tables and 100+ realistic records)
python app/seed.py

# Start backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API will be live at `http://127.0.0.1:8000`  
Interactive Swagger documentation: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev -- --host 127.0.0.1 --port 5173
```
Frontend application will be live at `http://127.0.0.1:5173`

---

## 🗄 Database Schema & Migrations

The relational schema consists of 19 normalized tables:
- `users`: Core identity, password hash, role (`admin`, `staff`, `customer`), last login
- `customers`: Company profile, address, GSTIN, contacts
- `products`: Software products, catalog classification, base sales and cost prices
- `product_variants`: Brand-specific surcharges (e.g. Odoo brand +₹560)
- `subscription_plans`: Billing frequencies (Daily, Weekly, Monthly, Yearly), constraints, early closure toggles
- `quotations`: Sales quotes, customer link, validity date, subtotal, tax, discount, total
- `quotation_lines`: Line items linking products, variants, quantities, and taxes
- `subscriptions`: Active subscriptions, number, frequency, expiry date, payment terms, next invoice date
- `subscription_lines`: Line items for subscriptions
- `subscription_status_history`: Immutable audit trail of every lifecycle status transition
- `invoices`: Invoice number, billing period start/end, due date, subtotal, tax, discount, total, paid, due
- `invoice_lines`: Line items replicated with unit price and tax calculations
- `taxes`: Tax rules (GST 18%, SGST 9%, CGST 9%)
- `discounts`: Promotional discount rules (percentage & fixed, minimum spend, expiry date, redemption limits)
- `discount_usage`: Customer-level discount consumption tracking
- `payments`: Payment number, invoice link, customer, payment method, transaction reference, reversal flag
- `notifications`: User notifications for registration, invoices, overdue notices, and renewals
- `audit_logs`: System action audit logs
- `settings`: Key-value application configurations

---

## 🧪 Automated Testing Suite

To run the automated test suite covering all 16 core business rules:
```bash
cd backend
python -m pytest tests/ -v
```

### Verified Test Cases:
1. `test_password_policy`: Validates 8+ length, uppercase, lowercase, numbers, and special characters.
2. `test_hash_and_jwt`: Validates bcrypt hashing and JWT token creation/decoding.
3. `test_tax_calculations`: Verifies percentage and fixed tax computations with exact Decimal rounding.
4. `test_discount_eligibility`: Tests minimum spend thresholds and usage limits.
5. `test_subscription_lifecycle`: Validates state machine (`DRAFT` ➔ `CONFIRMED` ➔ `ACTIVE` ➔ `PAUSED` ➔ `CLOSED`).
6. `test_invoice_generation_and_duplicate_prevention`: Verifies unique billing period constraint (409 Conflict on duplicate run).
7. `test_payments_and_reversals`: Verifies partial payments, overpayment guardrails, full settlement, and auditable reversals.
8. `test_mrr_calculation`: Validates accurate monthly revenue normalization across Daily, Weekly, Monthly, and Yearly subscriptions.

---

## 🎯 Hackathon Demo Workflow (8 Live Scenarios)

Demonstrate the system live to judges following this exact workflow:

### Scenario 1: New Customer Registration & Subscription Creation
1. Go to `http://127.0.0.1:5173/register`.
2. Register a new company (e.g., *Zenith Robotics*).
3. Log in as Customer and navigate to the catalog to choose a plan.
4. Submit a new subscription request.

### Scenario 2: Active Monthly Subscription Generates Invoice
1. Log in as **Admin** (`admin@brightloop.com` / `Admin@123!`).
2. Navigate to **Subscriptions**, find an active subscription.
3. Click the **Bill** button (or click **Run Billing Job** in the navbar).
4. Navigate to **Invoices** to view the newly created invoice with unique number and due date based on payment terms (Net 30).

### Scenario 3: Customer Receives a Discount & Tax Calculation
1. Navigate to **Quotations** ➔ Click **New Quotation**.
2. Select a customer, product, and apply a promotional discount (e.g., *Startup Booster 15%*) and tax (*GST 18%*).
3. Inspect how line item totals and taxes calculate dynamically.
4. Click **Convert to Sub** to confirm the quotation into a live subscription.

### Scenario 4: Partial Payment & Overpayment Prevention
1. Open **Invoices** and select an invoice with a due balance of ₹5,000.
2. Click **Record Payment**.
3. Attempt to enter ₹6,000 ➔ System blocks the overpayment.
4. Enter ₹2,000 (partial payment) via UPI ➔ Invoice status transitions to **Partially Paid** and balance due updates to ₹3,000.

### Scenario 5: Invoice Becomes Overdue Detection
1. In the **Invoices** table, observe overdue invoices flagged with a red badge.
2. Click **Run Billing Job** in the top navbar ➔ Background scheduler inspects past-due invoices and marks their status as **Overdue**, generating overdue notifications.

### Scenario 6: Subscription Renewal
1. Navigate to **Subscriptions**, open a subscription near expiration.
2. Click **Inspect** ➔ Click **Renew Subscription**.
3. Expiry date automatically increments by the plan cycle (e.g. +30 days for monthly or +1 year for annual).
4. Renewal count increments, and an audit trail entry is logged.

### Scenario 7: Early Closure Governance
1. Open a subscription whose plan has `allow_early_closure: false`.
2. Attempt early closure ➔ System blocks unauthorized cancellation with an explanatory error.
3. Open a subscription with permission ➔ Click **Close Early** ➔ Status updates to **Closed**.

### Scenario 8: Executive Revenue & MRR Review
1. Open the **Overview** dashboard.
2. Review real-time KPIs: Total Revenue Collected, MRR, ARR, and Outstanding Receivables.
3. Review interactive Recharts: Cash Collection vs Invoiced, Subscription Trajectory, and Revenue by Product.

---

## 📖 API Architecture & Documentation

FastAPI provides interactive OpenAPI/Swagger documentation at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Key Endpoint Groups:
- `/api/v1/auth`: `/login`, `/register`, `/me`, `/forgot-password`, `/reset-password`
- `/api/v1/customers`: Full customer CRUD with role isolation
- `/api/v1/products`: Product catalog and variant management (`/variants`)
- `/api/v1/plans`: Plan configuration with frequency and policy controls
- `/api/v1/quotations`: Quotation generation and conversion (`/{id}/confirm`)
- `/api/v1/subscriptions`: Lifecycle endpoints (`/confirm`, `/activate`, `/pause`, `/resume`, `/close`, `/renew`)
- `/api/v1/invoices`: Invoice listing, generation (`/from-subscription/{id}`), PDF export (`/{id}/pdf`), background run (`/run-billing-job`)
- `/api/v1/payments`: Payment recording and reversals (`/{id}/reverse`)
- `/api/v1/taxes`: Tax rule configuration
- `/api/v1/discounts`: Promotional discount rules and eligibility evaluation (`/evaluate/{id}`)
- `/api/v1/dashboard`: Live DB aggregated analytics (`/analytics`)
- `/api/v1/notifications`: User notifications and unread badges
