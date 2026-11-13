"""Capa de mapeo: dominio -> clases UBL generadas por xsdata (ubl_models)."""
from decimal import Decimal

from xsdata.models.datatype import XmlDate

from ubl_invoice.domain import InvoiceEntity, PartyInfo, TaxGroup, money
from ubl_models import (
    AccountingCustomerParty,
    AccountingSupplierParty,
    Description,
    DocumentCurrencyCode,
    DueDate,
    Id,
    Invoice as UblInvoice,
    InvoiceLine,
    InvoicedQuantity,
    InvoiceTypeCode,
    IssueDate,
    Item,
    LegalMonetaryTotal,
    LineExtensionAmount,
    Name,
    Party,
    PartyIdentification,
    PartyLegalEntity,
    PartyName,
    PayableAmount,
    Percent,
    Price,
    PriceAmount,
    RegistrationName,
    TaxableAmount,
    TaxAmount,
    TaxCategory,
    TaxExclusiveAmount,
    TaxInclusiveAmount,
    TaxScheme,
    TaxSubtotal,
    TaxTotal,
    TaxTypeCode,
    UblversionId,
)

UNIT_CODE = "NIU"
UBL_VERSION = "2.1"
# Esquema de impuesto: IGV (codigos del catalogo peruano) como IVA/VAT.
TAX_SCHEME_ID, TAX_SCHEME_NAME, TAX_TYPE_CODE = "1000", "IGV", "VAT"
CATEGORY_STANDARD, CATEGORY_ZERO = "S", "Z"  # UN/ECE 5305: tasa general / tasa cero


def _xml_date(d) -> XmlDate:
    return XmlDate(d.year, d.month, d.day)


def _party(info: PartyInfo, role_cls):
    """PartyInfo -> rol UBL (Supplier/Customer). Vacio -> rol sin datos."""
    if info.is_empty():
        return role_cls()
    party = Party(
        party_identification=[PartyIdentification(id=Id(value=info.tax_id))] if info.tax_id else [],
        party_name=[PartyName(name=Name(value=info.name))] if info.name else [],
        party_legal_entity=(
            [PartyLegalEntity(registration_name=RegistrationName(value=info.name))]
            if info.name
            else []
        ),
    )
    return role_cls(party=party)


def _price(item, currency):
    """Precio unitario UBL; None si la linea no tiene precio."""
    if item.unit_price is None:
        return None
    return Price(price_amount=PriceAmount(value=item.unit_price, currency_id=currency))


def _tax_subtotal(taxable: float, tax: float, rate: float, currency: str) -> TaxSubtotal:
    return TaxSubtotal(
        taxable_amount=TaxableAmount(value=taxable, currency_id=currency),
        tax_amount=TaxAmount(value=tax, currency_id=currency),
        tax_category=TaxCategory(
            id=Id(value=CATEGORY_STANDARD if rate > 0 else CATEGORY_ZERO),
            percent=Percent(value=Decimal(str(round(rate * 100, 4))).normalize()),
            tax_scheme=TaxScheme(
                id=Id(value=TAX_SCHEME_ID),
                name=Name(value=TAX_SCHEME_NAME),
                tax_type_code=TaxTypeCode(value=TAX_TYPE_CODE),
            ),
        ),
    )


def _tax_total(groups, currency: str) -> TaxTotal:
    """TaxTotal UBL a partir de uno o mas grupos (linea: 1 grupo; factura: uno por tasa)."""
    return TaxTotal(
        tax_amount=TaxAmount(value=money(sum(g.tax for g in groups)), currency_id=currency),
        tax_subtotal=[_tax_subtotal(g.taxable, g.tax, g.rate, currency) for g in groups],
    )


def _line_taxes(invoice: InvoiceEntity, item, currency: str) -> list:
    rate = invoice.rate_for(item)
    if rate is None:
        return []
    group = TaxGroup(rate, item.line_amount, invoice.line_tax(item))
    return [_tax_total([group], currency)]


def _monetary_total(invoice: InvoiceEntity, currency: str) -> LegalMonetaryTotal:
    payable = PayableAmount(value=invoice.total, currency_id=currency)
    if not invoice.is_taxed:
        return LegalMonetaryTotal(payable_amount=payable)
    return LegalMonetaryTotal(
        line_extension_amount=LineExtensionAmount(value=invoice.subtotal, currency_id=currency),
        tax_exclusive_amount=TaxExclusiveAmount(value=invoice.subtotal, currency_id=currency),
        tax_inclusive_amount=TaxInclusiveAmount(value=invoice.total, currency_id=currency),
        payable_amount=payable,
    )


class InvoiceMapper:
    def to_ubl(self, invoice: InvoiceEntity) -> UblInvoice:
        invoice.validate()
        currency = invoice.currency_code
        lines = [
            InvoiceLine(
                id=Id(value=str(i)),
                invoiced_quantity=InvoicedQuantity(value=item.quantity, unit_code=UNIT_CODE),
                line_extension_amount=LineExtensionAmount(value=item.line_amount, currency_id=currency),
                item=Item(description=[Description(value=item.description)]),
                price=_price(item, currency),
                tax_total=_line_taxes(invoice, item, currency),
            )
            for i, item in enumerate(invoice.line, start=1)
        ]
        due = invoice.due_date
        return UblInvoice(
            ublversion_id=UblversionId(value=UBL_VERSION),
            id=Id(value=invoice.id),
            issue_date=IssueDate(value=_xml_date(invoice.issue_date)),
            invoice_type_code=InvoiceTypeCode(value=invoice.document_type),
            due_date=DueDate(value=_xml_date(due)) if due else None,
            document_currency_code=DocumentCurrencyCode(value=currency),
            accounting_supplier_party=_party(invoice.supplier, AccountingSupplierParty),
            accounting_customer_party=_party(invoice.customer, AccountingCustomerParty),
            tax_total=[_tax_total(invoice.tax_breakdown(), currency)] if invoice.is_taxed else [],
            legal_monetary_total=_monetary_total(invoice, currency),
            invoice_line=lines,
        )
