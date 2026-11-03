# Copyright (c) 2026, ALYF GmbH and contributors
# For license information, please see license.txt

from frappe.model.docstatus import DocStatus
from frappe.model.document import Document


class EInvoiceCompanySettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		auto_attach_xml: DF.Check
		auto_name_format_for_xml_file: DF.Data | None
		company: DF.Link
		default_profile: DF.Literal["", "BASIC", "EN 16931", "EXTENDED", "XRECHNUNG"]
		enabled: DF.Check
		error_action_on_save: DF.Literal["", "Warning Message", "Error Message"]
		error_action_on_submit: DF.Literal["", "Warning Message", "Error Message"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		sales_invoice_number_field: DF.Autocomplete | None
		validate_on_save: DF.Check
		validate_on_submit: DF.Check
		vat_exemption_reason_text: DF.SmallText | None
	# end: auto-generated types

	def should_validate(self, docstatus: DocStatus) -> bool:
		"""Return True if a Sales Invoice should be validated."""
		return bool(
			(docstatus == DocStatus.submitted() and self.validate_on_submit)
			or (docstatus == DocStatus.draft() and self.validate_on_save)
		)

	def should_raise_exception(self, docstatus: DocStatus) -> bool:
		"""Return True if the error action is set to 'Error Message'."""
		return (docstatus == DocStatus.submitted() and self.error_action_on_submit == "Error Message") or (
			docstatus == DocStatus.draft() and self.error_action_on_save == "Error Message"
		)

	def should_show_message(self, docstatus: DocStatus) -> bool:
		"""Return True if any error action is set."""
		return bool(
			(docstatus == DocStatus.submitted() and self.error_action_on_submit)
			or (docstatus == DocStatus.draft() and self.error_action_on_save)
		)
