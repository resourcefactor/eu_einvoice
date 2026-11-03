import frappe


def execute():
	"""Set the default settings for the new 'EU Einvoice Settings' doctype."""
	settings = frappe.get_single("EU Einvoice Settings")
	settings.validate_sales_invoice_on_save = 1
	settings.validate_sales_invoice_on_submit = 1
	settings.error_action_on_save = ""
	settings.error_action_on_submit = ""
	settings.save()
