"""Compatibility boundaries shared by installation and migration."""
import re

import frappe
from frappe import _


def get_major_version(version):
    """Also accept development versions such as 16.0.0-dev."""
    match = re.match(r"^(\d+)\.", str(version))
    return int(match.group(1)) if match else None


def validate_versions():
    import erpnext

    frappe_major = get_major_version(frappe.__version__)
    erpnext_major = get_major_version(erpnext.__version__)
    if frappe_major not in (15, 16) or erpnext_major != frappe_major:
        frappe.throw(_(
            "Real Estate requires matching Frappe and ERPNext major versions "
            "(15 or 16). Found Frappe {0} and ERPNext {1}."
        ).format(frappe.__version__, erpnext.__version__))


def get_desk_route():
    prefix = "/desk" if get_major_version(frappe.__version__) == 16 else "/app"
    return prefix + "/real-estate-dashboard"
