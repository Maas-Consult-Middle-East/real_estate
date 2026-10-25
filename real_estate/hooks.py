from real_estate.compat import get_desk_route

app_name = "real_estate"
app_title = "Real Estate"
app_publisher = "Real Estate Module"
app_description = "Comprehensive Real Estate and Property Management for ERPNext"
app_email = "support@example.com"
app_license = "MIT"
app_version = "1.0.0"

# ─── Required Apps ────────────────────────────────────────────────────────────
required_apps = ["erpnext"]

# ─── Module Def ───────────────────────────────────────────────────────────────
# modules defined in modules.txt

# ─── Website Route Rules ──────────────────────────────────────────────────────
website_route_rules = [
    {"from_route": "/tenant-portal/<path:subpath>", "to_route": "tenant-portal"},
    {"from_route": "/tenant-portal", "to_route": "tenant-portal"},
]

# ─── Scheduled Tasks ──────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "real_estate.tasks.rent_billing.run_daily_billing",
        "real_estate.tasks.lease_alerts.run_lease_expiry_alerts",
        "real_estate.tasks.document_alerts.run_document_expiry_alerts",
        "real_estate.tasks.rent_billing.apply_late_fees",
        "real_estate.tasks.rent_billing.send_payment_reminders",
    ],
    "weekly": [
        "real_estate.tasks.ai_maintenance.run_predictive_maintenance",
    ],
    "monthly": [
        "real_estate.tasks.owner_statements.generate_owner_statements",
    ],
}

# ─── DocType Events ───────────────────────────────────────────────────────────
# Controller class methods (on_submit, on_cancel, validate, etc.) are called
# automatically by Frappe. doc_events is only for cross-app hooks.
doc_events = {}

# ─── Custom Fields on ERPNext Customer (Tenant extension) ─────────────────────
custom_fields = {
    "Customer": [
        {
            "fieldname": "tenant_details_section",
            "fieldtype": "Section Break",
            "label": "Tenant Details",
            "insert_after": "customer_details",
            "collapsible": 1,
        },
        {
            "fieldname": "id_type",
            "fieldtype": "Select",
            "label": "ID Type",
            "options": "National ID\nPassport\nIqama",
            "insert_after": "tenant_details_section",
        },
        {
            "fieldname": "id_number",
            "fieldtype": "Data",
            "label": "ID Number",
            "insert_after": "id_type",
        },
        {
            "fieldname": "id_expiry",
            "fieldtype": "Date",
            "label": "ID Expiry Date",
            "insert_after": "id_number",
        },
        {
            "fieldname": "tenant_col_break",
            "fieldtype": "Column Break",
            "insert_after": "id_expiry",
        },
        {
            "fieldname": "nationality",
            "fieldtype": "Data",
            "label": "Nationality",
            "insert_after": "tenant_col_break",
        },
        {
            "fieldname": "employer",
            "fieldtype": "Data",
            "label": "Employer",
            "insert_after": "nationality",
        },
        {
            "fieldname": "monthly_income",
            "fieldtype": "Currency",
            "label": "Monthly Income",
            "insert_after": "employer",
        },
        {
            "fieldname": "emergency_section",
            "fieldtype": "Section Break",
            "label": "Emergency Contact",
            "insert_after": "monthly_income",
            "collapsible": 1,
        },
        {
            "fieldname": "emergency_contact_name",
            "fieldtype": "Data",
            "label": "Emergency Contact Name",
            "insert_after": "emergency_section",
        },
        {
            "fieldname": "emergency_contact_phone",
            "fieldtype": "Phone",
            "label": "Emergency Contact Phone",
            "insert_after": "emergency_contact_name",
        },
        {
            "fieldname": "kyc_section",
            "fieldtype": "Section Break",
            "label": "KYC & Credit",
            "insert_after": "emergency_contact_phone",
            "collapsible": 1,
        },
        {
            "fieldname": "kyc_status",
            "fieldtype": "Select",
            "label": "KYC Status",
            "options": "Pending\nVerified\nRejected",
            "default": "Pending",
            "insert_after": "kyc_section",
        },
        {
            "fieldname": "credit_score",
            "fieldtype": "Int",
            "label": "Credit Score",
            "insert_after": "kyc_status",
        },
        {
            "fieldname": "blacklist_flag",
            "fieldtype": "Check",
            "label": "Blacklisted",
            "insert_after": "credit_score",
        },
        {
            "fieldname": "blacklist_reason",
            "fieldtype": "Small Text",
            "label": "Blacklist Reason",
            "insert_after": "blacklist_flag",
            "depends_on": "eval:doc.blacklist_flag == 1",
        },
    ],
}

# ─── Fixtures ─────────────────────────────────────────────────────────────────
# Roles and Workspace created programmatically in setup/install.py after_migrate.
fixtures = [
    {
        "dt": "Module Def",
        "filters": [["name", "=", "Real Estate"]],
    },
    {
        "dt": "Print Format",
        "filters": [["module", "=", "Real Estate"]],
    },
]

# ─── Permission Rules ─────────────────────────────────────────────────────────
# Defined via DocType JSON permission tables

# ─── Jinja Whitelisted Methods ────────────────────────────────────────────────
jinja = {
    "methods": [
        "real_estate.utils.jinja_helpers.get_qr_code_url",
    ],
}

# ─── Override Whitelisted Methods ─────────────────────────────────────────────
override_whitelisted_methods = {}

# ─── After Migrate ────────────────────────────────────────────────────────────
after_migrate = ["real_estate.setup.install.after_migrate"]

# Run the same idempotent setup for fresh installs and upgrades.
before_install = "real_estate.compat.validate_versions"
before_migrate = "real_estate.compat.validate_versions"
after_install = "real_estate.setup.install.after_migrate"

app_home = get_desk_route()
add_to_apps_screen = [{
    "name": app_name,
    "title": app_title,
    "logo": "/assets/real_estate/images/real-estate.svg",
    "route": app_home,
}]
