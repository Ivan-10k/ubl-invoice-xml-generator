"""Capa de validacion: XML contra el XSD de UBL 2.1 (lxml)."""
from functools import lru_cache
from pathlib import Path

from lxml import etree

from ubl_invoice.ports import ValidationResult

__all__ = ["DEFAULT_XSD", "ValidationResult", "XsdValidator"]

DEFAULT_XSD = Path(__file__).resolve().parent.parent / "xsd" / "maindoc" / "UBL-Invoice-2.1.xsd"


@lru_cache(maxsize=4)
def _load_schema(path: str) -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(path))


class XsdValidator:
    def __init__(self, xsd_path=DEFAULT_XSD):
        self._xsd_path = str(xsd_path)

    def validate(self, xml: str) -> ValidationResult:
        schema = _load_schema(self._xsd_path)
        doc = etree.fromstring(xml.encode("utf-8"))
        valid = schema.validate(doc)
        return ValidationResult(valid, [str(e) for e in schema.error_log])
