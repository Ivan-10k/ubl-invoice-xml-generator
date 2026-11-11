import xml.etree.ElementTree as ET
from invoice import Invoice

def test_generacion_basica_pizarra():
    """Prueba unitaria exacta con el código de la imagen de clase"""
    factura = Invoice('F001-524')
    factura.duedate = '20/02/2020'
    factura.line.add
    factura.line[0].quantity = 5

    xml_str = factura.genXML()

    # 1. Verifica que devuelva contenido y sea un XML con formato válido
    assert xml_str is not None
    root = ET.fromstring(xml_str.encode('utf-8'))
    assert root is not None

    # 2. Verifica que los datos asignados estén dentro de las etiquetas XML
    assert 'F001-524' in xml_str
    assert '2020-02-20' in xml_str
    assert '>5<' in xml_str

def test_multiples_lineas_factura():
    """Prueba unitaria agregando más de un ítem a la factura"""
    factura = Invoice('F001-525')
    factura.line.add
    factura.line[0].quantity = 2
    factura.line.add
    factura.line[1].quantity = 10

    xml_str = factura.genXML()

    assert 'F001-525' in xml_str
    assert '>2<' in xml_str
    assert '>10<' in xml_str
    
def test_validation_contra_xsd():
    """Verifica que el XML generado cumple 100% con el archivo XSD oficial"""
    factura = Invoice('F001-524')
    factura.duedate = '2020-02-20' # Formato estándar XSD YYYY-MM-DD
    factura.line.add
    factura.line[0].quantity = 5

    assert factura.validateXML() is True
    
