# Real Estate — Comprehensive Property Management for ERPNext

A Frappe v15/v16 app for end-to-end real estate and property portfolio management, fully integrated with ERPNext. Covers the complete lifecycle from property onboarding and tenant leasing through automated billing, maintenance tracking, sales, and AI-powered portfolio analytics.


<img width="862" height="602" alt="Screenshot from 2026-06-17 03-48-24" src="https://github.com/user-attachments/assets/f4739a5d-083d-46e3-8598-da12d75b9fa9" />

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Roles and Permissions](#roles-and-permissions)
6. [Module Guide](#module-guide)
   * [Properties](#properties)
   * [Leasing](#leasing)
   * [Billing](#billing)
   * [Maintenance](#maintenance)
   * [Sales](#sales)
   * [Owner Statements](#owner-statements)
   * [Listings and Inquiries](#listings-and-inquiries)
7. [AI Features](#ai-features)
8. [Tenant Portal](#tenant-portal)
9. [Portfolio Dashboard](#portfolio-dashboard)
10. [Scheduled Jobs](#scheduled-jobs)
11. [ERPNext Integration](#erpnext-integration)
12. [API Reference](#api-reference)
13. [DocType Reference](#doctype-reference)
14. [Development](#development)

---

## Features

**Property Management**
* Property and Unit master with geo-coordinates, amenities, images, and document vault
* Unit status lifecycle: Available → Occupied → Under Maintenance → Vacant

**Leasing**
* Submittable Lease Agreements with automatic unit status update
* One-click lease renewal wizard with configurable rent escalation
* AI-generated tenancy clause drafting
* Security deposit ledger with automatic Journal Entry creation

**Automated Billing**
* Daily billing engine creates Rent Invoices on the configured due day
* Utility billing with slab-based rate cards and IoT meter reading API
* Late fee application after grace period, with automated email reminders
* VAT calculation and multi-currency support
* ERPNext Sales Invoice created automatically on Rent Invoice submission

**Maintenance**
* Full maintenance request lifecycle with vendor assignment
* Inspection checklists auto-populated by inspection type (Move-In, Move-Out, Periodic, Pre-Sale)
* AI-powered predictive maintenance analysis runs weekly and creates draft requests

**Sales**
* Sale Agreement with milestone-based payment schedule
* Agent commission tracking and management
* Milestone Sales Invoices generated from ERPNext

**Analytics and Reporting**
* Portfolio Dashboard with KPI cards, occupancy donut chart, and 6-month revenue bar chart
* Owner Statement with AI-generated narrative summary
* Natural language portfolio queries via AI chat widget

**Tenant Self-Service Portal**
* Accessible at `/tenant-portal` for any logged-in tenant
* View leases, download invoices as PDF, submit and track maintenance requests

**AI (Claude API)**
* Rent valuation suggestions with market comparables
* Lease clause generator
* Predictive maintenance scheduling
* Natural language portfolio analytics
* Owner statement narrative

---

## Requirements

Use matching Frappe and ERPNext major versions on the same bench:

| Frappe | ERPNext | Python | Node.js |
| --- | --- | --- | --- |
| v15 | v15 | 3.10+ | 18+ |
| v16 | v16 | 3.14+ | 24+ |

The same app branch supports both versions. Installation and migration reject
unsupported or mixed major versions. Follow the runtime requirements of the
specific framework release you install; see the
[Frappe v16 migration guide](https://github.com/frappe/frappe/wiki/Migrating-to-version-16).

* `anthropic` Python package (required only for AI features)

---

## Installation

### Step 1 — Get the app

```bash
cd /path/to/frappe-bench
bench get-app real_estate https://github.com/Zaryab03/real_estate.git
```

### Step 2 — Install the Python AI client (optional but recommended)

```bash
./env/bin/pip install anthropic
```

### Step 3 — Install on your site

```bash
bench --site yoursite.com install-app real_estate
```

### Step 4 — Run migrations

```bash
bench --site yoursite.com migrate
```

Installation and migration register the roles, ensure billing items and tenant custom fields exist, and create the Real Estate workspace if missing. Existing workspaces are preserved. When upgrading from v15 to v16, upgrade Frappe and ERPNext together, then run migration and rebuild assets.

### Step 5 — Build frontend assets

```bash
bench build --app real_estate
```

### Step 6 — Restart the bench

```bash
# Production (supervisor)
sudo supervisorctl restart all

# Development
bench start
```

---

## Configuration

### Claude AI Key

Open `sites/yoursite.com/site_config.json` and add:

```json
{
  "real_estate_claude_api_key": "sk-ant-..."
}
```

Without this key the app works fully; AI feature buttons will show a friendly message asking to configure the key. Never commit this value to version control.

### Utility Meter Reading API

IoT devices and smart meters can push readings via the REST API:

```http
POST /api/method/real_estate.utils.meter_reading.receive_meter_reading
Authorization: token <api_key>:<api_secret>
Content-Type: application/json

{
  "unit_name": "PROP001-U001",
  "utility_type": "Electricity",
  "reading": 12345.6,
  "reading_date": "2025-01-15"
}
```

The system finds the previous reading, calculates consumption, applies the matching slab rate from the Utility Rate Card, and updates the current open Rent Invoice automatically.

---

## Roles and Permissions

| Role | Desk Access | Scope |
|---|---|---|
| Property Manager | Yes | Full access to all doctypes, dashboards, settings |
| Real Estate Agent | Yes | Properties, units, listings, inquiries, lease creation |
| Property Owner | Yes | Own properties and owner statements (read-only) |
| Tenant | No | Self-service portal only (web-facing) |

ERPNext's built-in Accountant role retains read access to invoices, statements, and journal entries.

---

## Module Guide

### Properties

**Property** is the top-level record representing a building, villa, or land parcel.

Fields to fill in:
* Property Name and Property Code (used for auto-naming units)
* Property Type: Residential, Commercial, Industrial, Mixed-Use, Land
* Owner: link to a Customer or Supplier record
* Address and Geo Coordinates (Geolocation field — paste lat,lng)
* Amenities (Table MultiSelect from a predefined list)
* Status: Available, Occupied, Under Maintenance, For Sale

Use the Documents child table to store contracts, title deeds, and NOCs with expiry dates. The daily scheduler will email Property Managers when any document is approaching its expiry.

**Property Unit** represents an individual rentable space inside a property.

Fields to fill in:
* Property (links to the parent Property)
* Unit Number and Unit Type (Studio, 1BHK, 2BHK, Office, Shop, Warehouse)
* Floor Area and Floor Number
* Monthly Rent (suggested by AI — see AI Features)
* Status: Available, Occupied, Reserved, Under Maintenance

The unit status is managed automatically. When a Lease Agreement is submitted the unit moves to Occupied. When the lease is cancelled or expires it returns to Available.

---

### Leasing

**Lease Agreement** is the core transactional document for tenant leasing.

How to create a lease:
1. Open a Property Unit and click **New Lease** from the quick buttons in the top right.
2. The unit, property, and monthly rent are pre-filled.
3. Set the Tenant (link to an ERPNext Customer), Start Date, and End Date.
4. Configure the Payment Due Day (1–28), Grace Period, and Late Fee Percent.
5. Optionally link an Agent and set the commission.
6. Click **Generate Clauses (AI)** to draft the standard tenancy clauses automatically.
7. Save, review, then Submit. The unit status changes to Occupied and a Security Deposit Ledger entry is created.

**Lease Renewal**

Click **Renew Lease** on a submitted Lease Agreement. A dialog asks for the new end date and whether to apply annual escalation. A new draft lease is created with the updated terms and the renewal is recorded in the Renewal History table.

**Lease Termination**

Click **Terminate Lease** on a submitted Lease Agreement. This cancels the agreement, marks the unit as Available, and initiates the security deposit refund workflow.

---

### Billing

**Rent Invoice** is created automatically by the daily scheduler on the configured Payment Due Day. It can also be created manually from the Lease Agreement form.

The invoice calculates:
* Base Rent (from the lease)
* Utility Charges (electricity, water, gas — from meter readings)
* Late Fee (applied after grace period)
* Discount (manual entry)
* VAT (configured percentage)
* Total Amount

When the invoice is submitted an ERPNext Sales Invoice is created and linked automatically.

**Utility Rate Cards**

Before using utility billing, create a Utility Rate Card for each utility type. Add slabs to define tiered pricing (e.g. first 100 units at 0.10 SAR, next 200 units at 0.15 SAR). Link the rate card to the Property Unit.

**Late Fees and Reminders**

The daily scheduler sends payment reminder emails at 3 days before due, on the due date, and 1 day after the grace period. After the grace period passes, a late fee is added and the invoice status moves to Overdue.

---

### Maintenance

**Maintenance Request** captures repair and service requests for any property unit.

How to raise a request:
1. From a Property Unit, click **New Maintenance Request**.
2. Set the Category (Plumbing, Electrical, HVAC, Civil, Cleaning, Other), Priority, and description.
3. Attach photos using the standard file attachment field.
4. Save — Property Managers are notified by email immediately. Emergency-priority requests also trigger a real-time browser notification.

The request moves through statuses: Open → Assigned → In Progress → Completed → Cancelled.

**Assign to Vendor**: Once a vendor is selected, click **Assign to Vendor** to record the vendor and expected completion date.

**Property Inspection**

Create an Inspection linked to a unit. Choose the Inspection Type:
* Move-In — documents the condition before a tenant moves in
* Move-Out — documents the condition when a tenant vacates
* Periodic — routine condition check
* Pre-Sale — condition assessment before listing for sale

The checklist is auto-populated with standard items for each inspection type. Rate each item and add remarks and photos.

---

### Sales

**Sale Agreement** records the sale of a property.

How to create a sale:
1. Open a Property and click **New Sale Agreement**.
2. Set the Buyer, Sale Price, and currency.
3. Add rows to the Payment Schedule table with milestone names, amounts, and due dates. The total must equal the Sale Price.
4. Optionally link an Agent and commission.
5. Submit when executed.

**Generate Milestone Invoices**: Click this button to create ERPNext Sales Invoices for all payment schedule milestones that are due today or earlier.

**Agent Management**

The Agent DocType stores agent profiles with commission rates. The Agent dashboard shows pending commission from all linked Lease and Sale Agreements. Use the **View Leases** and **View Sale Agreements** buttons on the Agent form to navigate to related records.

---

### Owner Statements

**Owner Statement** is a monthly financial summary for a property owner.

Statements are generated automatically each month by the scheduler for all active properties. You can also create one manually.

**Compute from Invoices**: Click this button to pull all paid Rent Invoices and completed Maintenance Requests for the statement period and populate the income and expense totals.

When submitted, the system:
1. Creates a Journal Entry crediting the owner's account
2. Generates a 2-paragraph AI narrative summarising portfolio performance for the month

The AI narrative appears in the **AI Summary** field and is included in the print output.

---

### Listings and Inquiries

**Property Listing** creates a public-facing record for an available unit. Set the listing price, highlights, and photos. The inquiry counter tracks how many visitors have expressed interest.

**Visitor Lead Inquiry** captures interest from prospective tenants or buyers submitted via the property listing page. On save:
* The parent listing's inquiry count increments
* A CRM Lead is created automatically in ERPNext

---

## AI Features

All AI features use Claude (`claude-sonnet-4-6`) via the Anthropic API. The API key must be set in `site_config.json` as `real_estate_claude_api_key`.

### Rent Valuation

On the Property Unit form, click **Suggest Rent (AI)**. A dialog appears with:
* Suggested minimum and maximum monthly rent
* Reasoning based on unit size, type, and property location
* Comparable units from the same property

### Lease Clause Generator

On the Lease Agreement form, click **Generate Clauses (AI)**. The AI drafts 10 standard clause categories:
* Payment terms, maintenance obligations, permitted use
* Subletting restrictions, alterations policy, entry rights
* Termination notice, renewal rights, dispute resolution, governing law

Clauses are saved to the AI Clauses field and included in the Lease Agreement print format.

### Predictive Maintenance

Every week the scheduler analyses units with at least 3 completed maintenance records. For each unit it predicts:
* Likely failure category
* Suggested inspection/service date
* Priority level and reasoning

A draft Maintenance Request is created for each prediction so a manager can review and schedule proactively.

### Natural Language Portfolio Analytics

The Portfolio Dashboard has an AI chat widget. Type any question about your portfolio in plain English:

> "How many units are currently vacant and what is the estimated monthly revenue loss?"
> "Which properties have the most overdue invoices this quarter?"
> "List tenants whose leases expire in the next 60 days."

The AI builds live context from your database (occupancy, rent collection, expiring leases, maintenance stats) before answering.

### Owner Statement Narrative

When an Owner Statement is submitted, the AI automatically writes a 2-paragraph narrative summarising the month's performance for that property, including occupancy highlights, income versus maintenance costs, and notable events.

---

## Tenant Portal

The tenant portal is a web page available at `yoursite.com/tenant-portal` for any logged-in user whose email matches a Customer marked as a tenant.

**What tenants can do:**
* View all active and past leases with key terms
* Download any rent invoice as a PDF
* See their outstanding balance
* Submit new maintenance requests with descriptions and photo attachments
* Track the status of existing maintenance requests

**Authentication**: Tenants log in using Frappe's standard login page. Guest users are redirected to login automatically. No Frappe desk access is given to the Tenant role.

---

## Portfolio Dashboard

Access the dashboard from the Frappe sidebar under Real Estate → Real Estate Dashboard, or directly at `/app/real-estate-dashboard` on v15 and `/desk/real-estate-dashboard` on v16.

The dashboard shows:
* **KPI Cards**: Total properties, occupied units, vacant units, monthly revenue collected, overdue invoices
* **Occupancy Donut Chart**: Visual breakdown of unit statuses (Frappe Charts)
* **6-Month Revenue Bar Chart**: Collected rent by month (Frappe Charts)
* **Expiring Leases Table**: Leases expiring in the next 90 days with colour-coded urgency badges
* **Maintenance Pipeline**: Open, In-Progress, and Completed request counts
* **AI Chat Widget**: Natural language queries answered live from your portfolio data

Click **Refresh** in the page header to reload all data.

---

## Scheduled Jobs

| Frequency | Job | Description |
|---|---|---|
| Daily | Rent Billing Engine | Creates Rent Invoices for leases due today |
| Daily | Late Fee Application | Marks overdue invoices and adds late fee after grace period |
| Daily | Payment Reminders | Sends email reminders at 3 days before, on, and after due date |
| Daily | Lease Expiry Alerts | Notifies at 60, 30, and 15 days before lease end; expires overdue leases |
| Daily | Document Expiry Alerts | Notifies when property or agent documents approach their expiry date |
| Weekly | AI Predictive Maintenance | Analyses maintenance history and creates draft requests for at-risk units |
| Monthly | Owner Statement Generation | Creates draft Owner Statements for all active properties |

Jobs run automatically via Frappe's background scheduler. No manual intervention is needed after initial setup.

---

## ERPNext Integration

| Real Estate Document | ERPNext Document Created |
|---|---|
| Rent Invoice (Submit) | Sales Invoice (Draft) |
| Security Deposit Received | Journal Entry (Liability Credit) |
| Security Deposit Refunded | Journal Entry (Liability Debit) |
| Owner Statement (Submit) | Journal Entry (Owner Payout) |
| Sale Agreement Milestones | Sales Invoice per milestone |
| Visitor Lead Inquiry | CRM Lead |

The app also creates three ERPNext Items on first migrate: Monthly Rent, Property Sale Milestone, and Management Fee. These are used as line items in the Sales Invoices.

**Customer Extension**: The app adds 14 custom fields to the ERPNext Customer DocType (under a collapsible Tenant Details section) for KYC and financial screening. No core patching is done — fields are created via Frappe's Custom Field mechanism and are fully removable.

---

## API Reference

All endpoints require Frappe API token authentication (`Authorization: token api_key:api_secret`).

### Meter Reading

```
POST /api/method/real_estate.utils.meter_reading.receive_meter_reading

Parameters:
  unit_name      (string, required) — Property Unit name
  utility_type   (string, required) — Electricity | Water | Gas | District Cooling
  reading        (float, required)  — Current meter reading value
  reading_date   (date, optional)   — Defaults to today
```

### Tenant Portal (authenticated web user)

```
GET  /api/method/real_estate.utils.portal_api.get_portal_data
POST /api/method/real_estate.utils.portal_api.submit_maintenance_request
GET  /api/method/real_estate.utils.portal_api.get_invoice_pdf
```

### Dashboard Data

```
GET /api/method/real_estate.utils.dashboard_data.get_dashboard_data
```

Returns KPIs, occupancy breakdown, monthly revenue, expiring leases, and maintenance stats as JSON.

---

## DocType Reference

### Main DocTypes

| DocType | Submittable | Description |
|---|---|---|
| Property | No | Building or land master |
| Property Unit | No | Individual rentable space |
| Lease Agreement | Yes | Tenant lease contract |
| Rent Invoice | Yes | Monthly billing document |
| Owner Statement | Yes | Monthly owner payout summary |
| Maintenance Request | No | Repair and service ticket |
| Property Inspection | No | Condition checklist |
| Property Listing | No | Public listing for vacant units |
| Visitor Lead Inquiry | No | Prospective tenant or buyer inquiry |
| Sale Agreement | Yes | Property sale contract |
| Agent | No | Agent or broker profile |
| Security Deposit Ledger | No | Deposit transaction record with JE |
| Utility Rate Card | No | Slab-based utility pricing |

### Child Tables

| Child Table | Parent DocType |
|---|---|
| Property Feature | Property |
| Property Image | Property |
| Property Document | Property, Property Unit, Lease Agreement, Agent |
| Utility Charge | Rent Invoice |
| Utility Rate Slab | Utility Rate Card |
| Inspection Checklist Item | Property Inspection |
| Lease Renewal History | Lease Agreement |
| Listing Highlight | Property Listing |
| Payment Schedule Item | Sale Agreement |

---

## Development

Run the site-independent compatibility regression suite inside either a v15 or
v16 bench (it checks the actual installed framework versions and controller imports):

```bash
./env/bin/python -m unittest real_estate.tests.test_compatibility -v
```

These checks do not replace testing installation, migration, and billing on a
disposable site before deploying an upgrade.

### Running tests

```bash
bench --site yoursite.com run-tests --app real_estate
```

### Watching for JS changes

```bash
bench watch
```

### Exporting fixtures after configuration changes

```bash
bench --site yoursite.com export-fixtures --app real_estate
```

### Adding the AI key for local development

Edit `sites/yoursite.com/site_config.json` and add `real_estate_claude_api_key`. The key is read at runtime via `frappe.conf.real_estate_claude_api_key` and is never stored in code.

### App structure

```
real_estate/
  real_estate/
    doctype/          Individual DocType folders (JSON + Python + JS)
    page/             Portfolio dashboard page
    print_format/     Rent Invoice and Lease Agreement PDF templates
    ai/               Claude API client and feature modules
    tasks/            Scheduled job modules
    utils/            Dashboard data, portal API, meter reading, Jinja helpers
    setup/            after_migrate installer (roles, items, custom fields)
  www/
    tenant-portal/    Web portal (index.html + index.py)
  hooks.py
  requirements.txt
```

---

## License

MIT
