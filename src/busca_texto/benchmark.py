"""Benchmark dos algoritmos com ``time.perf_counter`` em textos aleatórios e casos patológicos.

Cada medição é o **menor** tempo de algumas repetições (o mínimo é o estimador menos sensível a
interrupções do sistema). Antes de medir, confere que todos os algoritmos devolvem exatamente as
mesmas posições que ``str.find``. Os tempos dependem da máquina e da versão do Python; o que
interessa é a comparação entre as linhas de uma mesma coluna.
"""

from __future__ import annotations

import random
import string
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

from .algoritmos import ALGORITMOS, AhoCorasick, kmp, str_find


@dataclass(frozen=True)
class Cenario:
    """Um caso de teste do benchmark: texto, padrão e uma descrição curta."""

    rotulo: str
    descricao: str
    texto: str
    padrao: str


def _aleatorio(rnd: random.Random, alfabeto: str, n: int) -> str:
    return "".join(rnd.choices(alfabeto, k=n))


def montar_cenarios(escala: float = 1.0, semente: int = 2026) -> list[Cenario]:
    """Cenários do benchmark; ``escala`` multiplica o tamanho dos textos (testes usam escala
    pequena para rodar rápido)."""
    rnd = random.Random(semente)
    grande = max(50, int(200_000 * escala))
    medio = max(50, int(20_000 * escala))
    m_pat = max(2, min(200, medio // 10))

    letras = _aleatorio(rnd, string.ascii_lowercase, grande)
    i = rnd.randrange(grande - 10)
    dna = _aleatorio(rnd, "ACGT", grande)
    j = rnd.randrange(grande - 16)
    return [
        Cenario("A", f"aleatório a-z, n={grande}, m=10 (trecho do próprio texto)",
                letras, letras[i:i + 10]),
        Cenario("B", f"DNA (ACGT), n={grande}, m=16", dna, dna[j:j + 16]),
        Cenario("C", f"'a'*{medio} com 'a'*{m_pat - 1}+'b' (pior caso da força bruta)",
                "a" * medio, "a" * (m_pat - 1) + "b"),
        Cenario("D", f"'a'*{medio} com 'b'+'a'*{m_pat - 1} (pior caso do Horspool)",
                "a" * medio, "b" + "a" * (m_pat - 1)),
        Cenario("E", f"'a'*{medio} com 'a'*{m_pat} (ocorrência em toda posição)",
                "a" * medio, "a" * m_pat),
    ]


def medir(funcao: Callable[[], object], repeticoes: int = 3) -> float:
    """Menor tempo, em segundos, entre ``repeticoes`` execuções de ``funcao``."""
    melhor = float("inf")
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        melhor = min(melhor, time.perf_counter() - inicio)
    return melhor


def _ms(segundos: float) -> str:
    return f"{segundos * 1000:9.2f}"


def tabela_padrao_unico(cenarios: list[Cenario], repeticoes: int = 3) -> None:
    """Imprime a tabela de tempos (ms) com um algoritmo por linha e um cenário por coluna."""
    funcoes = {**ALGORITMOS, "str.find (C)": str_find}
    for c in cenarios:
        esperado = str_find(c.texto, c.padrao)
        for nome, f in funcoes.items():
            if f(c.texto, c.padrao) != esperado:
                raise AssertionError(f"{nome} divergiu de str.find no cenário {c.rotulo}")
        print(f"  {c.rotulo}: {c.descricao} -> {len(esperado)} ocorrência(s)")
    print()
    cabecalho = "".join(f"{c.rotulo:>10}" for c in cenarios)
    print(f"  {'algoritmo (ms)':<16}{cabecalho}")
    print(f"  {'-' * 16}{'-' * 10 * len(cenarios)}")
    for nome, f in funcoes.items():
        tempos = "".join(" " + _ms(medir(lambda f=f, c=c: f(c.texto, c.padrao), repeticoes))
                         for c in cenarios)
        print(f"  {nome:<16}{tempos}")


def tabela_varios_padroes(escala: float = 1.0, quantidades: tuple[int, ...] = (1, 10, 50),
                          repeticoes: int = 3, semente: int = 7) -> None:
    """Compara Aho-Corasick (uma passada) com KMP e ``str.find`` repetidos por padrão."""
    rnd = random.Random(semente)
    n = max(100, int(100_000 * escala))
    texto = _aleatorio(rnd, "abcdefgh", n)
    print(f"  texto aleatório a-h com n={n}; padrões de 4 a 8 letras tirados do texto")
    print()
    print(f"  {'padrões':>8}{'ocorrências':>13}{'Aho-Corasick':>14}{'KMP repetido':>14}"
          f"{'str.find rep.':>15}")
    for k in quantidades:
        padroes = []
        while len(padroes) < k:
            t = rnd.randint(4, 8)
            i = rnd.randrange(n - t)
            if texto[i:i + t] not in padroes:
                padroes.append(texto[i:i + t])
        automato = AhoCorasick(padroes)
        total = len(automato.buscar(texto))
        if total != sum(len(str_find(texto, p)) for p in padroes):
            raise AssertionError("Aho-Corasick divergiu de str.find")
        t_aho = medir(lambda a=automato: a.buscar(texto), repeticoes)
        t_kmp = medir(lambda ps=padroes: [kmp(texto, p) for p in ps], repeticoes)
        t_find = medir(lambda ps=padroes: [str_find(texto, p) for p in ps], repeticoes)
        print(f"  {k:>8}{total:>13}{_ms(t_aho):>14}{_ms(t_kmp):>14}{_ms(t_find):>15}")


def executar(escala: float = 1.0, repeticoes: int = 3) -> None:
    """Roda o benchmark completo e imprime as tabelas."""
    versao = ".".join(map(str, sys.version_info[:3]))
    print("=== Benchmark de busca em texto (tempos em ms; menor de "
          f"{repeticoes} repetições; Python {versao}) ===")
    print("Os tempos variam de máquina para máquina; compare as linhas de uma mesma coluna.")
    print()
    print("Um padrão")
    print("---------")
    tabela_padrao_unico(montar_cenarios(escala), repeticoes)
    print()
    print("Vários padrões: Aho-Corasick x um algoritmo de padrão único repetido")
    print("--------------------------------------------------------------------")
    tabela_varios_padroes(escala, repeticoes=repeticoes)


if __name__ == "__main__":
    executar()
