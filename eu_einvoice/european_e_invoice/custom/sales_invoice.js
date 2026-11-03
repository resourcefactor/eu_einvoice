frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		if (!eu_einvoice.utils.is_enabled_for(frm.doc.company)) {
			return;
		}

		frm.trigger("add_einvoice_button");

		if (!frm.is_dirty() && !frm.doc.einvoice_is_correct && frm.doc.einvoice_profile) {
			frm.dashboard.set_headline_alert(
				__("Please note the validation errors of the e-invoice.")
			);
		}
	},
	add_einvoice_button: function (frm) {
		if (frm.is_new() || !frm.doc.einvoice_profile) {
			return;
		}

		frm.page.add_menu_item(__("Download eInvoice"), () => {
			window.open(
				`/api/method/eu_einvoice.european_e_invoice.custom.sales_invoice.download_xrechnung?invoice_id=${encodeURIComponent(
					frm.doc.name
				)}`,
				"_blank"
			);
		});

		if (frm.doc.docstatus === 1 && frm.perm[0]?.write) {
			frm.page.add_menu_item(__("Attach eInvoice XML"), () => {
				eu_einvoice.utils.attach_xml([frm.doc.name], () => frm.reload_doc());
			});
		}
	},
});
