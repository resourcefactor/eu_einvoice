// Extend the list view settings of ERPNext and other apps instead of replacing them.
frappe.listview_settings["Sales Invoice"] = frappe.listview_settings["Sales Invoice"] || {};

(function () {
	const settings = frappe.listview_settings["Sales Invoice"];
	const original_onload = settings.onload;

	settings.onload = function (listview) {
		original_onload && original_onload(listview);

		if (!eu_einvoice.utils.get_enabled_companies().length) {
			return;
		}

		listview.page.add_action_item(__("Attach eInvoice XML"), () => {
			const selected = listview.get_checked_items(true);
			if (!selected.length) {
				frappe.msgprint(__("Please select at least one Sales Invoice."));
				return;
			}

			eu_einvoice.utils.attach_xml(selected, () => listview.refresh());
		});
	};
})();
