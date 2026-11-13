"""Generador de facturas XML (UBL 2.1).

Capas (la dependencia va siempre hacia el dominio):

    facade.py      Invoice: interfaz publica (Facade); orquesta las demas capas
    domain.py      Entidades y reglas de negocio puras (sin xsdata ni lxml)
    mapper.py      Dominio -> clases UBL generadas (ubl_models)
    serializer.py  Clases UBL -> texto XML (xsdata)
    validator.py   Texto XML -> validacion contra el XSD (lxml)
    storage.py     Texto XML -> archivo fisico (ISO-8859-1)
    encoding.py    Codificacion del XML (compartida por serializador, validador y escritor)
"""
from ubl_invoice.domain import InvoiceLineItem, LineCollection, PartyInfo
from ubl_invoice.facade import Invoice

__all__ = ["Invoice", "InvoiceLineItem", "LineCollection", "PartyInfo"]
