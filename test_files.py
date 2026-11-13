"""Pruebas de generacion del archivo fisico: nombre, codificacion ISO-8859-1 y escritura."""
from pathlib import Path

import pytest
from lxml import etree

from invoice import Invoice, PartyInfo
from ubl_invoice.encoding import XML_ENCODING, declared_encoding, encode_xml
from ubl_invoice.ports import ValidationResult, XmlWriter
from ubl_invoice.storage import XmlFileWriter
from ubl_invoice.validator import DEFAULT_XSD

NS = {"cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"}


def factura(id_="F001-524", ruc="20123456789"):
    f = Invoice(id_)
    f.supplier = PartyInfo("Mi Empresa SAC", ruc)
    f.line.add
    f.line[0].quantity = 1
    f.line[0].amount = 10
    return f


def esquema_valida(path: Path) -> bool:
    schema = etree.XMLSchema(etree.parse(str(DEFAULT_XSD)))
    return schema.validate(etree.parse(str(path)))


# ---- Nombre del archivo: RUC-TIPO-SERIE-NUMERO.xml ----
def test_nombre_de_archivo_ruc_tipo_serie_numero():
    assert factura().file_name == "20123456789-01-F001-524.xml"


def test_nombre_de_archivo_para_boleta():
    f = factura("B001-7")
    f.document_type = "03"
    assert f.file_name == "20123456789-03-B001-7.xml"


@pytest.mark.parametrize("ruc", ["", "123", "1234567890", "2012345678X", "201234567890"])
def test_nombre_exige_ruc_de_11_digitos(ruc):
    with pytest.raises(ValueError, match="RUC"):
        factura(ruc=ruc).file_name


@pytest.mark.parametrize("id_", ["F001524", "f001-1", "F01-1", "F001-123456789", "F001-"])
def test_nombre_exige_formato_serie_numero(id_):
    with pytest.raises(ValueError, match="SERIE-NUMERO"):
        factura(id_).file_name


@pytest.mark.parametrize("tipo", ["07", "08", "99", ""])
def test_tipo_de_documento_invalido(tipo):
    f = factura()
    f.document_type = tipo
    with pytest.raises(ValueError, match="Tipo de documento"):
        f.file_name
    with pytest.raises(ValueError, match="Tipo de documento"):
        f.genXML()


def test_tipo_de_documento_va_tambien_en_el_xml():
    f = factura("B001-1")
    f.document_type = "03"
    root = etree.fromstring(encode_xml(f.genXML()))
    assert root.xpath("//cbc:InvoiceTypeCode/text()", namespaces=NS) == ["03"]


# ---- Codificacion ISO-8859-1 ----
def test_encabezado_declara_iso_8859_1():
    xml = factura().genXML()
    assert xml.startswith('<?xml version="1.0" encoding="ISO-8859-1"?>')
    assert XML_ENCODING == "ISO-8859-1"


def test_declared_encoding_y_encode_xml():
    assert declared_encoding('<?xml version="1.0" encoding="ISO-8859-1"?><a/>') == "ISO-8859-1"
    assert declared_encoding("<a/>") == "UTF-8"                      # sin encabezado
    assert encode_xml('<?xml version="1.0" encoding="ISO-8859-1"?><a>ñ</a>').endswith(b"\xf1</a>")
    assert encode_xml("<a>ñ</a>") == "<a>ñ</a>".encode("utf-8")      # UTF-8 por defecto
    assert b"&#8364;" in encode_xml('<?xml version="1.0" encoding="ISO-8859-1"?><a>€</a>')


def test_validar_no_deforma_las_tildes():
    """El validador debe decodificar con la misma codificacion que declara el XML."""
    f = factura()
    f.line[0].description = "Café ñandú"
    assert f.validateXML() is True, f.last_errors


# ---- save_xml: escritura fisica ----
def test_save_xml_escribe_en_la_carpeta_indicada(tmp_path):
    ruta = factura().save_xml(tmp_path)
    assert ruta == tmp_path / "20123456789-01-F001-524.xml"
    assert ruta.exists() and esquema_valida(ruta)


def test_save_xml_usa_la_carpeta_de_trabajo_por_defecto(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ruta = factura().saveXML()
    assert ruta.parent == tmp_path
    assert [p.name for p in tmp_path.iterdir()] == ["20123456789-01-F001-524.xml"]


def test_save_xml_crea_la_carpeta_si_no_existe(tmp_path):
    destino = tmp_path / "salida" / "xml"
    assert factura().save_xml(destino).parent == destino


def test_archivo_esta_realmente_en_iso_8859_1(tmp_path):
    f = factura()
    f.customer = PartyInfo("Peña & Cía. Ñandú", "10456789012")
    f.line[0].description = "Café € Ł"
    datos = f.save_xml(tmp_path).read_bytes()
    assert datos.startswith(b'<?xml version="1.0" encoding="ISO-8859-1"?>')
    assert b"\xf1" in datos and b"\xe9" in datos           # ñ y é: un byte cada una (latin-1)
    assert b"\xc3\xb1" not in datos                         # no es UTF-8 (ñ serian 2 bytes)
    assert b"&#8364;" in datos and b"&#321;" in datos       # € y Ł no existen en latin-1
    with pytest.raises(UnicodeDecodeError):
        datos.decode("utf-8")


def test_el_archivo_se_lee_de_vuelta_sin_perder_texto(tmp_path):
    f = factura()
    f.line[0].description = "Café ñandú € Ł"
    arbol = etree.parse(str(f.save_xml(tmp_path)))
    assert arbol.xpath("//cbc:Description/text()", namespaces=NS) == ["Café ñandú € Ł"]


def test_no_escribe_nada_si_faltan_datos_del_nombre(tmp_path):
    with pytest.raises(ValueError, match="RUC"):
        factura(ruc="").save_xml(tmp_path)
    assert list(tmp_path.iterdir()) == []


class _Invalido:
    def validate(self, xml):
        return ValidationResult(False, ["error de prueba"])


def test_no_escribe_nada_si_el_xml_no_cumple_el_xsd(tmp_path):
    f = Invoice("F001-1", validator=_Invalido())
    f.supplier = PartyInfo("X", "20123456789")
    f.line.add
    with pytest.raises(ValueError, match="no se escribio"):
        f.save_xml(tmp_path)
    assert list(tmp_path.iterdir()) == []
    assert f.last_errors == ["error de prueba"]


def test_validate_false_omite_la_validacion(tmp_path):
    f = Invoice("F001-1", validator=_Invalido())
    f.supplier = PartyInfo("X", "20123456789")
    f.line.add
    assert f.save_xml(tmp_path, validate=False).exists()


# ---- Inyeccion del escritor ----
class _Escritor:
    def __init__(self):
        self.llamada = None

    def write(self, xml, directory, file_name):
        self.llamada = (xml, directory, file_name)
        return Path("falso") / file_name


def test_escritor_inyectado(tmp_path):
    escritor = _Escritor()
    f = Invoice("F001-524", writer=escritor)
    f.supplier = PartyInfo("X", "20123456789")
    f.line.add
    assert f.save_xml(tmp_path) == Path("falso/20123456789-01-F001-524.xml")
    xml, directorio, nombre = escritor.llamada
    assert xml.startswith("<?xml") and directorio == tmp_path
    assert nombre == "20123456789-01-F001-524.xml"
    assert list(tmp_path.iterdir()) == []                  # el escritor falso no toca el disco


def test_escritor_por_defecto_cumple_el_puerto():
    assert isinstance(XmlFileWriter(), XmlWriter)
