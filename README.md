# XML Electronic Invoice Generator (UBL Invoice 2.1)

**Curso:** Arquitectura de Software — 2do Parcial
**Autor:** Roger Iván Ochoa Fernández

## 1. Descripción del caso

Los sistemas ERP necesitan emitir facturas electrónicas en XML según el estándar
**OASIS UBL 2.1** (`UBL-Invoice-2.1.xsd`). Un antipatrón común es construir el XML
concatenando cadenas o con plantillas fijas: produce errores de sintaxis, riesgo de
inyección XML, alto acoplamiento y dificultad para seguir cambios del esquema.

### Solución
1. **XML Data Binding:** `xsdata` genera clases Python (`ubl_models.py`) desde los XSD
   oficiales (carpeta `xsd/`). El XML se obtiene serializando objetos, sin plantillas.
   El escape de caracteres especiales lo hace el serializador (hay una prueba que lo verifica).
2. **Facade (`invoice.py`):** la clase `Invoice` expone una interfaz simple y oculta la
   complejidad de UBL: mapea el dominio a las clases del XSD, serializa y valida contra el XSD.

Limitación declarada: el documento cumple el XSD 2.1, pero **no** implementa las reglas
adicionales de SUNAT (RUC, tipo de comprobante, etc.).

## 2. Arquitectura

```
Usuario ──> Invoice (Facade/dominio) ──> _to_ubl() (mapeo) ──> ubl_models.py (clases del XSD)
                                      └─> XmlSerializer (xsdata) ──> XML
                                      └─> validate_xml() (lxml + XSD)
```

## 3. Uso

```python
from invoice import Invoice

factura = Invoice('F001-524')
factura.duedate = '20/02/2020'
factura.line.add
factura.line[0].quantity = 5

xml = factura.genXML()
print(factura.validateXML())   # True si cumple el XSD
```

## 4. Instalación y pruebas

```bash
pip install -r requirements.txt
pytest -v
pytest --cov=invoice --cov-report=term-missing
```

## 5. Estructura

| Ruta | Contenido |
|---|---|
| `invoice.py` | Fachada, mapeo, serialización y validación |
| `ubl_models.py` | Clases generadas con xsdata (no editar a mano) |
| `xsd/` | Esquemas oficiales UBL 2.1 |
| `test_invoice.py` | Pruebas unitarias de generación |