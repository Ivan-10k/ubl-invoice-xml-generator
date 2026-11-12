"""Fachada publica: oculta la complejidad de UBL detras de una interfaz simple."""
from ubl_invoice.domain import InvoiceEntity
from ubl_invoice.mapper import InvoiceMapper
from ubl_invoice.serializer import XmlInvoiceSerializer
from ubl_invoice.validator import DEFAULT_XSD, XsdValidator


class Invoice(InvoiceEntity):
    """Factura con generacion y validacion de XML UBL 2.1."""

    def __init__(self, invoice_id: str):
        super().__init__(invoice_id)
        self.last_errors: list = []

    def gen_xml(self) -> str:
        ubl = InvoiceMapper().to_ubl(self)
        return XmlInvoiceSerializer().serialize(ubl)

    genXML = gen_xml  # nombre usado en clase

    def validate_xml(self, xsd_path=DEFAULT_XSD) -> bool:
        result = XsdValidator(xsd_path).validate(self.gen_xml())
        self.last_errors = result.errors
        return result.valid

    validateXML = validate_xml  # nombre usado en clase
