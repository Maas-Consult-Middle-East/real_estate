"""Tenant portal backend — data handler for /tenant-portal."""
import frappe
from frappe import _
from frappe.utils import nowdate, get_url_to_form


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/tenant-portal"
        raise frappe.Redirect

    tenant = _get_tenant_customer()
    if not tenant:
        context.no_tenant = True
        context.message = _("Your account is not linked to a tenant profile. Contact your property manager.")
        return

    context.tenant = tenant
    context.leases = _get_active_leases(tenant)
    for lease in context.leases:
        lease.desk_url = get_url_to_form("Lease Agreement", lease.name)
    context.invoices = _get_invoices(tenant)
    context.maintenance_requests = _get_maintenance_requests(tenant)
    context.no_cache = 1


def _get_tenant_customer():
    return frappe.db.get_value("Customer", {"email_id": frappe.session.user})


def _get_active_leases(tenant):
    return frappe.get_all(
        "Lease Agreement",
        filters={"tenant": tenant, "lease_status": ("in", ["Active", "Renewed"]), "docstatus": 1},
        fields=["name", "property_unit", "lease_start_date", "lease_end_date",
                "monthly_rent", "lease_status", "payment_due_day"],
        order_by="lease_start_date desc",
        limit=5,
    )


def _get_invoices(tenant):
    return frappe.get_all(
        "Rent Invoice",
        filters={"tenant": tenant, "docstatus": 1},
        fields=["name", "billing_period_start", "billing_period_end",
                "total_amount", "status", "payment_date"],
        order_by="billing_period_start desc",
        limit=12,
    )


def _get_maintenance_requests(tenant):
    return frappe.get_all(
        "Maintenance Request",
        filters={"tenant": tenant},
        fields=["name", "category", "priority", "status", "reported_date", "completion_date"],
        order_by="reported_date desc",
        limit=10,
    )


# ─── API endpoints called by portal JS ────────────────────────────────────────

@frappe.whitelist()
def submit_maintenance_request(unit_name, category, priority, description):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."))
    tenant = _get_tenant_customer()
    req = frappe.new_doc("Maintenance Request")
    req.property_unit = unit_name
    req.tenant = tenant
    req.category = category
    req.priority = priority
    req.description = description
    req.reported_date = nowdate()
    req.flags.ignore_permissions = True
    req.insert()
    return req.name


@frappe.whitelist()
def get_invoice_pdf(invoice_name):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required."))
    tenant = _get_tenant_customer()
    inv_tenant = frappe.db.get_value("Rent Invoice", invoice_name, "tenant")
    if inv_tenant != tenant:
        frappe.throw(_("Access denied."))
    return frappe.get_print("Rent Invoice", invoice_name, as_pdf=True)
