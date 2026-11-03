from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from eu_einvoice.european_e_invoice.report.e_invoice_status.e_invoice_status import (
	INVALID,
	NOT_EINVOICED,
	NOT_VALIDATED,
	VALID,
	execute,
	get_status,
)

MODULE = "eu_einvoice.european_e_invoice.report.e_invoice_status.e_invoice_status"


def mock_sales_invoice_list(invoices: list) -> MagicMock:
	"""Return `invoices` for Sales Invoice queries; other queries (e.g. translations) hit the database."""
	real_get_list = frappe.get_list

	def get_list(doctype, *args, **kwargs):
		if doctype == "Sales Invoice":
			return invoices
		return real_get_list(doctype, *args, **kwargs)

	return MagicMock(side_effect=get_list)


def sales_invoice_calls(get_list: MagicMock) -> list:
	return [call for call in get_list.call_args_list if call.args[0] == "Sales Invoice"]


class TestEInvoiceStatus(FrappeTestCase):
	def test_status(self):
		self.assertEqual(get_status(None, 0, None), NOT_EINVOICED)
		self.assertEqual(get_status("EXTENDED", 1, None), VALID)
		self.assertEqual(get_status("EXTENDED", 0, "[BR-01] error"), INVALID)
		self.assertEqual(get_status("EXTENDED", 0, ""), NOT_VALIDATED)

	def test_only_enabled_companies(self):
		with (
			patch(f"{MODULE}.get_enabled_companies", return_value=["Company A"]),
			patch(f"{MODULE}.frappe.get_list", new=mock_sales_invoice_list([])) as get_list,
		):
			self.assertEqual(execute({"company": "Company B"})[1], [])
			self.assertEqual(sales_invoice_calls(get_list), [])

			execute({})
			list_filters = sales_invoice_calls(get_list)[0].kwargs["filters"]
			self.assertIn(["company", "in", ["Company A"]], list_filters)
			self.assertIn(["docstatus", "=", 1], list_filters)

	def test_summary_and_chart(self):
		invoices = [
			frappe._dict(
				name="SI-1",
				einvoice_profile="EXTENDED",
				einvoice_is_correct=1,
				einvoice_xml_file="/private/files/SI-1.xml",
				docstatus=1,
			),
			frappe._dict(
				name="SI-2",
				einvoice_profile="EXTENDED",
				einvoice_is_correct=0,
				validation_errors="[BR-01] first\n[BR-02] second",
				docstatus=1,
			),
		]
		with (
			patch(f"{MODULE}.get_enabled_companies", return_value=["Company A"]),
			patch(f"{MODULE}.frappe.get_list", new=mock_sales_invoice_list(invoices)),
		):
			_columns, data, _message, chart, summary = execute({})

		self.assertEqual([row["status"] for row in data], [VALID, INVALID])
		self.assertEqual(data[1]["error_count"], 2)
		self.assertEqual(data[1]["first_error"], "[BR-01] first")
		self.assertEqual(chart["data"]["datasets"][0]["values"], [1, 1, 0, 0])
		summary_values = {item["label"]: item["value"] for item in summary}
		self.assertEqual(summary_values["Sales Invoices"], 2)
		self.assertEqual(summary_values["XML Attached"], 1)
