"""Puertos (abstracciones) de las que depende la fachada.

La fachada depende de estos contratos, no de implementaciones concretas
(Inversion de Dependencias). Cualquier objeto con estos metodos sirve:
se puede cambiar el serializador o el validador sin modificar `Invoice`
(Abierto/Cerrado) y reemplazarlos por dobles de prueba.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from ubl_invoice.domain import InvoiceEntity


@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


@runtime_checkable
class UblMapper(Protocol):
    """Convierte la factura de dominio en el objeto UBL a serializar."""

    def to_ubl(self, invoice: InvoiceEntity) -> Any: ...


@runtime_checkable
class XmlSerializer(Protocol):
    """Convierte el objeto UBL en texto XML."""

    def serialize(self, ubl_invoice: Any) -> str: ...


@runtime_checkable
class XmlValidator(Protocol):
    """Valida un texto XML y devuelve el resultado."""

    def validate(self, xml: str) -> ValidationResult: ...


@runtime_checkable
class XmlWriter(Protocol):
    """Guarda el texto XML como archivo y devuelve la ruta escrita."""

    def write(self, xml: str, directory: Path, file_name: str) -> Path: ...
