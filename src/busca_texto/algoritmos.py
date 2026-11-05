"""Algoritmos de busca de um padrão em um texto.

Todas as funções têm a mesma assinatura ``f(texto, padrao) -> list[int]`` e devolvem **todas**
as posições iniciais em que ``padrao`` ocorre em ``texto``, em ordem crescente e **incluindo
ocorrências sobrepostas** (``"aa"`` em ``"aaaa"`` → ``[0, 1, 2]``).

Convenções comuns a todas:

- **Padrão vazio** ocorre em toda posição de ``0`` a ``len(texto)`` (inclusive), ou seja, o
  resultado é ``list(range(len(texto) + 1))``. É a mesma convenção de ``str.find``,
  ``str.count`` e de ``re.finditer("(?=)", texto)``: a cadeia vazia é prefixo de todo sufixo.
- **Padrão maior que o texto** não ocorre: ``[]``.
- Os índices são de **caracteres** (pontos de código Unicode), como em ``str``. Nenhuma
  normalização é feita: ``"é"`` pré-composto (U+00E9) e ``"e" + U+0301`` são textos diferentes.
- Argumentos que não sejam ``str`` levantam ``TypeError``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence

# ----------------------------------------------------------------- auxiliares


def _validar(texto: object, padrao: object) -> None:
    if not isinstance(texto, str):
        raise TypeError(f"texto deve ser str, não {type(texto).__name__}")
    if not isinstance(padrao, str):
        raise TypeError(f"padrão deve ser str, não {type(padrao).__name__}")


def _casos_triviais(texto: str, padrao: str) -> list[int] | None:
    """Trata padrão vazio e padrão maior que o texto; ``None`` se não for caso trivial."""
    _validar(texto, padrao)
    if not padrao:
        return list(range(len(texto) + 1))
    if len(padrao) > len(texto):
        return []
    return None


# ----------------------------------------------------------------- força bruta


def forca_bruta(texto: str, padrao: str) -> list[int]:
    """Testa cada alinhamento comparando caractere a caractere da esquerda para a direita.

    Tempo O((n - m + 1) · m) no pior caso (ex.: ``"aaa…a"`` com ``"aa…ab"``), mas O(n) em média
    para textos aleatórios com alfabeto grande, porque quase todo alinhamento falha cedo.
    """
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial
    n, m = len(texto), len(padrao)
    ocorrencias = []
    for i in range(n - m + 1):
        j = 0
        while j < m and texto[i + j] == padrao[j]:
            j += 1
        if j == m:
            ocorrencias.append(i)
    return ocorrencias


# ----------------------------------------------------------------- KMP


def funcao_prefixo(padrao: str) -> list[int]:
    """Função de prefixo (``π``) de Knuth–Morris–Pratt.

    ``pi[q]`` é o tamanho da maior **borda** de ``padrao[:q + 1]``: o maior prefixo próprio que
    também é sufixo. Ex.: ``funcao_prefixo("ababaca") == [0, 0, 1, 2, 3, 0, 1]``.
    Tempo O(m) amortizado: ``k`` só cresce de 1 em 1 e cada ``while`` o diminui.
    """
    pi = [0] * len(padrao)
    k = 0
    for q in range(1, len(padrao)):
        while k > 0 and padrao[k] != padrao[q]:
            k = pi[k - 1]
        if padrao[k] == padrao[q]:
            k += 1
        pi[q] = k
    return pi


def kmp(texto: str, padrao: str) -> list[int]:
    """Knuth–Morris–Pratt: nunca volta no texto; na falha, o padrão "pula" para a maior borda.

    Tempo O(n + m) no pior caso, espaço O(m).
    """
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial
    pi = funcao_prefixo(padrao)
    m = len(padrao)
    ocorrencias = []
    q = 0  # quantos caracteres do padrão já casaram
    for i, c in enumerate(texto):
        while q > 0 and padrao[q] != c:
            q = pi[q - 1]
        if padrao[q] == c:
            q += 1
        if q == m:
            ocorrencias.append(i - m + 1)
            q = pi[q - 1]  # continua a partir da borda: acha ocorrências sobrepostas
    return ocorrencias


# ----------------------------------------------------------------- Rabin-Karp

#: Base do hash polinomial (maior que o maior ponto de código Unicode, 0x10FFFF).
BASE = 1_114_129
#: Módulo primo de Mersenne 2^61 - 1: colisões acidentais têm chance ~ m / 2^61.
MODULO = (1 << 61) - 1


def rabin_karp_com_colisoes(
    texto: str, padrao: str, *, base: int = BASE, modulo: int = MODULO
) -> tuple[list[int], int]:
    """Rabin–Karp devolvendo também quantas **colisões** de hash foram descartadas.

    Uma colisão é uma janela com o mesmo hash do padrão mas conteúdo diferente; a verificação
    explícita garante que ela nunca vira um falso positivo. Útil para testes e para a demo
    (com um módulo pequeno, as colisões aparecem).
    """
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial, 0
    if base < 2 or modulo < 2:
        raise ValueError("base e módulo devem ser >= 2")
    n, m = len(texto), len(padrao)
    alto = pow(base, m - 1, modulo)  # peso do caractere que sai da janela
    hp = ht = 0
    for i in range(m):
        hp = (hp * base + ord(padrao[i])) % modulo
        ht = (ht * base + ord(texto[i])) % modulo
    ocorrencias = []
    colisoes = 0
    for i in range(n - m + 1):
        if hp == ht:
            if texto.startswith(padrao, i):  # verificação: hash igual não basta
                ocorrencias.append(i)
            else:
                colisoes += 1
        if i < n - m:
            # janela rolante: tira texto[i], desloca e acrescenta texto[i + m]
            ht = ((ht - ord(texto[i]) * alto) * base + ord(texto[i + m])) % modulo
    return ocorrencias, colisoes


def rabin_karp(texto: str, padrao: str, *, base: int = BASE, modulo: int = MODULO) -> list[int]:
    """Rabin–Karp: compara hashes polinomiais rolantes e só confere a janela quando batem.

    Tempo esperado O(n + m) (mais O(m) por ocorrência na verificação); pior caso O(n · m) se
    todas as janelas colidirem. Espaço O(1) além da saída.
    """
    return rabin_karp_com_colisoes(texto, padrao, base=base, modulo=modulo)[0]


# ----------------------------------------------------------------- Boyer-Moore-Horspool


def tabela_horspool(padrao: str) -> dict[str, int]:
    """Deslocamento por caractere: distância da última ocorrência de ``c`` em ``padrao[:-1]``
    até o fim do padrão. Caracteres ausentes (``dict.get`` padrão) deslocam ``len(padrao)``.

    Ex.: ``tabela_horspool("abcab") == {"a": 1, "b": 3, "c": 2}``.
    """
    m = len(padrao)
    return {c: m - 1 - i for i, c in enumerate(padrao[:-1])}


def horspool(texto: str, padrao: str) -> list[int]:
    """Boyer–Moore–Horspool: compara da direita para a esquerda e salta pelo último caractere
    da janela. Sublinear em média com alfabeto grande (pode pular ``m`` posições de uma vez);
    pior caso O(n · m) (ex.: ``"aaa…a"`` com ``"baa…a"``).
    """
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial
    n, m = len(texto), len(padrao)
    deslocamento = tabela_horspool(padrao)
    ultimo = padrao[-1]
    ocorrencias = []
    i = 0
    while i <= n - m:
        c = texto[i + m - 1]
        if c == ultimo:
            j = m - 2
            while j >= 0 and texto[i + j] == padrao[j]:
                j -= 1
            if j < 0:
                ocorrencias.append(i)
        i += deslocamento.get(c, m)
    return ocorrencias


# ----------------------------------------------------------------- algoritmo Z


def funcao_z(s: Sequence[object]) -> list[int]:
    """Vetor Z: ``z[i]`` é o tamanho do maior prefixo de ``s`` que começa em ``s[i]``.

    Por convenção ``z[0] = len(s)``. Mantém a "caixa Z" ``[l, r)`` mais à direita para reaproveitar
    comparações: tempo O(len(s)). Aceita qualquer sequência comparável (``str`` ou lista).
    Ex.: ``funcao_z("aabcaabxaaaz") == [12, 1, 0, 0, 3, 1, 0, 0, 2, 2, 1, 0]``.
    """
    n = len(s)
    z = [0] * n
    if n == 0:
        return z
    z[0] = n
    esq = dir_ = 0
    for i in range(1, n):
        if i < dir_:
            z[i] = min(dir_ - i, z[i - esq])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > dir_:
            esq, dir_ = i, i + z[i]
    return z


def busca_z(texto: str, padrao: str) -> list[int]:
    """Busca pelo algoritmo Z sobre ``padrao + [separador] + texto``.

    O separador é ``None``, que não é igual a nenhum caractere: por isso funciona com qualquer
    texto Unicode, sem precisar reservar um caractere como ``"$"``. Tempo e espaço O(n + m).
    """
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial
    m = len(padrao)
    z = funcao_z([*padrao, None, *texto])
    return [i - m - 1 for i in range(m + 1, len(z)) if z[i] == m]


# ----------------------------------------------------------------- Aho-Corasick


class AhoCorasick:
    """Autômato de Aho–Corasick para buscar **vários padrões** de uma vez.

    É uma trie dos padrões com **ligações de falha** (para o nó do maior sufixo próprio que
    também está na trie, como a função de prefixo do KMP) e **ligações de saída** (para o
    terminal mais próximo na cadeia de falhas, de modo que relatar ocorrências não visita nós
    que não terminam padrão).

    Construção O(Σ|p|) e busca O(n + z), onde ``z`` é o número de ocorrências, independente de
    quantos padrões existem. Padrões repetidos são considerados uma vez só; o padrão vazio ocorre
    em toda posição (mesma convenção das outras funções).
    """

    __slots__ = ("_filhos", "_falha", "_padrao_do_no", "_saida", "padroes")

    def __init__(self, padroes: Iterable[str]) -> None:
        if isinstance(padroes, str):
            raise TypeError("passe uma coleção de padrões, não uma única str")
        unicos: list[str] = []
        vistos: set[str] = set()
        for p in padroes:
            if not isinstance(p, str):
                raise TypeError(f"padrão deve ser str, não {type(p).__name__}")
            if p not in vistos:
                vistos.add(p)
                unicos.append(p)
        self.padroes: tuple[str, ...] = tuple(unicos)
        self._filhos: list[dict[str, int]] = [{}]
        self._padrao_do_no: list[int] = [-1]
        for indice, p in enumerate(self.padroes):
            self._inserir(p, indice)
        self._falha: list[int] = [0] * len(self._filhos)
        self._saida: list[int] = [-1] * len(self._filhos)
        self._construir_ligacoes()

    def _inserir(self, padrao: str, indice: int) -> None:
        no = 0
        for c in padrao:
            filho = self._filhos[no].get(c)
            if filho is None:
                filho = len(self._filhos)
                self._filhos[no][c] = filho
                self._filhos.append({})
                self._padrao_do_no.append(-1)
            no = filho
        self._padrao_do_no[no] = indice

    def _construir_ligacoes(self) -> None:
        """Busca em largura: a falha de um nó depende só de nós mais rasos, já processados."""
        filhos, falha, saida, terminal = self._filhos, self._falha, self._saida, self._padrao_do_no
        fila = list(filhos[0].values())  # filhos da raiz falham para a raiz
        for v in fila:
            saida[v] = 0 if terminal[0] >= 0 else -1
        inicio = 0
        while inicio < len(fila):
            u = fila[inicio]
            inicio += 1
            for c, v in filhos[u].items():
                f = falha[u]
                while f and c not in filhos[f]:
                    f = falha[f]
                falha[v] = filhos[f].get(c, 0)
                f = falha[v]
                saida[v] = f if terminal[f] >= 0 else saida[f]
                fila.append(v)

    def buscar(self, texto: str) -> list[tuple[int, str]]:
        """Todas as ocorrências como ``(posição inicial, padrão)``.

        A ordem é a de descoberta: por posição **final** crescente e, entre as que terminam no
        mesmo ponto, do padrão mais longo para o mais curto.
        """
        if not isinstance(texto, str):
            raise TypeError(f"texto deve ser str, não {type(texto).__name__}")
        filhos, falha, saida = self._filhos, self._falha, self._saida
        terminal, padroes = self._padrao_do_no, self.padroes
        resultado: list[tuple[int, str]] = []
        if terminal[0] >= 0:
            resultado.append((0, ""))
        estado = 0
        for i, c in enumerate(texto):
            while estado and c not in filhos[estado]:
                estado = falha[estado]
            estado = filhos[estado].get(c, 0)
            v = estado if terminal[estado] >= 0 else saida[estado]
            while v != -1:
                p = padroes[terminal[v]]
                resultado.append((i + 1 - len(p), p))
                v = saida[v]
        return resultado

    def buscar_por_padrao(self, texto: str) -> dict[str, list[int]]:
        """Ocorrências agrupadas por padrão (todos os padrões aparecem, mesmo sem ocorrência),
        com as posições em ordem crescente."""
        grupos: dict[str, list[int]] = {p: [] for p in self.padroes}
        for pos, p in self.buscar(texto):
            grupos[p].append(pos)
        return grupos

    def __len__(self) -> int:
        """Quantidade de nós do autômato (inclui a raiz)."""
        return len(self._filhos)

    def __repr__(self) -> str:
        return f"AhoCorasick(padroes={len(self.padroes)}, nos={len(self)})"


def aho_corasick(texto: str, padrao: str) -> list[int]:
    """Aho–Corasick com um único padrão (mesma interface das outras funções).

    Com um padrão só, o autômato equivale ao do KMP; serve para comparar as implementações.
    """
    _validar(texto, padrao)
    return [pos for pos, _ in AhoCorasick([padrao]).buscar(texto)]


# ----------------------------------------------------------------- referência e registro


def str_find(texto: str, padrao: str) -> list[int]:
    """Referência usando ``str.find`` (implementado em C no CPython), avançando 1 posição após
    cada ocorrência para incluir as sobrepostas. Não é um dos algoritmos estudados; serve de
    linha de base no benchmark."""
    trivial = _casos_triviais(texto, padrao)
    if trivial is not None:
        return trivial
    ocorrencias = []
    i = texto.find(padrao)
    while i != -1:
        ocorrencias.append(i)
        i = texto.find(padrao, i + 1)
    return ocorrencias


#: Algoritmos de padrão único, na ordem usada na demo, no benchmark e nos testes.
ALGORITMOS: dict[str, Callable[[str, str], list[int]]] = {
    "forca_bruta": forca_bruta,
    "kmp": kmp,
    "rabin_karp": rabin_karp,
    "horspool": horspool,
    "z": busca_z,
    "aho_corasick": aho_corasick,
}


def buscar(texto: str, padrao: str, algoritmo: str = "kmp") -> list[int]:
    """Busca ``padrao`` em ``texto`` com o algoritmo escolhido pelo nome (ver ``ALGORITMOS``)."""
    try:
        funcao = ALGORITMOS[algoritmo]
    except KeyError:
        opcoes = ", ".join(ALGORITMOS)
        raise ValueError(f"algoritmo desconhecido {algoritmo!r}; opções: {opcoes}") from None
    return funcao(texto, padrao)
