"""Ponto de entrada (funciona sem instalar o pacote).

Uso: ``python main.py`` (demonstração) ou ``python main.py benchmark``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from busca_texto.cli import principal  # noqa: E402

if __name__ == "__main__":
    sys.exit(principal())
