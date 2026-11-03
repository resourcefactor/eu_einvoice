// Copyright (c) 2026, ALYF GmbH and contributors
// For license information, please see license.txt

const E_INVOICE_STATUS_INDICATORS = {
	Valid: "green",
	Invalid: "red",
	"Not Validated": "orange",
	"Not E-Invoiced": "gray",
};

frappe.query_reports["E Invoice Status"] = {
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
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "einvoice_profile",
			label: __("E Invoice Profile"),
			fieldtype: "Select",
			options: ["", "BASIC", "EN 16931", "EXTENDED", "XRECHNUNG"],
		},
		{
			fieldname: "status",
			label: __("E-Invoice Status"),
			fieldtype: "Select",
			options: [
				{ value: "", label: "" },
				...Object.keys(E_INVOICE_STATUS_INDICATORS).map((status) => ({
					value: status,
					label: __(status),
				})),
			],
		},
		{
			fieldname: "xml_attached",
			label: __("XML Attached"),
			fieldtype: "Select",
			options: [
				{ value: "", label: "" },
				{ value: "Yes", label: __("Yes") },
				{ value: "No", label: __("No") },
			],
		},
		{
			fieldname: "document_status",
			label: __("Document Status"),
			fieldtype: "Select",
			options: [
				{ value: "Submitted", label: __("Submitted") },
				{ value: "Draft", label: __("Draft") },
				{ value: "Draft and Submitted", label: __("Draft and Submitted") },
			],
			default: "Submitted",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		if (data && column.fieldname === "status") {
			const indicator = E_INVOICE_STATUS_INDICATORS[data.status] || "gray";
			return `<span class="indicator ${indicator}">${__(data.status)}</span>`;
		}

		if (data && column.fieldname === "xml_file" && data.xml_file) {
			return `<a href="${encodeURI(data.xml_file)}" target="_blank">${__("Download")}</a>`;
		}

		return default_formatter(value, row, column, data);
	},
};
