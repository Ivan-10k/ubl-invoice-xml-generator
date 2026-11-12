"""Fachada publica: oculta la complejidad de UBL detras de una interfaz simple.

`Invoice` depende de los puertos de `ports.py`. Las implementaciones por defecto se
eligen aqui (raiz de composicion) y se pueden reemplazar por parametro:

    Invoice("F001-1", serializer=MiSerializador(), validator=MiValidador())
"""
from typing import Optional

from ubl_invoice.domain import InvoiceEntity
from ubl_invoice.mapper import InvoiceMapper
from ubl_invoice.ports import UblMapper, XmlSerializer, XmlValidator
from ubl_invoice.serializer import XmlInvoiceSerializer
from ubl_invoice.validator import XsdValidator


class Invoice(InvoiceEntity):
    """Factura con generacion y validacion de XML UBL 2.1."""

    def __init__(
        self,
        invoice_id: str,
        *,
        mapper: Optional[UblMapper] = None,
        serializer: Optional[XmlSerializer] = None,
        validator: Optional[XmlValidator] = None,
    ):
        super().__init__(invoice_id)
        self._mapper = mapper if mapper is not None else InvoiceMapper()
        self._serializer = serializer if serializer is not None else XmlInvoiceSerializer()
        self._validator = validator if validator is not None else XsdValidator()
        self.last_errors: list = []

    def gen_xml(self) -> str:
        return self._serializer.serialize(self._mapper.to_ubl(self))

    genXML = gen_xml  # nombre usado en clase

    def validate_xml(self, xsd_path=None) -> bool:
        """Valida el XML generado. Con `xsd_path` usa ese XSD en lugar del validador inyectado."""
        validator = XsdValidator(xsd_path) if xsd_path is not None else self._validator
        result = validator.validate(self.gen_xml())
        self.last_errors = result.errors
        return result.valid

    validateXML = validate_xml  # nombre usado en clase
