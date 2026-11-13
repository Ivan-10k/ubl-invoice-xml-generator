"""Unit tests for XML generation (UBL Invoice 2.1)."""
import pytest
from lxml import etree

from invoice import Invoice, PartyInfo

NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def parse(xml: str):
    return etree.fromstring(xml.encode("utf-8"))


def text(root, xpath):
    return [e.text for e in root.xpath(xpath, namespaces=NS)]


@pytest.fixture
def factura():
    f = Invoice("F001-524")
    f.duedate = "20/02/2020"
    f.line.add
    f.line[0].quantity = 5
    return f


def test_generacion_basica(factura):
    root = parse(factura.genXML())
    assert root.tag == "{%s}Invoice" % NS["inv"]
    assert text(root, "/inv:Invoice/cbc:ID") == ["F001-524"]
    assert text(root, "//cac:InvoiceLine/cbc:InvoicedQuantity") == ["5"]


def test_fecha_vencimiento_se_convierte_a_iso():
    f = Invoice("F001-1")
    f.issuedate = "2021-01-01"      # distinta de duedate para probar cada campo
    f.duedate = "20/02/2020"
    f.line.add
    root = parse(f.genXML())
    assert text(root, "/inv:Invoice/cbc:IssueDate") == ["2021-01-01"]
    assert text(root, "/inv:Invoice/cbc:DueDate") == ["2020-02-20"]


def test_sin_duedate_no_emite_etiqueta():
    f = Invoice("F001-2")
    f.line.add
    assert text(parse(f.genXML()), "/inv:Invoice/cbc:DueDate") == []


def test_multiples_lineas_y_numeracion():
    f = Invoice("F001-525")
    f.line.add
    f.line[0].quantity = 2
    f.line.add
    f.line[1].quantity = 10
    root = parse(f.genXML())
    assert text(root, "//cac:InvoiceLine/cbc:ID") == ["1", "2"]
    assert text(root, "//cac:InvoiceLine/cbc:InvoicedQuantity") == ["2", "10"]


def test_total_es_suma_de_lineas():
    f = Invoice("F001-3")
    f.line.add
    f.line[0].amount = 100.5
    f.line.add
    f.line[1].amount = 50
    root = parse(f.genXML())
    assert float(text(root, "//cac:LegalMonetaryTotal/cbc:PayableAmount")[0]) == 150.5


@pytest.mark.parametrize("n_lineas", [1, 3])
def test_xml_valido_contra_xsd(n_lineas):
    f = Invoice("F001-524")
    f.duedate = "2020-02-20"
    for _ in range(n_lineas):
        f.line.add
    assert f.validateXML() is True, f.last_errors


def test_caracteres_especiales_se_escapan():
    f = Invoice('F001<&>"x')
    f.line.add
    xml = f.genXML()
    assert "&lt;&amp;&gt;" in xml
    assert text(parse(xml), "/inv:Invoice/cbc:ID") == ['F001<&>"x']


# ---- Casos negativos ----
def test_factura_sin_lineas_falla():
    with pytest.raises(ValueError):
        Invoice("F001-9").genXML()


def test_fecha_invalida_falla():
    f = Invoice("F001-9")
    f.duedate = "31-02-2020"
    f.line.add
    with pytest.raises(ValueError):
        f.genXML()


@pytest.mark.parametrize("bad_id", ["", "   ", None])
def test_id_vacio_falla(bad_id):
    with pytest.raises(ValueError):
        Invoice(bad_id)

# ---- Emisor, cliente, moneda y version UBL ----
def test_emisor_y_cliente_en_el_xml():
    f = Invoice("F001-10")
    f.supplier = PartyInfo("Mi Empresa SAC", "20123456789")
    f.customer = PartyInfo("Cliente Demo", "10456789012")
    f.line.add
    root = parse(f.genXML())
    sup = "//cac:AccountingSupplierParty/cac:Party"
    cus = "//cac:AccountingCustomerParty/cac:Party"
    assert text(root, sup + "/cac:PartyIdentification/cbc:ID") == ["20123456789"]
    assert text(root, sup + "/cac:PartyLegalEntity/cbc:RegistrationName") == ["Mi Empresa SAC"]
    assert text(root, cus + "/cac:PartyName/cbc:Name") == ["Cliente Demo"]
    assert f.validateXML() is True, f.last_errors


def test_moneda_configurable_se_refleja_en_todos_los_importes():
    f = Invoice("F001-11")
    f.currency = "usd"
    f.line.add
    f.line[0].amount = 10
    root = parse(f.genXML())
    assert text(root, "/inv:Invoice/cbc:DocumentCurrencyCode") == ["USD"]
    monedas = root.xpath("//*[@currencyID]/@currencyID", namespaces=NS)
    assert monedas and set(monedas) == {"USD"}
    assert f.validateXML() is True, f.last_errors


@pytest.mark.parametrize("bad", ["", "US", "DOLAR", "12$", None])
def test_moneda_invalida_falla(bad):
    f = Invoice("F001-12")
    f.currency = bad
    f.line.add
    with pytest.raises(ValueError):
        f.genXML()


def test_version_ubl_2_1():
    f = Invoice("F001-13")
    f.line.add
    assert text(parse(f.genXML()), "/inv:Invoice/cbc:UBLVersionID") == ["2.1"]

# ---- Precio unitario ----
def test_importe_se_calcula_con_precio_unitario():
    f = Invoice("F001-20")
    f.line.add
    f.line[0].quantity = 3
    f.line[0].unit_price = 0.1          # 3 x 0.1 debe dar 0.3 (no 0.30000000000000004)
    root = parse(f.genXML())
    assert text(root, "//cac:InvoiceLine/cbc:LineExtensionAmount") == ["0.3"]
    assert text(root, "//cac:InvoiceLine/cac:Price/cbc:PriceAmount") == ["0.1"]
    assert text(root, "//cac:LegalMonetaryTotal/cbc:PayableAmount") == ["0.3"]
    assert f.validateXML() is True, f.last_errors


def test_linea_sin_precio_unitario_no_emite_price():
    f = Invoice("F001-21")
    f.line.add
    f.line[0].amount = 10
    assert text(parse(f.genXML()), "//cac:InvoiceLine/cac:Price/cbc:PriceAmount") == []


def test_total_con_varias_lineas_con_precio():
    f = Invoice("F001-22")
    for cantidad, precio in [(2, 10.5), (4, 2.25)]:
        f.line.add
        f.line[-1].quantity = cantidad
        f.line[-1].unit_price = precio
    root = parse(f.genXML())
    assert float(text(root, "//cac:LegalMonetaryTotal/cbc:PayableAmount")[0]) == 30.0
    assert f.validateXML() is True, f.last_errors


def test_importe_inconsistente_con_precio_falla():
    f = Invoice("F001-23")
    f.line.add
    f.line[0].quantity = 2
    f.line[0].unit_price = 10
    f.line[0].amount = 25               # deberia ser 20
    with pytest.raises(ValueError, match="no coincide"):
        f.genXML()


@pytest.mark.parametrize("campo,valor", [("quantity", -1), ("unit_price", -5)])
def test_valores_negativos_fallan(campo, valor):
    f = Invoice("F001-24")
    f.line.add
    setattr(f.line[0], campo, valor)
    with pytest.raises(ValueError, match="negativ"):
        f.genXML()
