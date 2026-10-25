"""Site-independent regression tests, runnable in either supported Bench env."""
import importlib
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import erpnext
import frappe

from real_estate import compat
from real_estate.setup import install
from real_estate.utils import dashboard_data


class TestCompatibility(unittest.TestCase):
    def test_installed_framework_versions(self):
        # Test the actual framework imports as well as the mocked boundaries below.
        compat.validate_versions()

    def test_controllers_and_hook_targets_import(self):
        from real_estate import hooks

        root = Path(__file__).resolve().parents[1]
        for path in (root / "real_estate" / "doctype").glob("*/*.py"):
            if path.stem == path.parent.name:
                module = ".".join(path.relative_to(root.parent).with_suffix("").parts)
                with self.subTest(module=module):
                    importlib.import_module(module)
        targets = [hooks.before_install, hooks.before_migrate, hooks.after_install]
        targets.extend(hooks.after_migrate)
        for tasks in hooks.scheduler_events.values():
            targets.extend(tasks)
        for target in targets:
            module, name = target.rsplit(".", 1)
            self.assertTrue(callable(getattr(importlib.import_module(module), name)))

    def test_framework_form_url(self):
        from frappe.utils.data import get_url_to_form

        with patch("frappe.utils.data.get_url", side_effect=lambda uri: uri):
            url = get_url_to_form("Lease Agreement", "LEASE 0001")
        prefix = "/desk" if compat.get_major_version(frappe.__version__) == 16 else "/app"
        self.assertEqual(url, prefix + "/lease-agreement/LEASE%200001")

    def test_supported_versions_and_routes(self):
        for major, prefix in [(15, "/app"), (16, "/desk")]:
            for suffix in [".0.0", ".0.0-dev", ".12.3"]:
                with self.subTest(major=major, suffix=suffix), patch.object(
                    frappe, "__version__", str(major) + suffix
                ), patch.object(erpnext, "__version__", str(major) + suffix):
                    compat.validate_versions()
                    self.assertEqual(compat.get_desk_route(), prefix + "/real-estate-dashboard")

    def test_unsupported_or_mismatched_versions(self):
        for framework, erp in [("14.0.0", "14.0.0"), ("17.0.0", "17.0.0"),
                               ("15.0.0", "16.0.0"), ("16.0.0", "15.0.0"),
                               ("unknown", "16.0.0")]:
            with self.subTest(framework=framework, erp=erp), patch.object(
                frappe, "__version__", framework
            ), patch.object(erpnext, "__version__", erp), patch.object(
                frappe, "_", side_effect=lambda value: value
            ), patch("real_estate.compat._", side_effect=lambda value: value), patch.object(
                frappe, "throw", side_effect=ValueError
            ):
                with self.assertRaises(ValueError):
                    compat.validate_versions()

    def test_setup_runs_all_steps(self):
        with patch.object(install, "_create_roles") as roles, patch.object(
            install, "_create_property_item"
        ) as items, patch.object(install, "_create_tenant_custom_fields") as fields, patch.object(
            install, "_create_workspace"
        ) as workspace:
            install.after_migrate()
            for step in [roles, items, fields, workspace]:
                step.assert_called_once_with()

    def test_existing_workspace_is_preserved(self):
        with patch.object(frappe, "db", SimpleNamespace(exists=lambda *args: True)), patch.object(
            frappe, "new_doc"
        ) as new_doc:
            install._create_workspace()
            new_doc.assert_not_called()

    def test_workspace_cards_match_links(self):
        workspace = MagicMock()
        with patch.object(frappe, "db", SimpleNamespace(exists=lambda *args: False)), patch.object(
            frappe, "new_doc", return_value=workspace
        ):
            install._create_workspace()
        cards = [block["data"]["card_name"] for block in json.loads(workspace.content)]
        links = [call.args[1] for call in workspace.append.call_args_list]
        self.assertEqual(cards, [link["label"] for link in links if link["type"] == "Card Break"])
        self.assertTrue(any(link.get("link_to") == "real-estate-dashboard" for link in links))
        workspace.insert.assert_called_once_with(ignore_permissions=True)

    def test_expiring_leases_ordered_before_limit(self):
        with patch.object(frappe, "get_all", return_value=[]) as query:
            self.assertEqual(dashboard_data._get_expiring_leases("2026-10-25"), [])
        self.assertEqual(query.call_args.kwargs["order_by"], "lease_end_date asc, name asc")
        self.assertEqual(query.call_args.kwargs["limit"], 10)


if __name__ == "__main__":
    unittest.main()
