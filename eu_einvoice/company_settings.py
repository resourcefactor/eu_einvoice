from __future__ import annotations

from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from eu_einvoice.european_e_invoice.doctype.e_invoice_company_settings.e_invoice_company_settings import (
		EInvoiceCompanySettings,
	)


def get_company_settings(company: str | None) -> EInvoiceCompanySettings | None:
	"""Return the E Invoice settings row of the company, or None if e-invoicing is not enabled for it."""
	if not company:
		return None

	settings = frappe.get_cached_doc("EU Einvoice Settings")
	return next(
		(row for row in settings.company_settings if row.company == company and row.enabled),
		None,
	)


def is_einvoice_enabled(company: str | None) -> bool:
	return get_company_settings(company) is not None


def get_enabled_companies() -> list[str]:
	settings = frappe.get_cached_doc("EU Einvoice Settings")
	return [row.company for row in settings.company_settings if row.enabled]


def extend_bootinfo(bootinfo):
	"""Make the enabled companies available to the desk UI as `frappe.boot.eu_einvoice`."""
	bootinfo.eu_einvoice = {"enabled_companies": get_enabled_companies()}
