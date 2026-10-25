"""
Automated rent billing engine.
Runs daily — creates Rent Invoice for each Active lease where today == payment_due_day.
Also handles late fees and payment reminder notifications.
"""
import frappe
from frappe.utils import (
    add_days, flt, get_first_day, get_last_day, getdate,
    nowdate, today,
)
from frappe.utils.data import get_datetime
from datetime import date


def run_daily_billing():
    """Entry point: called by Frappe scheduler daily."""
    today_date = getdate(nowdate())
    active_leases = frappe.get_all(
        "Lease Agreement",
        filters={"lease_status": "Active", "docstatus": 1},
        fields=["name", "property_unit", "tenant", "monthly_rent",
                "security_deposit", "payment_due_day", "grace_period_days",
                "late_fee_percent", "lease_start_date",
                "lease_end_date", "escalation_percent"],
    )
    for lease in active_leases:
        if lease.payment_due_day and today_date.day == lease.payment_due_day:
            _create_rent_invoice(lease, today_date)


def _create_rent_invoice(lease, billing_date):
    """Create a Rent Invoice for the given lease if not already created this period."""
    period_start = get_first_day(billing_date)
    period_end = get_last_day(billing_date)
    existing = frappe.db.exists(
        "Rent Invoice",
        {
            "lease": lease.name,
            "billing_period_start": period_start,
            "docstatus": ("!=", 2),
        },
    )
    if existing:
        return
    inv = frappe.new_doc("Rent Invoice")
    inv.lease = lease.name
    inv.tenant = lease.tenant
    inv.billing_period_start = period_start
    inv.billing_period_end = period_end
    inv.base_rent = flt(lease.monthly_rent)
    inv.vat_percent = 0
    inv.status = "Unpaid"
    inv.flags.ignore_permissions = True
    inv.insert()
    frappe.db.commit()
    return inv.name


@frappe.whitelist()
def create_invoice_for_lease(lease_name):
    """Manual trigger — create invoice for a lease today."""
    lease = frappe.get_doc("Lease Agreement", lease_name)
    today_date = getdate(nowdate())
    return _create_rent_invoice(lease, today_date)


def apply_late_fees():
    """
    Find Unpaid invoices whose billing_period_start + grace_period_days < today.
    Apply late_fee if not already applied.
    """
    today_date = getdate(nowdate())
    overdue_invoices = frappe.get_all(
        "Rent Invoice",
        filters={"status": "Unpaid", "late_fee": 0, "docstatus": 0},
        fields=["name", "lease", "billing_period_start", "base_rent", "late_fee"],
    )
    for inv_data in overdue_invoices:
        grace = frappe.db.get_value("Lease Agreement", inv_data.lease, "grace_period_days") or 0
        late_fee_pct = frappe.db.get_value("Lease Agreement", inv_data.lease, "late_fee_percent") or 0
        due_with_grace = add_days(inv_data.billing_period_start, grace)
        if today_date > getdate(due_with_grace) and late_fee_pct:
            late_fee = flt(inv_data.base_rent) * flt(late_fee_pct) / 100
            inv = frappe.get_doc("Rent Invoice", inv_data.name)
            inv.late_fee = late_fee
            inv.status = "Overdue"
            inv.save(ignore_permissions=True)
    frappe.db.commit()


def send_payment_reminders():
    """Send reminder emails/notifications 3 days before due, on due date, 1 day after overdue."""
    today_date = getdate(nowdate())
    active_leases = frappe.get_all(
        "Lease Agreement",
        filters={"lease_status": "Active", "docstatus": 1},
        fields=["name", "tenant", "payment_due_day", "grace_period_days"],
    )
    for lease in active_leases:
        if not lease.payment_due_day:
            continue
        due_day = lease.payment_due_day
        days_to_due = due_day - today_date.day
        grace = lease.grace_period_days or 0
        tenant_email = frappe.db.get_value("Customer", lease.tenant, "email_id")
        if not tenant_email:
            continue
        if days_to_due == 3:
            _send_rent_reminder(lease.name, lease.tenant, tenant_email, "3 days before due")
        elif days_to_due == 0:
            _send_rent_reminder(lease.name, lease.tenant, tenant_email, "due today")
        elif days_to_due == -(grace + 1):
            _send_rent_reminder(lease.name, lease.tenant, tenant_email, "overdue — immediate payment required")


def _send_rent_reminder(lease_name, tenant, tenant_email, context):
    subject = f"Rent Payment Reminder — {context.title()}"
    message = f"""
        <p>Dear {tenant},</p>
        <p>This is a reminder that your rent payment for lease <strong>{lease_name}</strong> is <strong>{context}</strong>.</p>
        <p>Please make your payment promptly to avoid late fees.</p>
        <p>Thank you,<br/>Property Management Team</p>
    """
    frappe.sendmail(
        recipients=[tenant_email],
        subject=subject,
        message=message,
        now=True,
    )
