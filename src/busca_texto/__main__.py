"""Permite executar ``python -m busca_texto`` (demo) e ``python -m busca_texto benchmark``."""

from .cli import principal

if __name__ == "__main__":
    raise SystemExit(principal())
