// Copyright (c) 2026, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.query_reports["E Invoice Import Register"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			get_query: () => ({
				filters: { name: ["in", eu_einvoice.utils.get_enabled_companies()] },
			}),
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "from_date",
			label: __("From Issue Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Issue Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "profile",
			label: __("E Invoice Profile"),
			fieldtype: "Select",
			options: ["", "BASIC", "EN 16931", "EXTENDED", "XRECHNUNG"],
		},
		{
			fieldname: "validity",
			label: __("Validation"),
			fieldtype: "Select",
			options: [
				{ value: "", label: "" },
				{ value: "Valid", label: __("Valid") },
				{ value: "Invalid", label: __("Invalid") },
			],
		},
		{
			fieldname: "purchase_invoice",
			label: __("Purchase Invoice"),
			fieldtype: "Select",
			options: [
				{ value: "", label: "" },
				{ value: "Linked", label: __("Linked") },
				{ value: "Not Linked", label: __("Not Linked") },
			],
		},
		{
			fieldname: "document_status",
			label: __("Document Status"),
			fieldtype: "Select",
			options: [
				{ value: "Draft and Submitted", label: __("Draft and Submitted") },
				{ value: "Submitted", label: __("Submitted") },
				{ value: "Draft", label: __("Draft") },
			],
			default: "Draft and Submitted",
		},
	],
};
