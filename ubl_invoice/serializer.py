"""Capa de serializacion: clases UBL -> texto XML (xsdata)."""
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

NS_MAP = {
    None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class XmlInvoiceSerializer:
    def __init__(self, indent: str = "  "):
        config = SerializerConfig(indent=indent, xml_declaration=True, encoding="UTF-8")
        self._serializer = XmlSerializer(config=config)

    def serialize(self, ubl_invoice) -> str:
        return self._serializer.render(ubl_invoice, ns_map=NS_MAP)
