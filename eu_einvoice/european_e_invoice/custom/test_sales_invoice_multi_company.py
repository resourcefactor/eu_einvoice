from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from eu_einvoice.european_e_invoice.custom.sales_invoice import attach_xml_on_submit, validate_doc

MODULE = "eu_einvoice.european_e_invoice.custom.sales_invoice"


def make_company_settings(**kwargs):
	return frappe.get_doc(
		{
			"doctype": "E Invoice Company Settings",
			"company": "Company A",
			"enabled": 1,
			"validate_on_save": 1,
			"validate_on_submit": 1,
			**kwargs,
		}
	)


def make_invoice(**kwargs):
	invoice = frappe.new_doc("Sales Invoice")
	invoice.update({"company": "Company A", "docstatus": 0, **kwargs})
	return invoice


class TestSalesInvoiceCompanyGating(FrappeTestCase):
	def test_disabled_company_clears_einvoice_fields(self):
		invoice = make_invoice(
			einvoice_profile="EXTENDED",
			einvoice_is_correct=1,
			validation_errors="Old error",
			validation_warnings="Old warning",
		)
		with (
			patch(f"{MODULE}.get_company_settings", return_value=None),
			patch(f"{MODULE}.validate_einvoice") as validate_einvoice,
		):
			validate_doc(invoice, "validate")

		validate_einvoice.assert_not_called()
		self.assertFalse(invoice.einvoice_profile)
		self.assertFalse(invoice.einvoice_is_correct)
		self.assertFalse(invoice.validation_errors)
		self.assertFalse(invoice.validation_warnings)

	def test_disabled_company_ignores_unsupported_charge_type(self):
		"""Used to fail with a ValueError for invoices without a profile."""
		invoice = make_invoice(taxes=[{"charge_type": "Actual", "description": "Freight"}])
		with patch(f"{MODULE}.get_company_settings", return_value=None):
			validate_doc(invoice, "validate")

	def test_default_profile_of_company(self):
		invoice = make_invoice()
		settings = make_company_settings(default_profile="EN 16931")
		with (
			patch(f"{MODULE}.get_company_settings", return_value=settings),
			patch(f"{MODULE}.validate_einvoice") as validate_einvoice,
		):
			validate_doc(invoice, "validate")

		self.assertEqual(invoice.einvoice_profile, "EN 16931")
		validate_einvoice.assert_called_once_with(invoice)

	def test_customer_profile_takes_precedence(self):
		invoice = make_invoice(einvoice_profile="XRECHNUNG")
		settings = make_company_settings(default_profile="EN 16931")
		with (
			patch(f"{MODULE}.get_company_settings", return_value=settings),
			patch(f"{MODULE}.validate_einvoice"),
		):
			validate_doc(invoice, "validate")

		self.assertEqual(invoice.einvoice_profile, "XRECHNUNG")

	def test_validation_disabled_for_company(self):
		invoice = make_invoice(einvoice_profile="EXTENDED")
		settings = make_company_settings(validate_on_save=0)
		with (
			patch(f"{MODULE}.get_company_settings", return_value=settings),
			patch(f"{MODULE}.validate_einvoice") as validate_einvoice,
		):
			validate_doc(invoice, "validate")

		validate_einvoice.assert_not_called()

	def test_attach_invalid_xml_on_submit(self):
		invoice = make_invoice(einvoice_profile="EXTENDED", einvoice_is_correct=0, docstatus=1)
		invoice._einvoice_xml_bytes = b"<rsm:CrossIndustryInvoice/>"
		settings = make_company_settings(auto_attach_xml=1)
		with (
			patch(f"{MODULE}.get_company_settings", return_value=settings),
			patch(f"{MODULE}._attach_xml_file") as attach,
		):
			attach_xml_on_submit(invoice, "on_submit")

		attach.assert_called_once_with(invoice, b"<rsm:CrossIndustryInvoice/>")

	def test_no_attach_when_disabled(self):
		invoice = make_invoice(einvoice_profile="EXTENDED", docstatus=1)
		invoice._einvoice_xml_bytes = b"<xml/>"
		for settings in (None, make_company_settings(auto_attach_xml=0)):
			with (
				patch(f"{MODULE}.get_company_settings", return_value=settings),
				patch(f"{MODULE}._attach_xml_file") as attach,
			):
				attach_xml_on_submit(invoice, "on_submit")

			attach.assert_not_called()
