"""Generador de facturas XML (UBL 2.1) sobre las clases generadas por xsdata.

Capas:
  - Dominio  : InvoiceLineItem, LineCollection, Invoice (interfaz para el usuario)
  - Mapeo    : Invoice._to_ubl() (dominio -> clases del XSD)
  - Infra    : _serialize() y validate_xml() (XML + validacion XSD)
"""
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from lxml import etree
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.models.datatype import XmlDate

from ubl_models import (
    AccountingCustomerParty,
    AccountingSupplierParty,
    Description,
    DueDate,
    Id,
    Invoice as UblInvoice,
    InvoiceLine,
    InvoicedQuantity,
    IssueDate,
    Item,
    LegalMonetaryTotal,
    LineExtensionAmount,
    PayableAmount,
)

DEFAULT_XSD = Path(__file__).parent / "xsd" / "maindoc" / "UBL-Invoice-2.1.xsd"
CURRENCY = "PEN"
UNIT_CODE = "NIU"
NS_MAP = {
    None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def _to_xml_date(value: str) -> XmlDate:
    """Convierte 'dd/mm/YYYY' o 'YYYY-mm-dd' a XmlDate. Lanza ValueError si es invalida."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(value, fmt)
            return XmlDate(d.year, d.month, d.day)
        except ValueError:
            continue
    raise ValueError(f"Fecha invalida '{value}'. Use dd/mm/YYYY o YYYY-mm-dd.")


@dataclass
class InvoiceLineItem:
    quantity: float = 0
    description: str = "Producto generico"
    amount: float = 0.0  # importe de la linea (LineExtensionAmount)


class LineCollection(list):
    """Lista de lineas. `factura.line.add` agrega una linea (sintaxis pedida en clase).

    Tambien funciona como `factura.line.add()`, que devuelve la linea creada.
    """

    @property
    def add(self):
        nueva = InvoiceLineItem()
        self.append(nueva)
        return lambda: nueva


class Invoice:
    def __init__(self, invoice_id: str):
        if not invoice_id or not str(invoice_id).strip():
            raise ValueError("El id de la factura no puede estar vacio.")
        self.id = invoice_id
        self.issuedate = "2020-02-20"
        self.duedate = None
        self.line = LineCollection()

    # ---- Mapeo dominio -> clases UBL ----
    def _to_ubl(self) -> UblInvoice:
        if not self.line:
            raise ValueError("La factura necesita al menos una linea (el XSD exige InvoiceLine).")
        lines = [
            InvoiceLine(
                id=Id(value=str(i)),
                invoiced_quantity=InvoicedQuantity(value=item.quantity, unit_code=UNIT_CODE),
                line_extension_amount=LineExtensionAmount(value=item.amount, currency_id=CURRENCY),
                item=Item(description=[Description(value=item.description)]),
            )
            for i, item in enumerate(self.line, start=1)
        ]
        total = sum(item.amount for item in self.line)
        return UblInvoice(
            id=Id(value=self.id),
            issue_date=IssueDate(value=_to_xml_date(self.issuedate)),
            due_date=DueDate(value=_to_xml_date(self.duedate)) if self.duedate else None,
            accounting_supplier_party=AccountingSupplierParty(),
            accounting_customer_party=AccountingCustomerParty(),
            legal_monetary_total=LegalMonetaryTotal(
                payable_amount=PayableAmount(value=total, currency_id=CURRENCY)
            ),
            invoice_line=lines,
        )

    # ---- Infraestructura ----
    @staticmethod
    def _serialize(ubl: UblInvoice) -> str:
        config = SerializerConfig(indent="  ", xml_declaration=True, encoding="UTF-8")
        return XmlSerializer(config=config).render(ubl, ns_map=NS_MAP)

    def gen_xml(self) -> str:
        return self._serialize(self._to_ubl())

    genXML = gen_xml  # nombre usado en clase

    def validate_xml(self, xsd_path=DEFAULT_XSD) -> bool:
        xml_doc = etree.fromstring(self.gen_xml().encode("utf-8"))
        schema = _load_schema(str(xsd_path))
        valid = schema.validate(xml_doc)
        self.last_errors = [str(e) for e in schema.error_log]
        return valid

    validateXML = validate_xml  # nombre usado en clase


@lru_cache(maxsize=4)
def _load_schema(path: str) -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse(path))