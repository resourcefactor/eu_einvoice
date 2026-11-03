# Copyright (c) 2026, ALYF GmbH and contributors
# For license information, please see license.txt

from collections import Counter

import frappe
from frappe import _

from eu_einvoice.company_settings import get_enabled_companies

VALID = "Valid"
INVALID = "Invalid"
NOT_VALIDATED = "Not Validated"
NOT_EINVOICED = "Not E-Invoiced"
STATUS_COLORS = {
	VALID: "#29CD42",
	INVALID: "#E24C4C",
	NOT_VALIDATED: "#ECAD4B",
	NOT_EINVOICED: "#98A2B3",
}
DOCUMENT_STATUS_FILTERS = {
	"Submitted": ("=", 1),
	"Draft": ("=", 0),
	"Draft and Submitted": ("<", 2),
}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	data = get_data(filters)
	return get_columns(), data, None, get_chart(data), get_summary(data)


def get_status(einvoice_profile: str | None, einvoice_is_correct: int, validation_errors: str | None) -> str:
	if not einvoice_profile:
		return NOT_EINVOICED
	if einvoice_is_correct:
		return VALID
	if validation_errors:
		return INVALID
	return NOT_VALIDATED


def get_status_filters(status: str | None) -> list:
	if status == VALID:
		return [["einvoice_profile", "is", "set"], ["einvoice_is_correct", "=", 1]]
	if status == INVALID:
		return [
			["einvoice_profile", "is", "set"],
			["einvoice_is_correct", "=", 0],
			["validation_errors", "is", "set"],
		]
	if status == NOT_VALIDATED:
		return [
			["einvoice_profile", "is", "set"],
			["einvoice_is_correct", "=", 0],
			["validation_errors", "is", "not set"],
		]
	if status == NOT_EINVOICED:
		return [["einvoice_profile", "is", "not set"]]
	return []


def get_data(filters) -> list[dict]:
	# Only companies that use e-invoicing are relevant. User permissions apply via `frappe.get_list`.
	companies = get_enabled_companies()
	if filters.company:
		companies = [filters.company] if filters.company in companies else []
	if not companies:
		return []

	list_filters = [
		["company", "in", companies],
		["docstatus", *DOCUMENT_STATUS_FILTERS.get(filters.document_status or "Submitted")],
	]
	if filters.from_date:
		list_filters.append(["posting_date", ">=", filters.from_date])
	if filters.to_date:
		list_filters.append(["posting_date", "<=", filters.to_date])
	if filters.customer:
		list_filters.append(["customer", "=", filters.customer])
	if filters.einvoice_profile:
		list_filters.append(["einvoice_profile", "=", filters.einvoice_profile])
	if filters.xml_attached:
		list_filters.append(
			["einvoice_xml_file", "is", "set" if filters.xml_attached == "Yes" else "not set"]
		)
	list_filters.extend(get_status_filters(filters.status))

	invoices = frappe.get_list(
		"Sales Invoice",
		filters=list_filters,
		fields=[
			"name",
			"posting_date",
			"company",
			"customer",
			"customer_name",
			"docstatus",
			"einvoice_profile",
			"einvoice_is_correct",
			"validation_errors",
			"validation_warnings",
			"einvoice_xml_file",
			"grand_total",
			"currency",
		],
		order_by="posting_date desc, name desc",
	)

	data = []
	for invoice in invoices:
		errors = [line for line in (invoice.validation_errors or "").splitlines() if line.strip()]
		warnings = [line for line in (invoice.validation_warnings or "").splitlines() if line.strip()]
		data.append(
			{
				"sales_invoice": invoice.name,
				"posting_date": invoice.posting_date,
				"company": invoice.company,
				"customer": invoice.customer,
				"customer_name": invoice.customer_name,
				"document_status": _("Submitted") if invoice.docstatus == 1 else _("Draft"),
				"einvoice_profile": invoice.einvoice_profile,
				"status": get_status(
					invoice.einvoice_profile, invoice.einvoice_is_correct, invoice.validation_errors
				),
				"error_count": len(errors),
				"warning_count": len(warnings),
				"first_error": errors[0] if errors else None,
				"xml_attached": 1 if invoice.einvoice_xml_file else 0,
				"xml_file": invoice.einvoice_xml_file,
				"grand_total": invoice.grand_total,
				"currency": invoice.currency,
			}
		)

	return data


def get_columns() -> list[dict]:
	return [
		{
			"fieldname": "sales_invoice",
			"label": _("Sales Invoice"),
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 160,
		},
		{"fieldname": "posting_date", "label": _("Posting Date"), "fieldtype": "Date", "width": 100},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 180,
		},
		{
			"fieldname": "customer",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 110,
		},
		{"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "document_status", "label": _("Document Status"), "fieldtype": "Data", "width": 100},
		{"fieldname": "einvoice_profile", "label": _("E Invoice Profile"), "fieldtype": "Data", "width": 100},
		{"fieldname": "status", "label": _("E-Invoice Status"), "fieldtype": "Data", "width": 130},
		{"fieldname": "error_count", "label": _("Errors"), "fieldtype": "Int", "width": 70},
		{"fieldname": "warning_count", "label": _("Warnings"), "fieldtype": "Int", "width": 80},
		{"fieldname": "first_error", "label": _("First Error"), "fieldtype": "Data", "width": 300},
		{"fieldname": "xml_attached", "label": _("XML Attached"), "fieldtype": "Check", "width": 100},
		{"fieldname": "xml_file", "label": _("XML File"), "fieldtype": "Data", "width": 100},
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
	]


def get_chart(data: list[dict]) -> dict | None:
	if not data:
		return None

	# Always list all statuses in the same order, so that the colors of the
	# "E-Invoice Status" dashboard chart (custom_options) match the labels.
	counts = Counter(row["status"] for row in data)
	return {
		"data": {
			"labels": [_(status) for status in STATUS_COLORS],
			"datasets": [
				{"name": _("Sales Invoices"), "values": [counts[status] for status in STATUS_COLORS]}
			],
		},
		"type": "donut",
		"colors": list(STATUS_COLORS.values()),
	}


def get_summary(data: list[dict]) -> list[dict]:
	if not data:
		return []

	counts = Counter(row["status"] for row in data)
	xml_attached = sum(row["xml_attached"] for row in data)
	return [
		{"value": len(data), "label": _("Sales Invoices"), "datatype": "Int", "indicator": "Blue"},
		{"value": counts[VALID], "label": _(VALID), "datatype": "Int", "indicator": "Green"},
		{"value": counts[INVALID], "label": _(INVALID), "datatype": "Int", "indicator": "Red"},
		{"value": counts[NOT_VALIDATED], "label": _(NOT_VALIDATED), "datatype": "Int", "indicator": "Orange"},
		{"value": counts[NOT_EINVOICED], "label": _(NOT_EINVOICED), "datatype": "Int", "indicator": "Grey"},
		{"value": xml_attached, "label": _("XML Attached"), "datatype": "Int", "indicator": "Green"},
	]
