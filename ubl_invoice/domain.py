"""Capa de dominio: entidades y reglas de negocio.

No depende de xsdata, lxml ni de las clases generadas: se puede probar y
reutilizar sin conocer UBL.
"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

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
    """Una linea de la factura.

    El importe de la linea (`line_amount`) se obtiene asi:
      - si se asigno `amount`, se usa tal cual;
      - si no, y hay `unit_price`, se calcula cantidad x precio unitario (2 decimales);
      - si no hay ninguno, es 0.
    """

    quantity: float = 0
    description: str = "Producto generico"
    amount: Optional[float] = None      # importe manual de la linea (LineExtensionAmount)
    unit_price: Optional[float] = None  # precio por unidad (opcional)

    @property
    def line_amount(self) -> float:
        if self.amount is not None:
            return self.amount
        if self.unit_price is not None:
            return round(self.quantity * self.unit_price, 2)
        return 0.0

    def validate(self, position: int) -> None:
        """Reglas de la linea. `position` (1, 2, ...) solo sirve para el mensaje de error."""
        if self.quantity < 0:
            raise ValueError(f"Linea {position}: la cantidad no puede ser negativa.")
        if self.unit_price is not None and self.unit_price < 0:
            raise ValueError(f"Linea {position}: el precio unitario no puede ser negativo.")
        if self.amount is not None and self.unit_price is not None:
            esperado = round(self.quantity * self.unit_price, 2)
            if abs(self.amount - esperado) > 0.005:
                raise ValueError(
                    f"Linea {position}: importe {self.amount} no coincide con "
                    f"cantidad x precio = {esperado}."
                )


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
        return round(sum(item.line_amount for item in self.line), 2)

    def validate(self) -> None:
        """Reglas de negocio. Lanza ValueError si la factura no se puede emitir."""
        self.currency_code
        if not self.line:
            raise ValueError("La factura necesita al menos una linea (el XSD exige InvoiceLine).")
        for posicion, item in enumerate(self.line, start=1):
            item.validate(posicion)
        self.issue_date
        self.due_date
