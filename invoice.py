"""Punto de entrada de compatibilidad: `from invoice import Invoice`.

La implementacion vive en el paquete `ubl_invoice` (ver su __init__.py).
"""
from ubl_invoice import Invoice, InvoiceLineItem, LineCollection, PartyInfo

__all__ = ["Invoice", "InvoiceLineItem", "LineCollection", "PartyInfo"]
