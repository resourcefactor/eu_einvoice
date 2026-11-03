frappe.provide("eu_einvoice");

eu_einvoice.utils = {
	/**
	 * Supposed to be called when the user clicks the "Create Purchase Invoice"
	 * button in the error message, when the uploaded file in the E Invoice Import
	 * does not contain XML data.
	 *
	 * Needs to be a global function because it is called 'from the backend'.
	 */
	new_purchase_invoice: function () {
		frappe.new_doc("Purchase Invoice", {
			company: cur_frm.doc.company,
			supplier_invoice_file: cur_frm.doc.einvoice,
		});
	},

	/** Companies with e-invoicing enabled in EU Einvoice Settings. */
	get_enabled_companies: function () {
		return frappe.boot.eu_einvoice?.enabled_companies || [];
	},

	is_enabled_for: function (company) {
		return !!company && eu_einvoice.utils.get_enabled_companies().includes(company);
	},

	attach_xml: function (invoice_names, callback) {
		return frappe
			.xcall("eu_einvoice.european_e_invoice.custom.sales_invoice.attach_einvoice_xml", {
				invoice_names: invoice_names,
			})
			.then((result) => {
				if (!result) {
					frappe.show_alert({
						message: __(
							"The e-invoice XML files are being attached in the background."
						),
						indicator: "blue",
					});
					return;
				}

				let message = __("E-invoice XML attached to {0} Sales Invoice(s).", [
					result.attached.length,
				]);
				const skipped = Object.entries(result.skipped);
				if (skipped.length) {
					message += "<br><br>" + __("Skipped:") + "<ul>";
					message += skipped
						.map(
							([name, reason]) =>
								`<li>${frappe.utils.escape_html(name)}: ${frappe.utils.escape_html(
									reason
								)}</li>`
						)
						.join("");
					message += "</ul>";
				}
				frappe.msgprint({
					title: __("Attach eInvoice XML"),
					message: message,
					indicator: skipped.length ? "orange" : "green",
				});
				callback && callback(result);
			});
	},
};
