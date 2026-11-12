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
2. **Facade (`ubl_invoice/facade.py`):** la clase `Invoice` expone una interfaz simple y oculta la
   complejidad de UBL, orquestando las capas de mapeo, serialización y validación.
3. **Arquitectura en capas:** cada responsabilidad vive en su propio módulo y las
   dependencias apuntan hacia el dominio (ver sección 2).

Limitación declarada: el documento cumple el XSD 2.1, pero **no** implementa las reglas
adicionales de SUNAT (RUC, tipo de comprobante, etc.).

## 2. Arquitectura

```mermaid
flowchart TD
    U([Usuario]) --> F["facade.py<br/>Invoice (Facade)"]
    F --> M["mapper.py<br/>InvoiceMapper"]
    F --> S["serializer.py<br/>XmlInvoiceSerializer"]
    F --> V["validator.py<br/>XsdValidator"]
    M --> D["domain.py<br/>InvoiceEntity, PartyInfo, InvoiceLineItem"]
    M --> G["ubl_models.py<br/>clases generadas por xsdata"]
    S --> X[("XML UBL 2.1")]
    V --> XSD[("UBL-Invoice-2.1.xsd")]
    G -. generado desde .-> XSD
```

_Flujo: el usuario habla solo con la fachada; esta orquesta mapeo, serialización y validación. El dominio no conoce a nadie._

| Capa | Módulo | Responsabilidad | Depende de |
|---|---|---|---|
| Fachada | `facade.py` | Interfaz pública `Invoice`; recibe sus colaboradores por parámetro | `ports.py` (y las implementaciones por defecto) |
| Puertos | `ports.py` | Contratos `UblMapper`, `XmlSerializer`, `XmlValidator` | dominio |
| Dominio | `domain.py` | Entidades, reglas de negocio (moneda, fechas, total) | nada externo |
| Mapeo | `mapper.py` | Dominio → clases UBL | dominio, `ubl_models` |
| Serialización | `serializer.py` | Clases UBL → texto XML | xsdata |
| Validación | `validator.py` | XML → conforme al XSD 2.1 | lxml |

### Inyección de dependencias (DIP y Abierto/Cerrado)

`Invoice` no instancia a mano sus colaboradores: depende de los contratos de `ports.py` y
recibe el mapeador, el serializador y el validador por parámetro (opcionales, con
implementaciones por defecto). Así se puede cambiar el formato de salida o la forma de
validar **sin modificar `Invoice`**, y reemplazarlos por dobles de prueba:

```python
class MiValidador:
    def validate(self, xml):
        return ValidationResult(True, [])

factura = Invoice('F001-524', validator=MiValidador())   # sin parámetros usa los de siempre
```

```mermaid
classDiagram
    direction LR
    class UblMapper {
        <<interface>>
        +to_ubl(invoice)
    }
    class XmlSerializer {
        <<interface>>
        +serialize(ubl_invoice) str
    }
    class XmlValidator {
        <<interface>>
        +validate(xml) ValidationResult
    }
    class InvoiceEntity {
        +id
        +currency
        +line
        +total
        +validate()
    }
    class Invoice {
        +gen_xml() str
        +validate_xml() bool
    }
    InvoiceEntity <|-- Invoice
    Invoice o-- UblMapper
    Invoice o-- XmlSerializer
    Invoice o-- XmlValidator
    UblMapper <|.. InvoiceMapper
    XmlSerializer <|.. XmlInvoiceSerializer
    XmlValidator <|.. XsdValidator
```

Una prueba automática (`test_dominio_no_depende_de_infraestructura`) garantiza que el
dominio no importe xsdata, lxml ni las clases generadas.

## 3. Uso

```python
from invoice import Invoice, PartyInfo

factura = Invoice('F001-524')
factura.duedate = '20/02/2020'
factura.line.add
factura.line[0].quantity = 5

factura.currency = 'PEN'                      # moneda ISO 4217 (por defecto PEN)
factura.supplier = PartyInfo('Mi Empresa SAC', '20123456789')   # emisor
factura.customer = PartyInfo('Cliente Demo', '10456789012')     # cliente

xml = factura.genXML()
print(factura.validateXML())   # True si cumple el XSD
```

## 4. Instalación y pruebas

Requiere **Python 3.10 o superior** (las clases generadas usan `dataclass(kw_only=True)`).

```bash
pip install -r requirements.txt
pytest -v
pytest --cov=ubl_invoice --cov-report=term-missing
```

## 5. Estructura

| Ruta | Contenido |
|---|---|
| `invoice.py` | Punto de entrada de compatibilidad (`from invoice import Invoice`) |
| `ubl_invoice/` | Paquete con las capas: `domain`, `ports`, `mapper`, `serializer`, `validator`, `facade` |
| `ubl_models.py` | Clases generadas con xsdata (no editar a mano; ver sección 6) |
| `scripts/regenerar_modelos.py` | Regenera / verifica `ubl_models.py` desde el XSD |
| `xsd/` | Esquemas oficiales UBL 2.1 |
| `test_invoice.py` | Pruebas de generación de XML (extremo a extremo) |
| `test_layers.py` | Pruebas unitarias aisladas por capa |
| `test_injection.py` | Pruebas de inyección de dependencias con dobles de prueba |
| `test_regeneracion.py` | Pruebas del script de regeneración |

## 6. Regenerar los modelos (`ubl_models.py`)

`ubl_models.py` es **código generado** por [xsdata](https://xsdata.readthedocs.io) a partir de
`xsd/maindoc/UBL-Invoice-2.1.xsd`. No se edita a mano. Para reproducirlo:

```bash
python scripts/regenerar_modelos.py           # regenera y sobrescribe ubl_models.py
python scripts/regenerar_modelos.py --check   # solo verifica que esté al día (código de salida 1 si no)
```

- El script genera en una carpeta temporal y copia solo `ubl_models.py`: `xsdata generate`
  deja además un `__init__.py` suelto de ~5 700 líneas que no debe entrar al proyecto.
- Comando equivalente que ejecuta por debajo:
  `xsdata generate <xsd> --package ubl_models --structure-style single-package`
- Verificado con **xsdata 26.10**: la salida es idéntica byte a byte al archivo versionado.
  Otra versión de xsdata puede producir diferencias de formato.
- Prueba opcional (lenta, ~6 s): `REGEN_CHECK=1 pytest test_regeneracion.py`
