# XML Electronic Invoice Generator (UBL Invoice 2.1)

**Curso:** Arquitectura de Software  
**Evaluación:** 2do Parcial  
**Autor:** Roger Iván Ochoa Fernández  

---

## 1. Descripción del Caso

### Contexto y Problemática
En los sistemas de planificación de recursos empresariales (ERP como Odoo, SAP u Oracle Fusion) que operan bajo la normativa de facturación electrónica de la SUNAT (Perú), existe la necesidad de emitir comprobantes de pago electrónicos (Facturas) en formato XML basados en el estándar internacional **OASIS UBL 2.1 (`UBL-Invoice-2.1.xsd`)**.

Un antipatrón común en el desarrollo de software es construir estos documentos XML concatenando cadenas de texto o utilizando plantillas estáticas (*hardcoded templates*), lo cual provoca errores de sintaxis, vulnerabilidades de inyección XML, alto acoplamiento y dificultad de mantenimiento frente a actualizaciones del esquema XSD.

### Solución Arquitectónica Implementada
Se diseñó e implementó un componente de generación y validación de XML en **Python** aplicando dos patrones clave:

1. **XML Data Binding (Migración de XSD a Clases):** Se utilizó la herramienta `xsdata` para transformar automáticamente la estructura jerárquica y las reglas del esquema oficial `UBL-Invoice-2.1.xsd` (y sus esquemas comunes `CBC`, `CAC`, `UDT`) en clases de datos nativas de Python (`ubl_models.py`), eliminando por completo el uso de plantillas de texto.
2. **Patrón Adapter / Wrapper (`invoice.py`):** Debido a la alta complejidad del estándar UBL 2.1, se construyó una capa de abstracción orientada a objetos (`class Invoice`) que expone una interfaz limpia y fluida para el desarrollador, encargándose internamente de instanciar las entidades del XSD, serializar el árbol de objetos a XML (`genXML()`) y validarlo contra el esquema oficial (`validateXML()`).

---

## 2. Ejemplo de Uso (Interfaz de Dominio)

```python
from invoice import Invoice

# Instanciación y asignación de propiedades orientadas a objetos
factura = Invoice('F001-524')
factura.duedate = '20/02/2020'
factura.line.add
factura.line[0].quantity = 5

# Serialización desde clases XSD hacia XML
xml_generado = factura.genXML()