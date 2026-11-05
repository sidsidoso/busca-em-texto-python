"""Pacote ``busca_texto``: algoritmos clássicos de busca de padrões em texto."""

from .algoritmos import (
    ALGORITMOS,
    BASE,
    MODULO,
    AhoCorasick,
    aho_corasick,
    buscar,
    busca_z,
    forca_bruta,
    funcao_prefixo,
    funcao_z,
    horspool,
    kmp,
    rabin_karp,
    rabin_karp_com_colisoes,
    str_find,
    tabela_horspool,
)

__all__ = [
    "ALGORITMOS",
    "BASE",
    "MODULO",
    "AhoCorasick",
    "aho_corasick",
    "buscar",
    "busca_z",
    "forca_bruta",
    "funcao_prefixo",
    "funcao_z",
    "horspool",
    "kmp",
    "rabin_karp",
    "rabin_karp_com_colisoes",
    "str_find",
    "tabela_horspool",
]
__version__ = "1.0.0"
