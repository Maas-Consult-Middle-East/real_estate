"""Post-migrate setup tasks."""
import frappe


def after_migrate():
    _create_roles()
    _create_property_item()
    _create_tenant_custom_fields()
    _create_workspace()


def _create_roles():
    for role in ["Property Manager", "Real Estate Agent", "Tenant", "Property Owner"]:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role}).insert(ignore_permissions=True)
    frappe.db.commit()


def _create_tenant_custom_fields():
    """Create tenant KYC/identity fields on the Customer DocType."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    custom_fields = {
        "Customer": [
            {
                "fieldname": "tenant_details_section",
                "fieldtype": "Section Break",
                "label": "Tenant Details",
                "insert_after": "customer_details",
                "collapsible": 1,
            },
            {"fieldname": "id_type", "fieldtype": "Select", "label": "ID Type",
             "options": "National ID\nPassport\nIqama", "insert_after": "tenant_details_section"},
            {"fieldname": "id_number", "fieldtype": "Data", "label": "ID Number", "insert_after": "id_type"},
            {"fieldname": "id_expiry", "fieldtype": "Date", "label": "ID Expiry Date", "insert_after": "id_number"},
            {"fieldname": "tenant_col_break", "fieldtype": "Column Break", "insert_after": "id_expiry"},
            {"fieldname": "nationality", "fieldtype": "Data", "label": "Nationality", "insert_after": "tenant_col_break"},
            {"fieldname": "employer", "fieldtype": "Data", "label": "Employer", "insert_after": "nationality"},
            {"fieldname": "monthly_income", "fieldtype": "Currency", "label": "Monthly Income", "insert_after": "employer"},
            {
                "fieldname": "emergency_section",
                "fieldtype": "Section Break",
                "label": "Emergency Contact",
                "insert_after": "monthly_income",
                "collapsible": 1,
            },
            {"fieldname": "emergency_contact_name", "fieldtype": "Data", "label": "Emergency Contact Name",
             "insert_after": "emergency_section"},
            {"fieldname": "emergency_contact_phone", "fieldtype": "Phone", "label": "Emergency Contact Phone",
             "insert_after": "emergency_contact_name"},
            {
                "fieldname": "kyc_section",
                "fieldtype": "Section Break",
                "label": "KYC & Credit",
                "insert_after": "emergency_contact_phone",
                "collapsible": 1,
            },
            {"fieldname": "kyc_status", "fieldtype": "Select", "label": "KYC Status",
             "options": "Pending\nVerified\nRejected", "default": "Pending", "insert_after": "kyc_section"},
            {"fieldname": "credit_score", "fieldtype": "Int", "label": "Credit Score", "insert_after": "kyc_status"},
            {"fieldname": "blacklist_flag", "fieldtype": "Check", "label": "Blacklisted", "insert_after": "credit_score"},
            {"fieldname": "blacklist_reason", "fieldtype": "Small Text", "label": "Blacklist Reason",
             "insert_after": "blacklist_flag", "depends_on": "eval:doc.blacklist_flag == 1"},
        ]
    }
    try:
        create_custom_fields(custom_fields, ignore_validate=True, update=False)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Tenant custom fields setup failed: {e}", "Real Estate Setup")


def _create_workspace():
    """Create navigation supported by both v15 and v16; preserve user changes."""
    import json

    if frappe.db.exists("Workspace", "Real Estate"):
        return
    groups = {
        "Properties": ["Property", "Property Unit", "Property Listing", "Agent"],
        "Leasing": ["Lease Agreement", "Rent Invoice", "Security Deposit Ledger",
                    "Visitor Lead Inquiry", "Sale Agreement"],
        "Operations": ["Maintenance Request", "Property Inspection", "Owner Statement",
                       "Utility Rate Card"],
    }
    ws = frappe.new_doc("Workspace")
    ws.label = ws.title = "Real Estate"
    ws.module = "Real Estate"
    ws.icon = "home"
    ws.public = 1
    ws.content = json.dumps([
        {"id": f"re-{index}", "type": "card", "data": {"card_name": title, "col": 4}}
        for index, title in enumerate(groups)
    ])
    for title, doctypes in groups.items():
        ws.append("links", {"type": "Card Break", "label": title})
        for doctype in doctypes:
            ws.append("links", {
                "type": "Link", "label": doctype, "link_to": doctype,
                "link_type": "DocType",
            })
        if title == "Operations":
            ws.append("links", {
                "type": "Link", "label": "Real Estate Dashboard",
                "link_to": "real-estate-dashboard", "link_type": "Page",
            })
    ws.insert(ignore_permissions=True)


def _create_property_item():
    """Ensure the standard items used by billing exist."""
    for item_code, item_name in [
        ("Monthly Rent", "Monthly Rent"),
        ("Property Sale Milestone", "Property Sale Milestone"),
        ("Management Fee", "Property Management Fee"),
    ]:
        if frappe.db.exists("Item", item_code):
            continue
        try:
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = item_name
            item.item_group = "Services"
            item.is_stock_item = 0
            item.flags.ignore_permissions = True
            item.insert()
        except Exception:
            pass
    frappe.db.commit()
