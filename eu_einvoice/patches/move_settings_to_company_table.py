import frappe
from frappe.utils import cint


def execute():
	"""Move the former global EU Einvoice Settings into per-company rows.

	A row is created for every company that already has e-invoices, or for the only company
	of a single-company site, so that e-invoicing keeps working where it was used before.
	All other companies stay disabled until they are added to the settings.
	"""
	settings = frappe.get_single("EU Einvoice Settings")
	if settings.company_settings:
		return

	old_values = frappe.db.get_singles_dict("EU Einvoice Settings")
	companies = frappe.get_all(
		"Sales Invoice", filters={"einvoice_profile": ("is", "set")}, pluck="company", distinct=True
	)
	if not companies:
		all_companies = frappe.get_all("Company", pluck="name")
		if len(all_companies) == 1:
			companies = all_companies

	for company in sorted(companies):
		settings.append(
			"company_settings",
			{
				"company": company,
				"enabled": 1,
				"validate_on_save": cint(old_values.get("validate_sales_invoice_on_save", 1)),
				"validate_on_submit": cint(old_values.get("validate_sales_invoice_on_submit", 1)),
				"error_action_on_save": old_values.get("error_action_on_save") or "",
				"error_action_on_submit": old_values.get("error_action_on_submit") or "",
				"sales_invoice_number_field": old_values.get("sales_invoice_number_field"),
				"auto_attach_xml": cint(old_values.get("auto_attach_xml")),
				"auto_name_format_for_xml_file": old_values.get("auto_name_format_for_xml_file"),
				"vat_exemption_reason_text": old_values.get("vat_exemption_reason_text"),
			},
		)

	if settings.company_settings:
		settings.flags.ignore_validate = True
		settings.save()
