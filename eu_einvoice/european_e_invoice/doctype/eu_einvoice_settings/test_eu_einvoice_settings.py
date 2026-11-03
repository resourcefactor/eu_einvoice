# Copyright (c) 2025, ALYF GmbH and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.model.docstatus import DocStatus
from frappe.tests.utils import FrappeTestCase

from eu_einvoice.company_settings import get_company_settings, get_enabled_companies, is_einvoice_enabled


def make_settings(*rows: dict):
	return frappe.get_doc({"doctype": "EU Einvoice Settings", "company_settings": list(rows)})


class TestEUEinvoiceSettings(FrappeTestCase):
	def test_company_listed_once(self):
		settings = make_settings({"company": "Company A"}, {"company": "Company A"})
		self.assertRaises(frappe.ValidationError, settings.validate)

	def test_error_action_cleared_without_validation(self):
		settings = make_settings(
			{
				"company": "Company A",
				"validate_on_save": 0,
				"error_action_on_save": "Error Message",
				"validate_on_submit": 1,
				"error_action_on_submit": "Warning Message",
			}
		)
		settings.before_validate()
		self.assertEqual(settings.company_settings[0].error_action_on_save, "")
		self.assertEqual(settings.company_settings[0].error_action_on_submit, "Warning Message")

	def test_error_actions(self):
		row = make_settings(
			{
				"company": "Company A",
				"validate_on_save": 1,
				"error_action_on_save": "Warning Message",
				"validate_on_submit": 0,
				"error_action_on_submit": "Error Message",
			}
		).company_settings[0]
		self.assertTrue(row.should_validate(DocStatus.draft()))
		self.assertFalse(row.should_validate(DocStatus.submitted()))
		self.assertTrue(row.should_show_message(DocStatus.draft()))
		self.assertFalse(row.should_raise_exception(DocStatus.draft()))
		self.assertTrue(row.should_raise_exception(DocStatus.submitted()))

	def test_company_resolution(self):
		settings = make_settings(
			{"company": "Company A", "enabled": 1, "default_profile": "EXTENDED"},
			{"company": "Company B", "enabled": 0},
		)
		with patch("eu_einvoice.company_settings.frappe.get_cached_doc", return_value=settings):
			self.assertEqual(get_company_settings("Company A").default_profile, "EXTENDED")
			self.assertIsNone(get_company_settings("Company B"), "disabled row")
			self.assertIsNone(get_company_settings("Company C"), "company not listed")
			self.assertIsNone(get_company_settings(None))
			self.assertTrue(is_einvoice_enabled("Company A"))
			self.assertFalse(is_einvoice_enabled("Company B"))
			self.assertEqual(get_enabled_companies(), ["Company A"])
