# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

- **Frappe app**: `eu_einvoice` ("European e-Invoice", by ALYF GmbH). It converts between ERPNext documents and UN/CEFACT CII e-invoice XML in the profiles BASIC, EN 16931, EXTENDED and XRECHNUNG, and embeds the XML in PDFs (ZUGFeRD / Factur-X). It does **not** handle UBL or transport (Peppol etc.).
- **Repo**: branch `version-15` of the `resourcefactor/eu_einvoice` fork (the git remote is named `upstream`), which regularly merges `alyf-de/eu_einvoice` `version-15`. The fork's own changes are described under "Fork changes" below.
- **Requires** frappe `>=15.117,<16` and erpnext `>=15.121.4,<16` (ERPNext's `Code List` / `Common Code` doctypes and its genericode import in `erpnext.edi`), plus `drafthorse~=2025.2` and `lxml>=6.1`. Older drafthorse versions fail when building the XML (read-only notes, single payment means).
- **Python deps**: `drafthorse` (build/parse CII XML, attach XML to PDF), `factur-x` (extract XML from PDF), `saxonche` (XSLT for schematron), `lxml`.
- **User docs** live in `eu_einvoice/docs/en/eu_einvoice/*.md` (served in Desk by the Compendium app); the README only links to them.
- **Bench root**: `/home/erp/frappe-bench15`. The app is installed on the dev site `netsdemo` (19 companies; only NETS INTERNATIONAL GMBH and NETS International I.K.E use e-invoicing, the Saudi company uses `zatca_erpgulf`).
- **Developer mode is off** on netsdemo: DocTypes, Reports, Number Cards and Dashboard Charts are edited as JSON files and synced with `migrate`. Bump `modified` in the JSON, or the sync skips the file.

## Commands

Run from `/home/erp/frappe-bench15`, always with an explicit `--site`:

```bash
bench --site <site> install-app eu_einvoice
bench --site <site> migrate        # after .json doctype edits or custom_fields.py edits (see below)
bench --site <site> clear-cache    # after Python/JS edits
bench build --app eu_einvoice

# Tests (needs `allow_tests`; the skip flags keep other apps' before_tests hooks from changing site data)
bench --site <site> run-tests --app eu_einvoice --skip-before-tests --skip-test-records
bench --site <site> run-tests --module eu_einvoice.european_e_invoice.custom.test_sales_invoice_multi_company --skip-before-tests --skip-test-records

# Translations (eu_einvoice/locale/main.pot, de.po)
bench generate-pot-file --app eu_einvoice
bench compile-po-to-mo --app eu_einvoice
```

Linting uses pre-commit (ruff lint + format, prettier, eslint, commitlint). Run it from the app directory with `pre-commit run --all-files`. Python style is tabs, double quotes, line length 110, target py310. Commit messages must follow Conventional Commits (`feat:`, `fix:`, `chore:` …). PR CI also runs the Frappe Semgrep rules and `pip-audit`. The CI workflow only installs the app; its test step is commented out.

**Tests**: use `FrappeTestCase` from `frappe.tests.utils`; `frappe.tests.IntegrationTestCase` does not exist in Frappe v15. The fork's multi-company tests (`test_sales_invoice_multi_company.py`, `TestEInvoiceImportCompany`, settings and report tests) mock `get_company_settings` / `get_enabled_companies` and don't write to the database. Upstream's tests in `custom/test_sales_invoice.py` and `test_e_invoice_import.py` partly need ERPNext test records (`_Test Company`, `_Test Customer`), so they only pass on a test site. Note that `frappe.new_doc` pre-fills Link fields such as `company` with the user's default.

## Architecture

### Multi-company: e-invoicing is enabled per company

**EU Einvoice Settings** (single) holds a child table `company_settings` (**E Invoice Company Settings**): company, enabled, default profile, auto-attach XML on submit, validate on save/submit, error actions, Sales Invoice number field, auto name format for the XML file, default VAT exemption reason (BT-120). The settings form also has upstream's "Import Code Lists" button. A company without an enabled row has e-invoicing switched off completely. The DocType was renamed from "E Invoice Settings" (patch `rename_einvoice_settings`, pre_model_sync) so it can't be confused with other regions' e-invoicing apps on the same bench, such as `zatca_erpgulf`.

- `eu_einvoice/company_settings.py` is the only place that resolves this: `get_company_settings(company)` (row or `None`), `is_einvoice_enabled()`, `get_enabled_companies()`. It reads `frappe.get_cached_doc("EU Einvoice Settings")`.
- Every entry point checks the company: `validate_doc`, `attach_xml_on_submit`, `attach_xml_to_pdf` / `download_pdf`, `download_xrechnung`, `attach_einvoice_xml`, E Invoice Import (`before_validate`, `validate`, `guess_company`, `create_einvoice_from_po`). Per-company values are read through `get_company_settings` (e.g. `EInvoiceGenerator.create_einvoice` for the VAT exemption text, `get_xml_attachment_file_base_name` for the file name pattern). New features need the same check.
- `extend_bootinfo` puts the enabled companies into `frappe.boot.eu_einvoice.enabled_companies`. In JS, use `eu_einvoice.utils.is_enabled_for(company)` / `get_enabled_companies()` (`public/js/utils.js`). The Sales Invoice E Invoicing tab and Buyer Reference use it in their `depends_on`. Users only see changed settings after a page reload.
- Customers are shared between companies and default to the profile `EXTENDED`. For a disabled company `validate_doc` clears the profile fetched from the Customer. For an enabled company, the Customer's profile wins over the company's default profile.

### Outgoing: Sales Invoice → XML / PDF

Everything is in `eu_einvoice/european_e_invoice/custom/sales_invoice.py`.

- **`get_einvoice(invoice)`** loads the Company, Customer, addresses and contacts. `EInvoiceGenerator` maps the ERPNext fields onto a drafthorse `Document`, which is then serialized with the drafthorse schema for the invoice's `einvoice_profile`.
- **Generation hooks**: `get_einvoice` calls `invoice.run_method("before_einvoice_generation")` and `("after_einvoice_generation", doc)`.
  - These are public extension points. Other apps hook them through `doc_events` (see README).
  - They also fire during `validate`, so any change a hook makes to the invoice is saved.
- **`validate_doc`** (doc_event `validate`):
  - Shows alerts for unsupported features: "On Item Quantity" taxes, more than one mode of payment, and document-level discounts.
  - Depending on the company's settings, it then builds the XML and validates it against the schematron, filling `einvoice_is_correct`, `validation_errors` and `validation_warnings` on the invoice.
  - The XML bytes are cached on `doc._einvoice_xml_bytes`. `attach_xml_on_submit` (doc_event `on_submit`) reuses them when the company has `auto_attach_xml` set. It attaches for every profile, also when validation failed, and stores the URL in the read-only field `einvoice_xml_file`. That dedicated field is how reports tell e-invoice XMLs apart from other attached XMLs, such as ZATCA's.
  - `attach_einvoice_xml(invoice_names)` is the manual / list view action. It replaces the existing file and is enqueued for more than 20 invoices.
- **`download_pdf`** overrides `frappe.utils.print_format.download_pdf` through `override_whitelisted_methods`. It calls Frappe's own implementation, then for Sales Invoices of enabled companies (all others are returned untouched):
  - converts the PDF to PDF/A-3 with Ghostscript (`gs`, which must find `srgb.icc`; on failure it logs and continues);
  - embeds the XML with `drafthorse.pdf.attach_xml` (never for XRECHNUNG).
  
  Any exception falls back to the plain PDF. Another app that overrides the same method will conflict with this one.
- **`download_xrechnung`** is the whitelisted endpoint behind the "Download eInvoice" menu item (`custom/sales_invoice.js`).

### Profiles (`eu_einvoice/utils.py`)

`EInvoiceProfile` is a totally ordered enum: `BASIC < EN16931 < XRECHNUNG < EXTENDED`. The generator gates features with these comparisons, so `>= EXTENDED` excludes XRECHNUNG. Each profile maps to:

- a drafthorse schema (`PROFILE_TO_SCHEMA`). XRECHNUNG serializes with the EN16931 schema.
- a guideline URN (`PROFILE_TO_GUIDELINE`). Imports reverse this mapping to detect an incoming file's profile.
- a schematron XSL (`PROFILE_TO_XSL` in `schematron/__init__.py`). XRECHNUNG validation also runs the EN16931 rules.

The values of the `einvoice_profile` Select field are the enum values. Note that EN 16931 is stored as `"EN 16931"`, with a space.

### Schematron validation (`eu_einvoice/schematron/`)

- The `.xsl` files are compiled from the official `.sch` sources and checked in. To regenerate them, follow `schematron/README.md`; don't edit them by hand.
- Validation runs them with SaxonC. SVRL `failed-assert` entries become errors and `successful-report` entries become warnings.
- Validation is slow, which is why EU Einvoice Settings can switch it off for save and for submit.

### Common codes (`eu_einvoice/common_codes.py`)

Some XML values are codes from standard code lists: UOM (`C62`), payment means (`ZZZ`, `58`), VAT category (`S`) and VAT exemption reason. Users import these lists as ERPNext **Code List** / **Common Code** records and map codes to ERPNext records.

`CommonCodeRetriever(code_list_uris, fallback).get([(doctype, name), ...])` resolves a code in this order:

1. the given records, from most to least specific;
2. the code list's default code;
3. the hard-coded fallback.

Code lists are identified by canonical URI, for example `urn:xoev-de:kosit:codeliste:rec20`. The module-level retrievers are at the top of `sales_invoice.py`. The EN 16931 code lists are bundled in `eu_einvoice/codelist/*.gc` and imported by `install.import_code_lists()`.

### Incoming: E Invoice Import → Purchase Invoice

The code is in `doctype/e_invoice_import/e_invoice_import.py`; the doctype is submittable.

- **`before_save`** runs when the `einvoice` attachment changes:
  - extracts the XML, using `facturx.get_xml_from_pdf` for PDFs;
  - parses it with drafthorse (`strict=False`) and detects the profile from the guideline URN;
  - runs schematron validation. Errors are shown but don't block the import.
  - fills the child tables (`E Invoice Item`, `E Invoice Trade Tax`, `E Invoice Payment Term`);
  - guesses the supplier, company, UOM, item and PO links. `guess_company` only picks enabled companies; `before_validate` drops a non-enabled company on new imports (usually the user's default company).
- **On submit**: a supplier, a company and an Item for every line are required. Seller product IDs are then written back to the Items.
- **Whitelisted mappers** (`create_purchase_invoice`, `create_supplier`, `create_supplier_address`, `create_item`, …) use `get_mapped_doc`. Taxes become "Actual" charges so ERPNext does not recalculate them.

### Custom fields are defined in code, not fixtures

- `eu_einvoice/custom_fields.py` defines all custom fields on Sales Invoice, Sales Order, Purchase Invoice, Customer, Supplier and Company. Don't export them with `export-fixtures`.
- `install.make_custom_fields()` creates them (`after_install` also imports the bundled code lists from `eu_einvoice/codelist/`). `patches.txt` re-runs it as `execute:from eu_einvoice.install import make_custom_fields; make_custom_fields() # 20`.
- **After changing `custom_fields.py`, bump that trailing number** so the patch runs again on the next `migrate`.
- In that file, `_` is a no-op (`utils.identity`). Labels are still extracted for translation but aren't translated at install time.

### Reports and dashboard

- Script Reports in `european_e_invoice/report/`: **E Invoice Status** (Sales Invoices of enabled companies, status Valid / Invalid / Not Validated / Not E-Invoiced, XML attached) and **E Invoice Import Register**. Both read through `frappe.get_list`, so user permissions (for example on Company) apply.
- Standard Number Cards (`european_e_invoice/number_card/`) and Dashboard Charts (`european_e_invoice/dashboard_chart/`) are shown on the **E-Invoicing** workspace. They are synced by `migrate` (`frappe.utils.dashboard.sync_dashboards`). They filter on `einvoice_profile is set`, which only invoices of enabled companies have. The "E-Invoice Status" chart uses the report chart; its colors come from the chart's `custom_options` and depend on `get_chart` always returning all four statuses in the same order.

### Other pieces

- `switzerland.py` normalizes Swiss UID VAT IDs and checks their checksum. It's used for the buyer tax ID. Other VAT IDs go through `validate_vat_id` in `sales_invoice.py`, with scheme `VA` if valid and `FC` otherwise.
- `jinja.py` provides `get_einvoice_logo(profile)` for Print Formats. It returns a base64 Factur-X logo.
- **Global JS** (`app_include_js`): `public/js/utils.js` (`eu_einvoice.utils`) and `public/js/queries.js` (`eu_einvoice.queries`). Per-doctype JS lives in `european_e_invoice/custom/*.js` and is registered under `doctype_js`. `custom/sales_invoice_list.js` (`doctype_list_js`) wraps the existing `listview_settings` `onload` instead of replacing it, because ERPNext and `zatca_erpgulf` extend the same list view.
- `export_python_type_annotations = True` is set, so saving a DocType in developer mode rewrites the `# begin/end: auto-generated types` blocks in its controller. Don't edit those blocks by hand.

## Fork changes (keep in mind when merging upstream)

These parts differ from `alyf-de/eu_einvoice` and are the usual merge conflicts:

- Upstream's `e_invoice_settings/` folder is renamed to `eu_einvoice_settings/` here. Upstream changes to the settings must be carried over by hand, and global settings fields usually belong in **E Invoice Company Settings** (per company).
- `custom/sales_invoice.py`: company gating in `validate_doc`, `attach_xml_on_submit`, `download_xrechnung`, `attach_xml_to_pdf`; `_attach_xml_file` always uses the `einvoice_xml_file` field (upstream's "attach field" option was dropped); per-company reads replace `frappe.db.get_single_value("E Invoice Settings", ...)`.
- `custom/test_sales_invoice.py` (upstream) patches `get_company_settings` in `TestNotSubjectToVatInvoice` and `TestXmlAttachmentNaming`; the fork's own tests are in `test_sales_invoice_multi_company.py`.
- `e_invoice_import.py`: company checks; `test_e_invoice_import.py`: extra class `TestEInvoiceImportCompany` at the end.
- `patches.txt`: `rename_einvoice_settings` (pre_model_sync), `move_settings_to_company_table`, and the custom fields line bumped to `# 20`.
