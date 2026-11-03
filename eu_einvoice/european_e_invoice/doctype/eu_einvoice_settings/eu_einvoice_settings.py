# Copyright (c) 2025, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EUEinvoiceSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from eu_einvoice.european_e_invoice.doctype.e_invoice_company_settings.e_invoice_company_settings import (
			EInvoiceCompanySettings,
		)

		company_settings: DF.Table[EInvoiceCompanySettings]
	# end: auto-generated types

	@frappe.whitelist()
	def import_code_lists(self):
		"""Import the bundled EN 16931 code lists into an existing site."""
		frappe.only_for("System Manager")
		# ~4600 Common Codes, too slow for a request
		frappe.enqueue(
			"eu_einvoice.install.import_code_lists",
			queue="long",
			timeout=1800,
			enqueue_after_commit=True,
		)

	def before_validate(self):
		for row in self.company_settings:
			if not row.validate_on_save:
				row.error_action_on_save = ""
			if not row.validate_on_submit:
				row.error_action_on_submit = ""

	def validate(self):
		self._validate_unique_companies()
		self._validate_invoice_number_fields()

	def _validate_unique_companies(self):
		seen = set()
		for row in self.company_settings:
			if row.company in seen:
				frappe.throw(
					_("Row #{0}: Company {1} is listed more than once.").format(
						row.idx, frappe.bold(row.company)
					)
				)
			seen.add(row.company)

	def _validate_invoice_number_fields(self):
		sales_invoice_meta = frappe.get_meta("Sales Invoice")
		for row in self.company_settings:
			if row.sales_invoice_number_field and not sales_invoice_meta.has_field(
				row.sales_invoice_number_field
			):
				frappe.throw(
					_("Row #{0}: Field '{1}' does not exist on Sales Invoice.").format(
						row.idx, row.sales_invoice_number_field
					)
				)
