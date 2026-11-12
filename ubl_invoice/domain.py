"""Capa de dominio: entidades y reglas de negocio.

No depende de xsdata, lxml ni de las clases generadas: se puede probar y
reutilizar sin conocer UBL.
"""
from dataclasses import dataclass
from datetime import date, datetime

DEFAULT_CURRENCY = "PEN"
_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def parse_date(value: str) -> date:
    """Convierte 'dd/mm/YYYY' o 'YYYY-mm-dd' a date. Lanza ValueError si es invalida."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    raise ValueError(f"Fecha invalida '{value}'. Use dd/mm/YYYY o YYYY-mm-dd.")


@dataclass
class InvoiceLineItem:
    quantity: float = 0
    description: str = "Producto generico"
    amount: float = 0.0  # importe de la linea (LineExtensionAmount)


@dataclass
class PartyInfo:
    """Datos de una parte de la factura (emisor o cliente)."""

    name: str = ""
    tax_id: str = ""  # RUC / NIT / identificador fiscal

    def is_empty(self) -> bool:
        return not (self.name or self.tax_id)


class LineCollection(list):
    """Lista de lineas. `factura.line.add` agrega una linea (sintaxis pedida en clase).

    Tambien funciona como `factura.line.add()`, que devuelve la linea creada.
    """

    @property
    def add(self):
        nueva = InvoiceLineItem()
        self.append(nueva)
        return lambda: nueva


class InvoiceEntity:
    """Datos y reglas de una factura, independientes del formato de salida."""

    def __init__(self, invoice_id: str):
        if not invoice_id or not str(invoice_id).strip():
            raise ValueError("El id de la factura no puede estar vacio.")
        self.id = invoice_id
        self.issuedate = "2020-02-20"
        self.duedate = None
        self.currency = DEFAULT_CURRENCY  # codigo ISO 4217 (PEN, USD, ...)
        self.supplier = PartyInfo()
        self.customer = PartyInfo()
        self.line = LineCollection()

    @property
    def currency_code(self) -> str:
        """Moneda normalizada en mayusculas; ValueError si no es un codigo de 3 letras."""
        c = self.currency
        if not (isinstance(c, str) and len(c) == 3 and c.isalpha()):
            raise ValueError(f"Moneda invalida '{c}'. Use codigo ISO 4217 (PEN, USD, EUR...).")
        return c.upper()

    @property
    def issue_date(self) -> date:
        return parse_date(self.issuedate)

    @property
    def due_date(self):
        return parse_date(self.duedate) if self.duedate else None

    @property
    def total(self) -> float:
        return sum(item.amount for item in self.line)

    def validate(self) -> None:
        """Reglas de negocio. Lanza ValueError si la factura no se puede emitir."""
        self.currency_code
        if not self.line:
            raise ValueError("La factura necesita al menos una linea (el XSD exige InvoiceLine).")
        self.issue_date
        self.due_date
