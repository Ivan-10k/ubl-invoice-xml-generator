"""Pruebas de inyeccion de dependencias: Invoice usa los puertos, no clases concretas."""
from ubl_invoice import Invoice
from ubl_invoice.mapper import InvoiceMapper
from ubl_invoice.ports import UblMapper, ValidationResult, XmlSerializer, XmlValidator
from ubl_invoice.serializer import XmlInvoiceSerializer
from ubl_invoice.validator import DEFAULT_XSD, XsdValidator


class FakeMapper:
    def __init__(self):
        self.recibido = None

    def to_ubl(self, invoice):
        self.recibido = invoice
        return "OBJETO-UBL"


class FakeSerializer:
    def __init__(self):
        self.recibido = None

    def serialize(self, ubl_invoice):
        self.recibido = ubl_invoice
        return "<fake/>"


class FakeValidator:
    def __init__(self, resultado):
        self.resultado = resultado
        self.recibido = None

    def validate(self, xml):
        self.recibido = xml
        return self.resultado


def test_implementaciones_por_defecto_cumplen_los_puertos():
    assert isinstance(InvoiceMapper(), UblMapper)
    assert isinstance(XmlInvoiceSerializer(), XmlSerializer)
    assert isinstance(XsdValidator(), XmlValidator)


def test_gen_xml_orquesta_mapper_y_serializer_inyectados():
    mapper, serializer = FakeMapper(), FakeSerializer()
    f = Invoice("F001-1", mapper=mapper, serializer=serializer)
    assert f.gen_xml() == "<fake/>"
    assert mapper.recibido is f                  # el mapper recibe la factura
    assert serializer.recibido == "OBJETO-UBL"   # el serializer recibe lo que devolvio el mapper


def test_validate_xml_usa_el_validador_inyectado():
    validador = FakeValidator(ValidationResult(False, ["boom"]))
    f = Invoice("F001-1", mapper=FakeMapper(), serializer=FakeSerializer(), validator=validador)
    assert f.validate_xml() is False
    assert validador.recibido == "<fake/>"       # valida el texto producido por el serializer
    assert f.last_errors == ["boom"]


def test_validate_xml_con_xsd_explicito_ignora_el_validador_inyectado():
    validador = FakeValidator(ValidationResult(False, ["no deberia usarse"]))
    f = Invoice("F001-1", validator=validador)
    f.line.add
    assert f.validate_xml(DEFAULT_XSD) is True
    assert validador.recibido is None


def test_serializador_alternativo_sin_modificar_invoice():
    """Abierto/Cerrado: un serializador distinto se enchufa sin tocar Invoice."""

    class SerializadorEnMayusculas:
        def serialize(self, ubl_invoice):
            return XmlInvoiceSerializer().serialize(ubl_invoice).upper()

    f = Invoice("f001-1", serializer=SerializadorEnMayusculas())
    f.line.add
    assert "<CBC:ID>F001-1</CBC:ID>" in f.gen_xml()


def test_sin_inyeccion_el_comportamiento_es_el_de_siempre():
    f = Invoice("F001-1")
    f.line.add
    assert f.validate_xml() is True, f.last_errors
