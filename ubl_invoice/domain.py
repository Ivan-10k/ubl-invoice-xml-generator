"""Capa de dominio: entidades y reglas de negocio.

No depende de xsdata, lxml ni de las clases generadas: se puede probar y
reutilizar sin conocer UBL.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional

DEFAULT_CURRENCY = "PEN"
_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


def money(value) -> float:
    """Redondea a 2 decimales con la regla comercial (mitad hacia arriba)."""
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _check_rate(rate: Optional[float], where: str) -> None:
    if rate is not None and not (0 <= rate <= 1):
        raise ValueError(f"{where}: la tasa de impuesto debe ser una fraccion entre 0 y 1 (ej. 0.18), no {rate}.")


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
    tax_rate: Optional[float] = None    # tasa propia (0.18 = 18 %); None = usa la de la factura

    @property
    def line_amount(self) -> float:
        if self.amount is not None:
            return self.amount
        if self.unit_price is not None:
            return money(self.quantity * self.unit_price)
        return 0.0

    def validate(self, position: int) -> None:
        """Reglas de la linea. `position` (1, 2, ...) solo sirve para el mensaje de error."""
        if self.quantity < 0:
            raise ValueError(f"Linea {position}: la cantidad no puede ser negativa.")
        if self.unit_price is not None and self.unit_price < 0:
            raise ValueError(f"Linea {position}: el precio unitario no puede ser negativo.")
        _check_rate(self.tax_rate, f"Linea {position}")
        if self.amount is not None and self.unit_price is not None:
            esperado = money(self.quantity * self.unit_price)
            if abs(self.amount - esperado) > 0.005:
                raise ValueError(
                    f"Linea {position}: importe {self.amount} no coincide con "
                    f"cantidad x precio = {esperado}."
                )


@dataclass(frozen=True)
class TaxGroup:
    """Subtotal de impuesto para una misma tasa."""

    rate: float      # fraccion (0.18)
    taxable: float   # base imponible
    tax: float       # impuesto


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
        self.tax_rate = None              # tasa por defecto de las lineas (0.18 = IGV 18 %); None = sin impuesto
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

    # ---- Impuestos y totales ----
    def rate_for(self, item: InvoiceLineItem) -> Optional[float]:
        """Tasa efectiva de una linea: la suya o, si no tiene, la de la factura."""
        return item.tax_rate if item.tax_rate is not None else self.tax_rate

    def line_tax(self, item: InvoiceLineItem) -> float:
        rate = self.rate_for(item)
        return 0.0 if rate is None else money(item.line_amount * rate)

    @property
    def is_taxed(self) -> bool:
        return any(self.rate_for(item) is not None for item in self.line)

    @property
    def subtotal(self) -> float:
        """Suma de los importes de linea (sin impuesto)."""
        return money(sum(item.line_amount for item in self.line))

    @property
    def tax_total(self) -> float:
        """Suma de los impuestos de linea (cada uno ya redondeado)."""
        return money(sum(self.line_tax(item) for item in self.line))

    @property
    def total(self) -> float:
        """Importe a pagar: subtotal + impuestos."""
        return money(self.subtotal + self.tax_total)

    def tax_breakdown(self) -> List[TaxGroup]:
        """Subtotales de impuesto agrupados por tasa (ordenados de menor a mayor)."""
        grupos: dict = {}
        for item in self.line:
            rate = self.rate_for(item)
            if rate is None:
                continue
            base, tax = grupos.get(rate, (0.0, 0.0))
            grupos[rate] = (base + item.line_amount, tax + self.line_tax(item))
        return [TaxGroup(rate, money(b), money(t)) for rate, (b, t) in sorted(grupos.items())]

    def validate(self) -> None:
        """Reglas de negocio. Lanza ValueError si la factura no se puede emitir."""
        self.currency_code
        _check_rate(self.tax_rate, "Factura")
        if not self.line:
            raise ValueError("La factura necesita al menos una linea (el XSD exige InvoiceLine).")
        for posicion, item in enumerate(self.line, start=1):
            item.validate(posicion)
        self.issue_date
        self.due_date
