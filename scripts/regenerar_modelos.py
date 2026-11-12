#!/usr/bin/env python3
"""Regenera `ubl_models.py` (clases Python) a partir del XSD UBL Invoice 2.1.

Uso (desde la raiz del proyecto):

    python scripts/regenerar_modelos.py            # regenera y sobrescribe ubl_models.py
    python scripts/regenerar_modelos.py --check    # solo verifica que ubl_models.py este al dia

El archivo `ubl_models.py` es CODIGO GENERADO: no se edita a mano. Si cambia el XSD
(o la version de xsdata) se regenera con este script.

Detalle: `xsdata generate` crea ademas un `__init__.py` suelto en el directorio donde
se ejecuta. Para no ensuciar el proyecto, se genera en una carpeta temporal y solo se
copia `ubl_models.py`.
"""
import argparse
import filecmp
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XSD = ROOT / "xsd" / "maindoc" / "UBL-Invoice-2.1.xsd"
TARGET = ROOT / "ubl_models.py"
PACKAGE = "ubl_models"


def generar(xsd: Path, workdir: Path) -> Path:
    """Ejecuta xsdata en `workdir` y devuelve la ruta del modulo generado."""
    cmd = [
        sys.executable, "-m", "xsdata", "generate", str(xsd),
        "--package", PACKAGE,
        "--structure-style", "single-package",
    ]
    resultado = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
    if resultado.returncode != 0:
        sys.exit(f"xsdata fallo:\n{resultado.stdout}\n{resultado.stderr}")
    modulo = workdir / f"{PACKAGE}.py"
    if not modulo.exists():
        sys.exit(f"xsdata no genero {modulo.name}.\n{resultado.stdout}")
    return modulo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--xsd", type=Path, default=DEFAULT_XSD, help="XSD de entrada")
    parser.add_argument("--check", action="store_true",
                        help="no escribe nada; falla (codigo 1) si ubl_models.py esta desactualizado")
    args = parser.parse_args()

    if not args.xsd.exists():
        sys.exit(f"No existe el XSD: {args.xsd}")

    with tempfile.TemporaryDirectory() as tmp:
        generado = generar(args.xsd.resolve(), Path(tmp))
        if args.check:
            if TARGET.exists() and filecmp.cmp(generado, TARGET, shallow=False):
                print("OK: ubl_models.py esta al dia con el XSD.")
                return 0
            print("DESACTUALIZADO: ubl_models.py no coincide con lo generado desde el XSD.")
            print("Ejecute: python scripts/regenerar_modelos.py")
            return 1
        shutil.copyfile(generado, TARGET)

    lineas = sum(1 for _ in TARGET.open(encoding="utf-8"))
    print(f"Generado {TARGET.name} ({lineas} lineas) desde {args.xsd.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
