from datetime import datetime
from lxml import etree
from xsdata.models.datatype import XmlDate
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from ubl_models import (
    Invoice as UblInvoice,
    InvoiceLine,
    Item,
    Id,
    IssueDate,
    DueDate,
    InvoicedQuantity,
    LineExtensionAmount,
    PayableAmount,
    Description,
    AccountingSupplierParty,
    AccountingCustomerParty,
    LegalMonetaryTotal,
)


# --- Función auxiliar para convertir '20/02/2020' o '2020-02-20' a XmlDate ---
def _to_xml_date(fecha_str: str) -> XmlDate:
    if "/" in fecha_str:
        dt = datetime.strptime(fecha_str, "%d/%m/%Y")
    else:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    return XmlDate(dt.year, dt.month, dt.day)


# --- CLASE 1: Representa cada renglón de la factura (factura.line[0]) ---
class InvoiceLineItem:
    def __init__(self):
        self.quantity = 0
        self.description = "Producto generico"
        self.amount = 0.0


# --- CLASE 2: Lista personalizada para que funcione "factura.line.add" ---
class LineCollection(list):
    @property
    def add(self):
        nuevo_renglon = InvoiceLineItem()
        self.append(nuevo_renglon)
        return self._call_dummy

    def _call_dummy(self):
        pass


# --- CLASE 3: La clase principal que pide el profesor ---
class Invoice:
    def __init__(self, invoice_id: str):
        self.id = invoice_id
        self.duedate = None
        self.issuedate = "2020-02-20"
        self.line = LineCollection()

    def genXML(self) -> str:
        # 1. Aseguramos que siempre haya al menos 1 línea (el XSD de UBL 2.1 exige mínimo 1 InvoiceLine)
        lineas_fuente = self.line if len(self.line) > 0 else [InvoiceLineItem()]

        ubl_lines = []
        for index, item in enumerate(lineas_fuente, start=1):
            ubl_line = InvoiceLine(
                id=Id(value=str(index)),
                invoiced_quantity=InvoicedQuantity(
                    value=item.quantity,
                    unit_code="NIU"
                ),
                line_extension_amount=LineExtensionAmount(
                    value=item.amount,
                    currency_id="PEN"
                ),
                item=Item(
                    description=[Description(value=item.description)]
                )
            )
            ubl_lines.append(ubl_line)

        # 2. Instanciamos la clase raíz del XSD con tipos XmlDate válidos
        ubl_root = UblInvoice(
            id=Id(value=self.id),
            issue_date=IssueDate(value=_to_xml_date(self.issuedate)),
            due_date=DueDate(value=_to_xml_date(self.duedate)) if self.duedate else None,
            accounting_supplier_party=AccountingSupplierParty(),
            accounting_customer_party=AccountingCustomerParty(),
            legal_monetary_total=LegalMonetaryTotal(
                payable_amount=PayableAmount(value=0.0, currency_id="PEN")
            ),
            invoice_line=ubl_lines
        )

        # 3. Serializamos el objeto a texto XML
        config = SerializerConfig(indent="  ", xml_declaration=True, encoding="UTF-8")
        serializer = XmlSerializer(config=config)
        return serializer.render(ubl_root)

    def validateXML(self, xsd_path: str = "xsd/maindoc/UBL-Invoice-2.1.xsd") -> bool:
        xml_str = self.genXML()
        xml_doc = etree.fromstring(xml_str.encode("utf-8"))
        schema = etree.XMLSchema(etree.parse(xsd_path))
        es_valido = schema.validate(xml_doc)
        if not es_valido:
            print("\nDetalle de validación XSD:", schema.error_log)
        return es_valido2026-11-03 14:25:31.852 [error] [Window] [Extension Host] Electronic Invoicing Document d:\sistema\invoice.py not found in AST tracker2026-11-03 14:25:33.821 [error] [Window] [Extension Host] Encountered UnhandledRejection: Error: No autocomplete model configured and provided model not found in config2026-11-03 14:25:34.817 [error] [Window] Error: No autocomplete model configured and provided model not found in config