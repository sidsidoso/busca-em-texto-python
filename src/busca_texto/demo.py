"""Demonstração: busca de palavras em um texto original em português embutido no código."""

from __future__ import annotations

from .algoritmos import (
    ALGORITMOS,
    AhoCorasick,
    funcao_prefixo,
    funcao_z,
    rabin_karp_com_colisoes,
    tabela_horspool,
)

# Texto original escrito para esta demonstração.
TEXTO = """\
A biblioteca da universidade abria cedo, e Ana gostava de chegar antes de todo mundo.
Naquela manhã ela procurava, num livro antigo de algoritmos, a explicação para um problema
que a perseguia desde a aula anterior: como encontrar uma palavra dentro de um texto enorme
sem comparar letra por letra em cada posição? O professor tinha falado de prefixos que também
são sufixos, de saltos baseados na última letra da janela e de impressões digitais calculadas
com aritmética modular. Ana anotou tudo no caderno, desenhou a tabela de prefixos da palavra
"ananas" e percebeu, com alegria, que o padrão podia deslizar sobre o texto sem nunca voltar
atrás. Na saída da biblioteca, encontrou a colega Mariana, que estudava compressão de dados,
e as duas passaram a tarde trocando ideias sobre textos, padrões e autômatos.
"""


def _titulo(texto: str) -> None:
    print()
    print(texto)
    print("-" * len(texto))


def _contexto(texto: str, pos: int, tamanho: int, margem: int = 18) -> str:
    """Trecho do texto em volta de uma ocorrência, com a ocorrência entre colchetes."""
    ini = max(0, pos - margem)
    fim = min(len(texto), pos + tamanho + margem)
    trecho = f"{texto[ini:pos]}[{texto[pos:pos + tamanho]}]{texto[pos + tamanho:fim]}"
    trecho = trecho.replace("\n", " ")
    return ("…" if ini > 0 else "") + trecho + ("…" if fim < len(texto) else "")


def _linha_e_coluna(texto: str, pos: int) -> tuple[int, int]:
    linha = texto.count("\n", 0, pos) + 1
    coluna = pos - (texto.rfind("\n", 0, pos) + 1) + 1
    return linha, coluna


def executar() -> None:
    """Executa a demonstração completa no terminal."""
    print("=== Busca de padrões em texto: força bruta, KMP, Rabin-Karp, Horspool, Z e"
          " Aho-Corasick ===")
    print(f"texto de exemplo: {len(TEXTO)} caracteres, {TEXTO.count(chr(10))} linhas")

    _titulo("Uma palavra, todos os algoritmos")
    # busca sem diferenciar maiúsculas: lower() preserva o tamanho deste texto (conferido abaixo)
    minusculo = TEXTO.lower()
    assert len(minusculo) == len(TEXTO)
    for palavra in ("biblioteca", "ana", "texto", "prefixos"):
        resultados = {nome: f(minusculo, palavra) for nome, f in ALGORITMOS.items()}
        unicos = {tuple(r) for r in resultados.values()}
        concordam = "todos concordam" if len(unicos) == 1 else "DIVERGÊNCIA!"
        posicoes = resultados["kmp"]
        print(f"  {palavra!r:<13} {len(posicoes):>2} ocorrência(s) ({concordam}): {posicoes}")

    _titulo("Ocorrências de 'ana' (sem diferenciar maiúsculas) com contexto")
    for pos in ALGORITMOS["horspool"](minusculo, "ana"):
        linha, coluna = _linha_e_coluna(TEXTO, pos)
        print(f"  linha {linha}, coluna {coluna:>2}: {_contexto(TEXTO, pos, 3)}")
    print("  ('ana' aparece em Ana, ananas, Mariana... e em 'ananas' duas vezes, sobrepostas)")

    _titulo("Ocorrências sobrepostas")
    for texto, padrao in (("ananas", "ana"), ("aaaaa", "aa"), ("abababab", "abab")):
        print(f"  {padrao!r:<6} em {texto!r:<10} -> {ALGORITMOS['kmp'](texto, padrao)}")

    _titulo("Padrão vazio e bordas")
    print(f"  ''      em 'abc' -> {ALGORITMOS['z']('abc', '')}  (toda posição de 0 a len(texto))")
    print(f"  'abcd'  em 'abc' -> {ALGORITMOS['horspool']('abc', 'abcd')}"
          "  (padrão maior que o texto)")
    print(f"  'ção'   em 'ação e reação' -> {ALGORITMOS['rabin_karp']('ação e reação', 'ção')}")
    decomposto = "café"  # 'e' + acento agudo combinante (U+0301)
    print(f"  'é'     em 'café' decomposto (e + U+0301) -> {ALGORITMOS['kmp'](decomposto, 'é')}"
          "  (sem normalização Unicode)")

    _titulo("Por dentro dos algoritmos")
    p = "ananas"
    print(f"  KMP, função de prefixo de {p!r}:   {funcao_prefixo(p)}")
    print(f"  Z, vetor Z de {p!r}:               {funcao_z(p)}")
    tabela = ", ".join(f"{c!r}: {d}" for c, d in sorted(tabela_horspool(p).items()))
    print(f"  Horspool, deslocamentos de {p!r}: {{{tabela}}} (outros: {len(p)})")
    ocorr, colisoes = rabin_karp_com_colisoes(minusculo, "texto")
    print(f"  Rabin-Karp com módulo 2^61-1: {len(ocorr)} ocorrências de 'texto',"
          f" {colisoes} colisões")
    ocorr, colisoes = rabin_karp_com_colisoes(minusculo, "texto", modulo=101)
    print(f"  Rabin-Karp com módulo 101:    {len(ocorr)} ocorrências de 'texto',"
          f" {colisoes} colisões descartadas pela verificação")

    _titulo("Aho-Corasick: vários padrões em uma única passada")
    palavras = ["texto", "textos", "padrão", "padrões", "prefixo", "sufixo", "letra", "ana", "na"]
    automato = AhoCorasick(palavras)
    print(f"  {automato}")
    grupos = automato.buscar_por_padrao(minusculo)
    for palavra in palavras:
        print(f"  {palavra:<8} {len(grupos[palavra]):>2}x  {grupos[palavra][:8]}"
              f"{' …' if len(grupos[palavra]) > 8 else ''}")
    primeiras = automato.buscar(minusculo)[:6]
    print(f"  primeiras ocorrências (posição, padrão): {primeiras}")
    total = sum(len(v) for v in grupos.values())
    print(f"  total: {total} ocorrências de {len(palavras)} padrões com 1 leitura do texto")
