"""Linha de comando: ``demo`` (padrão) ou ``benchmark``."""

from __future__ import annotations

import sys

from . import benchmark, demo


def principal(argumentos: list[str] | None = None) -> int:
    """Executa a demo ou o benchmark conforme o primeiro argumento."""
    args = sys.argv[1:] if argumentos is None else argumentos
    acao = args[0] if args else "demo"
    if acao == "demo":
        demo.executar()
    elif acao == "benchmark":
        benchmark.executar()
    else:
        print("uso: python main.py [demo|benchmark]", file=sys.stderr)
        return 2
    return 0
