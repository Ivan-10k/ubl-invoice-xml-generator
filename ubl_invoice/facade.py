"""Fachada publica: oculta la complejidad de UBL detras de una interfaz simple.

`Invoice` depende de los puertos de `ports.py`. Las implementaciones por defecto se
eligen aqui (raiz de composicion) y se pueden reemplazar por parametro:

    Invoice("F001-1", serializer=MiSerializador(), validator=MiValidador())
"""
from pathlib import Path
from typing import Optional

from ubl_invoice.domain import InvoiceEntity
from ubl_invoice.mapper import InvoiceMapper
from ubl_invoice.ports import UblMapper, XmlSerializer, XmlValidator, XmlWriter
from ubl_invoice.serializer import XmlInvoiceSerializer
from ubl_invoice.storage import XmlFileWriter
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
        writer: Optional[XmlWriter] = None,
    ):
        super().__init__(invoice_id)
        self._mapper = mapper if mapper is not None else InvoiceMapper()
        self._serializer = serializer if serializer is not None else XmlInvoiceSerializer()
        self._validator = validator if validator is not None else XsdValidator()
        self._writer = writer if writer is not None else XmlFileWriter()
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

    def save_xml(self, directory=None, validate: bool = True) -> Path:
        """Genera el XML y lo guarda como archivo RUC-TIPO-SERIE-NUMERO.xml (ISO-8859-1).

        `directory`: carpeta destino (por defecto, la carpeta de trabajo actual).
        `validate`: si es True (por defecto) valida contra el XSD y no escribe nada si falla.
        Devuelve la ruta del archivo escrito.
        """
        file_name = self.file_name  # falla antes de generar si faltan RUC o formato de id
        xml = self.gen_xml()
        if validate:
            result = self._validator.validate(xml)
            self.last_errors = result.errors
            if not result.valid:
                detalle = "; ".join(result.errors[:3])
                raise ValueError(f"El XML no cumple el XSD; no se escribio el archivo. {detalle}")
        destino = Path(directory) if directory is not None else Path.cwd()
        return self._writer.write(xml, destino, file_name)

    saveXML = save_xml  # nombre al estilo de genXML / validateXML
