"""Capa de almacenamiento: escribe el XML como archivo fisico."""
from pathlib import Path

from ubl_invoice.encoding import encode_xml


class XmlFileWriter:
    def write(self, xml: str, directory: Path, file_name: str) -> Path:
        """Guarda `xml` en `directory/file_name` (crea la carpeta si no existe)."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / file_name
        path.write_bytes(encode_xml(xml))
        return path
