"""Backend data provider for the portfolio dashboard page."""
import frappe
from frappe.utils import (
    add_days, add_months, date_diff, get_first_day, get_last_day, nowdate
)


@frappe.whitelist()
def get_dashboard_data():
    today = nowdate()
    return {
        "kpis": _get_kpis(today),
        "occupancy": _get_occupancy(),
        "monthly_revenue": _get_monthly_revenue(today),
        "expiring_leases": _get_expiring_leases(today),
        "maintenance": _get_maintenance_stats(today),
    }


def _get_kpis(today):
    total_units = frappe.db.count("Property Unit")
    occupied = frappe.db.count("Property Unit", {"status": "Occupied"})
    return {
        "properties": frappe.db.count("Property"),
        "total_units": total_units,
        "occupied": occupied,
        "occupancy_rate": round((occupied / total_units * 100), 1) if total_units else 0,
        "overdue_invoices": frappe.db.count("Rent Invoice", {"status": "Overdue", "docstatus": ("!=", 2)}),
        "open_maintenance": frappe.db.count("Maintenance Request", {"status": ("in", ["Open", "Assigned", "In Progress"])}),
    }


def _get_occupancy():
    statuses = ["Occupied", "Available", "Reserved", "Under Renovation"]
    result = {}
    for s in statuses:
        result[s.lower().replace(" ", "_")] = frappe.db.count("Property Unit", {"status": s})
    return result


def _get_monthly_revenue(today):
    labels, values = [], []
    for i in range(5, -1, -1):
        month_start = get_first_day(add_months(today, -i))
        month_end = get_last_day(add_months(today, -i))
        total = frappe.db.sql(
            """SELECT IFNULL(SUM(total_amount), 0) FROM `tabRent Invoice`
               WHERE status = 'Paid' AND docstatus = 1
               AND billing_period_start BETWEEN %s AND %s""",
            (month_start, month_end),
        )[0][0]
        labels.append(str(month_start)[:7])
        values.append(float(total))
    return {"labels": labels, "values": values}


def _get_expiring_leases(today):
    leases = frappe.get_all(
        "Lease Agreement",
        filters={
            "lease_status": "Active",
            "docstatus": 1,
            "lease_end_date": ("between", [today, add_days(today, 60)]),
        },
        fields=["name", "property_unit", "tenant", "lease_end_date"],
        order_by="lease_end_date asc, name asc",
        limit=10,
    )
    for l in leases:
        l["days_left"] = date_diff(l.lease_end_date, today)
    return sorted(leases, key=lambda x: x["days_left"])


def _get_maintenance_stats(today):
    completed_after = add_days(today, -30)
    return {
        "open": frappe.db.count("Maintenance Request", {"status": "Open"}),
        "assigned": frappe.db.count("Maintenance Request", {"status": "Assigned"}),
        "in_progress": frappe.db.count("Maintenance Request", {"status": "In Progress"}),
        "completed_30d": frappe.db.count(
            "Maintenance Request",
            {"status": "Completed", "completion_date": (">=", completed_after)},
        ),
    }
