"""Codificacion del XML.

Los anexos tecnicos de SUNAT trabajan con ISO-8859-1. El texto XML lleva su
codificacion en el encabezado (<?xml ... encoding="ISO-8859-1"?>) y todo paso que
convierta texto a bytes (validar, escribir el archivo) debe usar ESA misma codificacion,
para que los bytes coincidan con lo que el encabezado promete.
"""
import re

XML_ENCODING = "ISO-8859-1"

_DECLARATION = re.compile(r"""^\s*<\?xml[^>]*?encoding\s*=\s*["']([A-Za-z0-9._-]+)["']""")


def declared_encoding(xml: str) -> str:
    """Codificacion declarada en el encabezado XML (UTF-8 si no declara ninguna)."""
    match = _DECLARATION.match(xml)
    return match.group(1) if match else "UTF-8"


def encode_xml(xml: str) -> bytes:
    """Texto XML -> bytes con la codificacion que declara.

    Un caracter que la codificacion no puede representar (p. ej. el euro en ISO-8859-1)
    se escribe como referencia numerica (&#8364;): sigue siendo XML valido y no se pierde.
    """
    return xml.encode(declared_encoding(xml), errors="xmlcharrefreplace")
