"""Pruebas por capa: cada modulo se prueba de forma aislada."""
import ast
from pathlib import Path

import pytest

from ubl_invoice.domain import InvoiceEntity, PartyInfo, parse_date
from ubl_invoice.mapper import InvoiceMapper
from ubl_invoice.serializer import XmlInvoiceSerializer
from ubl_invoice.validator import XsdValidator

PKG = Path(__file__).parent / "ubl_invoice"


def factura_valida() -> InvoiceEntity:
    f = InvoiceEntity("F001-1")
    f.line.add
    f.line[0].quantity = 2
    f.line[0].amount = 30
    return f


# ---- Dominio (sin xsdata ni lxml) ----
def test_dominio_no_depende_de_infraestructura():
    """Regla arquitectonica: domain.py no importa xsdata, lxml ni ubl_models."""
    tree = ast.parse((PKG / "domain.py").read_text(encoding="utf-8"))
    importados = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            importados |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            importados.add((node.module or "").split(".")[0])
    assert not importados & {"xsdata", "lxml", "ubl_models", "ubl_invoice"}


def test_total_suma_lineas():
    f = factura_valida()
    f.line.add
    f.line[1].amount = 12.5
    assert f.total == 42.5


@pytest.mark.parametrize("valor", ["20/02/2020", "2020-02-20"])
def test_parse_date_formatos_validos(valor):
    assert parse_date(valor).isoformat() == "2020-02-20"


@pytest.mark.parametrize("valor", ["31-02-2020", "", "hoy", None])
def test_parse_date_invalida(valor):
    with pytest.raises(ValueError):
        parse_date(valor)


def test_moneda_se_normaliza_a_mayusculas():
    f = factura_valida()
    f.currency = "eur"
    assert f.currency_code == "EUR"


def test_validate_exige_lineas():
    with pytest.raises(ValueError):
        InvoiceEntity("F001-2").validate()


def test_partyinfo_vacio():
    assert PartyInfo().is_empty()
    assert not PartyInfo("X").is_empty()


# ---- Mapeo ----
def test_mapper_produce_clase_ubl():
    ubl = InvoiceMapper().to_ubl(factura_valida())
    assert ubl.id.value == "F001-1"
    assert len(ubl.invoice_line) == 1
    assert ubl.legal_monetary_total.payable_amount.value == 30


def test_mapper_rechaza_factura_invalida():
    with pytest.raises(ValueError):
        InvoiceMapper().to_ubl(InvoiceEntity("F001-3"))


# ---- Serializacion ----
def test_serializer_emite_xml_con_prefijos_ubl():
    xml = XmlInvoiceSerializer().serialize(InvoiceMapper().to_ubl(factura_valida()))
    assert xml.startswith("<?xml")
    assert "<cbc:ID>F001-1</cbc:ID>" in xml


# ---- Validacion ----
def test_validator_acepta_xml_valido():
    xml = XmlInvoiceSerializer().serialize(InvoiceMapper().to_ubl(factura_valida()))
    resultado = XsdValidator().validate(xml)
    assert resultado and resultado.errors == []


def test_validator_rechaza_xml_que_no_cumple_xsd():
    xml_malo = (
        '<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">'
        "<Basura/></Invoice>"
    )
    resultado = XsdValidator().validate(xml_malo)
    assert not resultado
    assert resultado.errors


# ---- Dominio: linea con precio unitario ----
def test_line_amount_prioridad_y_calculo():
    from ubl_invoice.domain import InvoiceLineItem

    assert InvoiceLineItem().line_amount == 0.0                                   # sin datos
    assert InvoiceLineItem(quantity=3, unit_price=0.1).line_amount == 0.3         # calculado y redondeado
    assert InvoiceLineItem(quantity=3, amount=50).line_amount == 50               # manual
    assert InvoiceLineItem(quantity=2, unit_price=10, amount=20).line_amount == 20  # consistente


def test_total_redondea_a_dos_decimales():
    f = InvoiceEntity("F001-30")
    for _ in range(3):
        f.line.add
        f.line[-1].quantity = 1
        f.line[-1].unit_price = 0.1
    assert f.total == 0.3
