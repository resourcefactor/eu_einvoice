# Copyright (c) 2026, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe import _

DOCUMENT_STATUS_FILTERS = {
	"Submitted": ("=", 1),
	"Draft": ("=", 0),
	"Draft and Submitted": ("<", 2),
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_data(filters) -> list[dict]:
	list_filters = [
		["docstatus", *DOCUMENT_STATUS_FILTERS.get(filters.document_status or "Draft and Submitted")]
	]
	if filters.company:
		list_filters.append(["company", "=", filters.company])
	if filters.supplier:
		list_filters.append(["supplier", "=", filters.supplier])
	if filters.from_date:
		list_filters.append(["issue_date", ">=", filters.from_date])
	if filters.to_date:
		list_filters.append(["issue_date", "<=", filters.to_date])
	if filters.profile:
		list_filters.append(["profile", "=", filters.profile])
	if filters.validity:
		list_filters.append(["e_invoice_is_correct", "=", 1 if filters.validity == "Valid" else 0])

	imports = frappe.get_list(
		"E Invoice Import",
		filters=list_filters,
		fields=[
			"name",
			"docstatus",
			"company",
			"supplier",
			"seller_name",
			"id",
			"issue_date",
			"profile",
			"e_invoice_is_correct",
			"validation_errors",
			"grand_total",
			"currency",
			"purchase_order",
		],
		order_by="issue_date desc, name desc",
	)
	if not imports:
		return []

	purchase_invoices = {
		pi.e_invoice_import: pi.name
		for pi in frappe.get_list(
			"Purchase Invoice",
			filters={"e_invoice_import": ("in", [row.name for row in imports]), "docstatus": ("<", 2)},
			fields=["name", "e_invoice_import"],
		)
	}

	data = []
	for row in imports:
		purchase_invoice = purchase_invoices.get(row.name)
		if filters.purchase_invoice == "Linked" and not purchase_invoice:
			continue
		if filters.purchase_invoice == "Not Linked" and purchase_invoice:
			continue

		errors = [line for line in (row.validation_errors or "").splitlines() if line.strip()]
		data.append(
			{
				"e_invoice_import": row.name,
				"document_status": _("Submitted") if row.docstatus == 1 else _("Draft"),
				"issue_date": row.issue_date,
				"invoice_id": row.id,
				"company": row.company,
				"supplier": row.supplier,
				"seller_name": row.seller_name,
				"profile": row.profile,
				"e_invoice_is_correct": row.e_invoice_is_correct,
				"error_count": len(errors),
				"grand_total": row.grand_total,
				"currency": row.currency,
				"purchase_order": row.purchase_order,
				"purchase_invoice": purchase_invoice,
			}
		)

	return data


def get_columns() -> list[dict]:
	return [
		{
			"fieldname": "e_invoice_import",
			"label": _("E Invoice Import"),
			"fieldtype": "Link",
			"options": "E Invoice Import",
			"width": 160,
		},
		{"fieldname": "document_status", "label": _("Document Status"), "fieldtype": "Data", "width": 100},
		{"fieldname": "issue_date", "label": _("Issue Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "invoice_id", "label": _("Invoice ID"), "fieldtype": "Data", "width": 130},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 180,
		},
		{
			"fieldname": "supplier",
			"label": _("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120,
		},
		{"fieldname": "seller_name", "label": _("Seller Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "profile", "label": _("E Invoice Profile"), "fieldtype": "Data", "width": 100},
		{"fieldname": "e_invoice_is_correct", "label": _("Valid"), "fieldtype": "Check", "width": 70},
		{"fieldname": "error_count", "label": _("Errors"), "fieldtype": "Int", "width": 70},
		{
			"fieldname": "grand_total",
			"label": _("Grand Total"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120,
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 80,
		},
		{
			"fieldname": "purchase_order",
			"label": _("Purchase Order"),
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 140,
		},
		{
			"fieldname": "purchase_invoice",
			"label": _("Purchase Invoice"),
			"fieldtype": "Link",
			"options": "Purchase Invoice",
			"width": 140,
		},
	]
