// Copyright (c) 2025, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("EU Einvoice Settings", {
	setup(frm) {
		frm.set_query("company", "company_settings", function () {
			return {
				filters: {
					is_group: 0,
				},
			};
		});
	},

	refresh(frm) {
		frm.trigger("set_invoice_number_field_options");
		frm.add_custom_button(__("Import Code Lists"), () => frm.trigger("import_code_lists"));
	},

	async import_code_lists(frm) {
		await frm.call("import_code_lists");
		frappe.show_alert({
			message: __("Import of code lists queued. This may take a few minutes."),
			indicator: "green",
		});
	},

	async set_invoice_number_field_options(frm) {
		const options = await get_autocomplete_options("Sales Invoice", ["Data", "Read Only"]);
		frm.fields_dict.company_settings.grid.update_docfield_property(
			"sales_invoice_number_field",
			"options",
			options
		);
	},
});

frappe.ui.form.on("E Invoice Company Settings", {
	company_settings_add(frm, cdt, cdn) {
		// Enabling e-invoicing should be a conscious choice, don't prefill the user's default company
		frappe.model.set_value(cdt, cdn, "company", "");
	},
});

async function get_autocomplete_options(doctype, allowed_fieldtypes) {
	await frappe.model.with_doctype(doctype);
	const meta = frappe.get_meta(doctype);
	return meta.fields
		.filter((d) => allowed_fieldtypes.includes(d.fieldtype))
		.map((value) => {
			return {
				label: __(value.label, null, doctype),
				description: value.fieldname,
				value: value.fieldname,
			};
		})
		.sort((a, b) => a.label.localeCompare(b.label));
}
