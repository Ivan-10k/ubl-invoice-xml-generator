"""Capa de mapeo: dominio -> clases UBL generadas por xsdata (ubl_models)."""
from xsdata.models.datatype import XmlDate

from ubl_invoice.domain import InvoiceEntity, PartyInfo
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
    RegistrationName,
    UblversionId,
)

UNIT_CODE = "NIU"
UBL_VERSION = "2.1"


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


class InvoiceMapper:
    def to_ubl(self, invoice: InvoiceEntity) -> UblInvoice:
        invoice.validate()
        currency = invoice.currency_code
        lines = [
            InvoiceLine(
                id=Id(value=str(i)),
                invoiced_quantity=InvoicedQuantity(value=item.quantity, unit_code=UNIT_CODE),
                line_extension_amount=LineExtensionAmount(value=item.amount, currency_id=currency),
                item=Item(description=[Description(value=item.description)]),
            )
            for i, item in enumerate(invoice.line, start=1)
        ]
        due = invoice.due_date
        return UblInvoice(
            ublversion_id=UblversionId(value=UBL_VERSION),
            id=Id(value=invoice.id),
            issue_date=IssueDate(value=_xml_date(invoice.issue_date)),
            due_date=DueDate(value=_xml_date(due)) if due else None,
            document_currency_code=DocumentCurrencyCode(value=currency),
            accounting_supplier_party=_party(invoice.supplier, AccountingSupplierParty),
            accounting_customer_party=_party(invoice.customer, AccountingCustomerParty),
            legal_monetary_total=LegalMonetaryTotal(
                payable_amount=PayableAmount(value=invoice.total, currency_id=currency)
            ),
            invoice_line=lines,
        )
