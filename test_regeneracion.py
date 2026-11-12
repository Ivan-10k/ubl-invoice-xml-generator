"""Pruebas del script de regeneracion de ubl_models.py."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent / "scripts" / "regenerar_modelos.py"


def test_script_muestra_ayuda():
    r = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
    assert r.returncode == 0
    assert "--check" in r.stdout


def test_script_falla_con_xsd_inexistente():
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--xsd", "no_existe.xsd"],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "No existe el XSD" in r.stderr


@pytest.mark.skipif(
    os.environ.get("REGEN_CHECK") != "1",
    reason="Lento (~6 s) y depende de la version de xsdata. Activar con REGEN_CHECK=1.",
)
def test_ubl_models_esta_al_dia_con_el_xsd():
    r = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
