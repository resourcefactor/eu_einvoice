import frappe

OLD_NAME = "E Invoice Settings"
NEW_NAME = "EU Einvoice Settings"


def execute():
	"""Rename the settings, so that they can't be confused with e-invoicing apps of other regions."""
	if not frappe.db.exists("DocType", OLD_NAME) or frappe.db.exists("DocType", NEW_NAME):
		return

	# Also moves the values in tabSingles and the parenttype of child rows
	frappe.rename_doc("DocType", OLD_NAME, NEW_NAME, force=True)

	# Child rows of a Single DocType use the DocType's name as their parent
	if frappe.db.table_exists("E Invoice Company Settings"):
		child = frappe.qb.DocType("E Invoice Company Settings")
		frappe.qb.update(child).set(child.parent, NEW_NAME).where(child.parent == OLD_NAME).run()
