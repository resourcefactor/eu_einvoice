---
title: Setup
order: 10
roles:
  - Accounts User
  - Accounts Manager
  - System Manager
---

## Code Lists

E-invoices use common codes to describe the content of the invoice. For example, "C62" is the UOM "One" and "ZZZ" is a mutually agreed mode of payment.

Common codes belong to a code list. Import the code lists and map the codes you need to the corresponding ERPNext entities. Use the "Import Genericode" button in **Code List**, download the linked XML file first, then upload it from your computer. Importing Genericode directly from a remote URL no longer works in recent ERPNext versions.

Code List | Mapped DocType | Default Value
----------|----------------|--------------
[UNTDID 4461 Payment means code](https://www.xrepository.de/api/xrepository/urn:xoev-de:xrechnung:codeliste:untdid.4461_3:technischerBestandteilGenericode) | Payment Terms Template, Mode of Payment | ZZZ
[Codes for Units of Measure Used in International Trade](https://www.xrepository.de/api/xrepository/urn:xoev-de:kosit:codeliste:rec20_3:technischerBestandteilGenericode) | UOM | C62
[Codes for Passengers, Types of Cargo, Packages and Packaging Materials](https://www.xrepository.de/api/xrepository/urn:xoev-de:kosit:codeliste:rec21_3:technischerBestandteilGenericode) (optional) | UOM | C62
[Codes for Duty Tax and Fee Categories](https://www.xrepository.de/api/xrepository/urn:xoev-de:kosit:codeliste:untdid.5305_3:technischerBestandteilGenericode) | Item Tax Template, Account, Tax Category, Sales Taxes and Charges Template | S
[VAT exemption reason code list](https://www.xrepository.de/api/xrepository/urn:xoev-de:kosit:codeliste:vatex_1:technischerBestandteilGenericode) | Item Tax Template, Account, Tax Category, Sales Taxes and Charges Template | vatex-eu-ae
[Electronic Address Scheme](https://www.xrepository.de/api/xrepository/urn:xoev-de:kosit:codeliste:eas_5:technischerBestandteilGenericode) (Mapping: _as Title_: scheme-name, _as Code_: aesc, _as Description_: remark) | N/A | EM

For example, your standard **Payment Terms Template** is "Bank Transfer, 30 days". Find the suitable **Common Code** for bank transfers in the **Code List** "UNTDID.4461". In this case, the code is "58". Add a row to the _Applies To_ table, select "Payment Terms Template" as the _Link Document Type_ and "Bank Transfer, 30 days" as the _Link Name_. If you now create an Invoice with this **Payment Terms Template**, the eInvoice contains the code "58" for the payment means, signalling that the payment should be done via bank transfer.

The retrieval of codes goes from the most specific to the most general. For example, for the VAT type of a line item, the app first looks for a code using the item's _Item Tax Template_ and _Income Account_, then falls back to the code for the invoice's _Tax Category_ or _Sales Taxes and Charges Template_.

## Buyer Reference (German: Leitweg-ID)

If you work with government customers or similar large organizations, you might need to specify their _Buyer Reference_ in the eInvoice. Set the _Buyer Reference_ field in the **Sales Invoice**. You can already fill this field in the **Customer** master data or the **Sales Order**.

The national terms for this field are:

- Germany: _Leitweg-ID_
- France: _Code Service_

## Electronic Address

If you send your invoice via PEPPOL, you might need to specify your and your customer's electronic addresses. Set the _Electronic Address Scheme_ and _Electronic Address_ fields in the **Company**, **Customer** and **Supplier** master data.

Import the **Electronic Address Scheme** code list first.

If not specified, email addresses are used as electronic addresses for outgoing invoices. For the Customer, the app uses the _Contact Email_ or _Buyer Address_ > _Email ID_. For the Company, the app uses the _Seller Contact_ > _Email ID_ or _Company_ > _Email_.

## Bank Details

If you want your eInvoice to contain bank details, set up a **Mode of Payment** of type "Bank", link the company's corresponding **Account** and create a **Bank Account** for the same account. Select this **Mode of Payment** in your **Payment Terms Template** under _Payment Terms_ -> _Mode of Payment_.

Then map a **Common Code** from **Code List** "UNTDID.4461", for example "Credit Transfer" (30) or "SEPA Credit Transfer" (58), to the **Mode of Payment**.

The eInvoice standard only supports one payment means per invoice, so do not specify multiple **Modes of Payment** in the same invoice.

## EU Einvoice Settings

E-invoicing is configured per company. Add a row for every company that uses e-invoicing to the _Company Settings_ table in **EU Einvoice Settings**. Companies that are not listed (or not enabled) are not affected at all: their Sales Invoices are not validated, get no XML attached, their PDFs stay unchanged and the e-invoicing fields are hidden. E Invoice Imports can only be created for enabled companies.

Per company, you can configure:

- **Enabled**: Turn e-invoicing on or off for the company.
- **Default Profile**: The _E Invoice Profile_ to use when the **Customer** has none.
- **Auto-attach XML on Submit**: Attach the generated XML to the **Sales Invoice** (field _E Invoice XML File_) when it is submitted. The XML is attached even if it does not pass the validation.
- **Validate on Save/Submit**: eInvoice validation can be time-consuming. Enable or disable validation at these stages.
- **Action on Validation Error**: Choose how to handle validation errors:
  - *Empty* (default): No action taken
  - *Warning Message*: Show errors but allow save/submit
  - *Error Message*: Block save/submit and show errors
- **Sales Invoice Number Field**: If you use a separate field for the sales invoice number, configure the field name here.
- **Auto Name Format for XML File**: Pattern for the file name of the downloaded and attached XML, for example `EXAMPLE-.MM.-.{po_no}.-.YYYY`. Leave it empty to use the Sales Invoice ID.
- **Default VAT exemption reason**: Text for BT-120 on VAT breakdowns that carry an exemption reason code.

Use the **Import Code Lists** button to import the bundled EN 16931 code lists.

To attach the XML to Sales Invoices that were submitted earlier, use "..." > "Attach eInvoice XML" in the **Sales Invoice**, or select the invoices in the list view and use _Actions_ > "Attach eInvoice XML". An existing XML file is replaced.
