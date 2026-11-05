# Busca de padrões em texto em Python

[![CI](https://github.com/sidsidoso/busca-em-texto-python/actions/workflows/ci.yml/badge.svg)](https://github.com/sidsidoso/busca-em-texto-python/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)

Implementação didática dos algoritmos clássicos de **busca de padrões em texto** (*string
matching*), em Python puro (somente biblioteca padrão):

- **força bruta**;
- **Knuth–Morris–Pratt (KMP)**, com a função de prefixo;
- **Rabin–Karp**, com hash polinomial rolante módulo 2⁶¹ − 1 e verificação de cada candidato;
- **Boyer–Moore–Horspool**;
- **algoritmo Z**;
- **Aho–Corasick**, para vários padrões ao mesmo tempo.

Todas as funções têm a mesma interface, `f(texto, padrao) -> list[int]`, e devolvem **todas** as
ocorrências, **inclusive as sobrepostas** (`"aa"` em `"aaaa"` → `[0, 1, 2]`). O projeto traz um
**benchmark** com `time.perf_counter` em texto aleatório e em casos patológicos, uma
**demonstração** que procura palavras em um texto original em português e uma suíte de testes que
compara todos os algoritmos com a força bruta e com `re` em milhares de entradas aleatórias.

## Sumário

- [Conceito](#conceito)
- [Operações e complexidade](#operações-e-complexidade)
- [Convenções: padrão vazio, bordas e Unicode](#convenções-padrão-vazio-bordas-e-unicode)
- [Decisões de implementação e otimizações](#decisões-de-implementação-e-otimizações)
- [Estrutura de pastas](#estrutura-de-pastas)
- [Como executar](#como-executar)
- [Como testar](#como-testar)
- [Exemplo de uso](#exemplo-de-uso)
- [Saída da demonstração](#saída-da-demonstração)
- [Benchmark](#benchmark)
- [Referências](#referências)

## Conceito

Dado um texto `T` de tamanho `n` e um padrão `P` de tamanho `m`, queremos todas as posições `i`
com `T[i:i+m] == P`. A **força bruta** testa cada um dos `n − m + 1` alinhamentos e, a cada
falha, recomeça do zero. Os outros algoritmos evitam esse retrabalho de maneiras diferentes:

**KMP: aproveitar o que já casou.** Se `ababa` casou e o próximo caractere falhou, o sufixo `aba`
do que já foi lido também é prefixo do padrão (uma **borda**). O padrão desliza direto para essa
borda, sem nunca voltar no texto. A **função de prefixo** `π` guarda a maior borda de cada
prefixo do padrão:

```text
 padrão:   a  b  a  b  a  c  a
 π:        0  0  1  2  3  0  1

 texto:  … a  b  a  b  a  b  a  c  a …
           a  b  a  b  a  c              ✗ falhou no 'c' (q = 5 casados)
                 a  b  a  b  a  c  a     desliza: q = π[4] = 3 ("aba" já está casado)
```

**Boyer–Moore–Horspool: olhar o fim da janela e saltar.** Compara da direita para a esquerda e,
seja qual for o resultado, desloca a janela conforme o **último caractere** dela. Um caractere
que não está no padrão faz a janela pular `m` posições de uma vez:

```text
 padrão "texto": deslocamentos  t→1 (o 't' de "tex|t|o")  x→2  e→3   outros→5

 texto:  l e i a   o   t e x t o
         t e x t o   último da janela = ' ' (fora do padrão): salta 5
                   t e x t o   último = 'x': salta 2
                       t e x t o   casou!
```

**Rabin–Karp: comparar impressões digitais.** Cada janela de `m` caracteres vira um número
`h = (c₀·Bᵐ⁻¹ + c₁·Bᵐ⁻² + … + cₘ₋₁) mod M`. Deslizar a janela custa O(1): tira o caractere que
sai, multiplica por `B` e soma o que entra. Só quando o hash da janela é igual ao do padrão a
janela é comparada de fato (hash igual não garante texto igual: pode ser **colisão**).

**Algoritmo Z: quanto cada posição repete o começo.** `Z[i]` é o tamanho do maior trecho a partir
de `i` que coincide com o prefixo da cadeia. Calculando Z sobre `padrão + separador + texto`, toda
posição com `Z[i] = m` é uma ocorrência:

```text
 s:  a  n  a  ┃  b  a  n  a  n  a
 Z:  -  0  1  0  0  3  0  3  0  1        Z = 3 = m nas posições do texto 1 e 3 → [1, 3]
```

**Aho–Corasick: KMP para vários padrões.** Os padrões formam uma trie; cada nó ganha uma
**ligação de falha** para o nó do maior sufixo próprio que também está na trie, e uma
**ligação de saída** para o padrão mais próximo nessa cadeia. Uma única leitura do texto
encontra todas as ocorrências de todos os padrões. Para `he`, `she`, `his`, `hers`:

```text
                (raiz)
               /      \
             h          s
           /   \        |
         e*     i       h ·····> h          (falha de "sh" → "h")
         |      |       |
         r      s*      e* ·····> e*        (falha de "she" → "he": ao achar "she", também
         |                                   relata "he" pela ligação de saída)
         s*

 buscar("ushers") -> [(1, 'she'), (2, 'he'), (2, 'hers')]
```

## Operações e complexidade

`n` = tamanho do texto, `m` = tamanho do padrão, `σ` = tamanho do alfabeto, `z` = número de
ocorrências, `M` = soma dos tamanhos dos padrões (Aho–Corasick).

| Algoritmo | Função | Pré-processamento | Busca (pior caso) | Busca (típica) | Espaço extra |
|---|---|---|---|---|---|
| Força bruta | `forca_bruta` | — | O((n − m + 1)·m) | O(n) em texto aleatório | O(1) |
| KMP | `kmp`, `funcao_prefixo` | O(m) | **O(n)** | O(n) | O(m) |
| Rabin–Karp | `rabin_karp` | O(m) | O(n·m) (tudo colide) | O(n + z·m) | O(1) |
| Horspool | `horspool`, `tabela_horspool` | O(m) | O(n·m) | **sublinear**, ~ n/m com σ grande | O(min(m, σ)) |
| Algoritmo Z | `busca_z`, `funcao_z` | — | **O(n + m)** | O(n + m) | O(n + m) |
| Aho–Corasick | `AhoCorasick(padroes).buscar` | O(M) | **O(n + z)** | O(n + z) | O(M) |
| Referência em C | `str_find` | — | — | — | — |

O pior caso **inclui** a saída: com padrão `"a"*m` em `"a"*n` há `n − m + 1` ocorrências, e
algoritmos que verificam cada uma (força bruta, Horspool, Rabin–Karp) pagam O(m) por ocorrência.
KMP, Z e Aho–Corasick reaproveitam o que já casou e continuam lineares.

## Convenções: padrão vazio, bordas e Unicode

- **Padrão vazio** ocorre em **toda posição de 0 a `len(texto)`**, inclusive: `buscar("abc", "")`
  devolve `[0, 1, 2, 3]` e `buscar("", "")` devolve `[0]`. A cadeia vazia é prefixo de todo
  sufixo do texto, inclusive do sufixo vazio; é a mesma convenção de `str.find`, `str.count`
  (`"abc".count("") == 4`) e de `re.finditer("(?=)", texto)`. No Aho–Corasick, o padrão vazio
  aparece como `(i, "")` para todo `i`.
- **Padrão maior que o texto**: `[]`.
- **Unicode**: as posições são índices de caracteres (pontos de código), como em `str`. Emojis
  fora do BMP contam como 1 caractere. **Não há normalização**: `"é"` pré-composto (U+00E9) não
  casa com `"e" + U+0301`, nem `"pão"` com `"PÃO"`. Quem precisar disso normaliza antes
  (`unicodedata.normalize`, `str.casefold`).
- Argumentos que não sejam `str` levantam `TypeError`; nome de algoritmo inválido em `buscar`
  levanta `ValueError`.

## Decisões de implementação e otimizações

- **Uma interface para todos**: o dicionário `ALGORITMOS` mapeia nome → função. Testes, demo e
  benchmark percorrem esse dicionário, então um algoritmo novo é testado contra todos os
  oráculos só por ser registrado.
- **Sobreposição sem casos especiais**: no KMP, depois de uma ocorrência o estado volta para
  `π[m − 1]` (a maior borda do padrão inteiro), e não para 0; no Aho–Corasick isso sai de graça
  pelas ligações de falha; nos outros, a janela avança no máximo até o próximo alinhamento possível.
- **Rabin–Karp com módulo primo de Mersenne `2⁶¹ − 1`** e base `1 114 129` (maior que o maior
  ponto de código Unicode): a chance de colisão acidental por janela fica na casa de `m / 2⁶¹`.
  Mesmo assim, **toda** janela com hash igual é conferida com `str.startswith(padrao, i)`, então
  o resultado é sempre exato. Os testes forçam módulos minúsculos (2, 3, 7, 101) para provocar
  milhares de colisões e verificar que nenhuma vira falso positivo; a demo mostra as colisões
  descartadas. `rabin_karp_com_colisoes` expõe essa contagem.
- **O peso `Bᵐ⁻¹ mod M` é calculado uma vez** com `pow(base, m − 1, modulo)` (exponenciação
  modular), e a janela rola com uma subtração, uma multiplicação e uma soma.
- **Horspool com `dict` e `get(c, m)`**: a tabela de deslocamentos só tem os caracteres de
  `padrao[:-1]`; qualquer outro caractere (de um alfabeto Unicode inteiro) usa o padrão `m`, sem
  precisar de um vetor de 1,1 milhão de posições. A comparação completa só começa quando o
  último caractere da janela casa.
- **Algoritmo Z com separador `None`**: em vez de reservar um caractere como `"$"` (que poderia
  aparecer no texto), a função Z roda sobre a lista `[*padrao, None, *texto]`. `None` nunca é
  igual a um caractere, então `Z[i] ≤ m` vale para qualquer entrada Unicode.
- **Aho–Corasick com ligações de saída**: relatar as ocorrências visita só nós terminais (não
  toda a cadeia de falhas), o que mantém a busca em O(n + z). Os filhos são `dict` (alfabeto
  aberto, sem vetor de σ posições por nó), a construção é uma busca em largura e padrões
  repetidos são deduplicados. A saída segue a ordem de descoberta: posição final crescente e,
  no mesmo ponto, do padrão mais longo para o mais curto.
- **`__slots__` no autômato** e referências locais (`filhos`, `falha`, `saida`) no laço quente:
  evitam buscas de atributo a cada caractere, que pesam bastante em Python.
- **Benchmark honesto**: antes de medir, cada algoritmo é conferido contra `str.find`; cada
  tempo é o **mínimo** de 3 repetições (o estimador menos afetado por interrupções do sistema);
  e `str.find`, escrito em C, aparece como linha de base para lembrar o custo do interpretador.

## Estrutura de pastas

```text
busca-em-texto-python/
├── .github/workflows/ci.yml   # testes + demo + benchmark em Python 3.11, 3.12 e 3.13
├── src/busca_texto/
│   ├── __init__.py            # API pública
│   ├── __main__.py            # python -m busca_texto [demo|benchmark]
│   ├── algoritmos.py          # força bruta, KMP, Rabin-Karp, Horspool, Z, Aho-Corasick
│   ├── benchmark.py           # cenários aleatórios e patológicos com time.perf_counter
│   ├── cli.py                 # linha de comando
│   └── demo.py                # texto em português e demonstração
├── tests/
│   └── test_busca.py          # unittest: bordas + aleatórios contra força bruta e re
├── main.py                    # demonstração/benchmark (não exige instalação)
├── pyproject.toml
├── LICENSE
└── README.md
```

## Como executar

Requisito: **Python 3.11+**. Não há dependências externas e nada é baixado.

**Linux / macOS**

```bash
git clone https://github.com/sidsidoso/busca-em-texto-python.git
cd busca-em-texto-python
python3 main.py              # demonstração
python3 main.py benchmark    # benchmark (alguns segundos)
# ou, como módulo:
PYTHONPATH=src python3 -m busca_texto benchmark
```

**Windows (PowerShell)**

```powershell
git clone https://github.com/sidsidoso/busca-em-texto-python.git
cd busca-em-texto-python
py main.py
py main.py benchmark
# ou, como módulo:
$env:PYTHONPATH = "src"; py -m busca_texto benchmark
```

Opcionalmente, instale o pacote em modo editável (`pip install -e .`); isso cria também o comando
`busca-texto [demo|benchmark]`.

## Como testar

```bash
# Linux / macOS
python3 -m unittest discover -s tests -v
```

```powershell
# Windows
py -m unittest discover -s tests -v
```

A suíte tem 35 testes:

- **bordas** para todos os algoritmos: padrão vazio (`[0..n]`), texto vazio, padrão maior que o
  texto, padrão igual ao texto, ocorrências no início/fim, sobrepostas (`"aa"` em `"aaaa"`,
  `"abab"` em `"abababab"`), caracteres especiais de regex, Unicode (acentos, emoji fora do BMP,
  CJK, acento combinante sem normalização) e tipos inválidos;
- **estruturas internas** conferidas contra a definição por força bruta: função de prefixo,
  vetor Z, tabela do Horspool (além dos exemplos clássicos `ababaca` e `aabcaabxaaaz`);
- **aleatórios**: 3 000 rodadas com alfabetos pequenos (`ab`, `abc`, `01`, `áàç`, `αβ`, letra +
  emoji…), em que **cada algoritmo** é comparado com a força bruta, que por sua vez é comparada
  com `re.finditer("(?=padrão)")`, o lookahead que encontra ocorrências sobrepostas; mais
  textos periódicos (`(ab)ᵏ`, `aᵏ`), que estressam bordas longas, e um texto de 20 000 caracteres;
- **Rabin–Karp** com módulos minúsculos (mais de mil colisões, nenhum falso positivo) e com o
  módulo padrão (zero colisões em 50 000 janelas);
- **Aho–Corasick**: exemplo clássico `he/she/his/hers`, ordem de saída, padrões que são prefixo e
  sufixo uns dos outros, duplicados, padrão vazio, conjunto vazio e 800 conjuntos aleatórios
  comparados com o oráculo;
- **execução** da demo, do benchmark (em escala reduzida) e da linha de comando.

Resultado local:

```text
Ran 35 tests in 0.673s

OK
```

## Exemplo de uso

```python
from busca_texto import AhoCorasick, buscar, kmp, funcao_prefixo

kmp("banana", "ana")                  # [1, 3]  (sobrepostas)
buscar("banana", "na", "horspool")    # [2, 4]
buscar("abc", "")                     # [0, 1, 2, 3]
funcao_prefixo("ababaca")             # [0, 0, 1, 2, 3, 0, 1]

ac = AhoCorasick(["he", "she", "his", "hers"])
ac.buscar("ushers")                   # [(1, 'she'), (2, 'he'), (2, 'hers')]
ac.buscar_por_padrao("ushers")        # {'he': [2], 'she': [1], 'his': [], 'hers': [2]}
```

## Saída da demonstração

Saída real de `python main.py`:

```text
=== Busca de padrões em texto: força bruta, KMP, Rabin-Karp, Horspool, Z e Aho-Corasick ===
texto de exemplo: 814 caracteres, 9 linhas

Uma palavra, todos os algoritmos
--------------------------------
  'biblioteca'   2 ocorrência(s) (todos concordam): [2, 662]
  'ana'          5 ocorrência(s) (todos concordam): [43, 481, 551, 553, 697]
  'texto'        3 ocorrência(s) (todos concordam): [256, 620, 785]
  'prefixos'     2 ocorrência(s) (todos concordam): [343, 530]

Ocorrências de 'ana' (sem diferenciar maiúsculas) com contexto
--------------------------------------------------------------
  linha 1, coluna 44: …ade abria cedo, e [Ana] gostava de chegar…
  linha 6, coluna 25: …itmética modular. [Ana] anotou tudo no ca…
  linha 7, coluna  2: …fixos da palavra "[ana]nas" e percebeu, c…
  linha 7, coluna  4: …xos da palavra "an[ana]s" e percebeu, com…
  linha 8, coluna 55: …trou a colega Mari[ana], que estudava com…
  ('ana' aparece em Ana, ananas, Mariana... e em 'ananas' duas vezes, sobrepostas)

Ocorrências sobrepostas
-----------------------
  'ana'  em 'ananas'   -> [0, 2]
  'aa'   em 'aaaaa'    -> [0, 1, 2, 3]
  'abab' em 'abababab' -> [0, 2, 4]

Padrão vazio e bordas
---------------------
  ''      em 'abc' -> [0, 1, 2, 3]  (toda posição de 0 a len(texto))
  'abcd'  em 'abc' -> []  (padrão maior que o texto)
  'ção'   em 'ação e reação' -> [1, 10]
  'é'     em 'café' decomposto (e + U+0301) -> []  (sem normalização Unicode)

Por dentro dos algoritmos
-------------------------
  KMP, função de prefixo de 'ananas':   [0, 0, 1, 2, 3, 0]
  Z, vetor Z de 'ananas':               [6, 0, 3, 0, 1, 0]
  Horspool, deslocamentos de 'ananas': {'a': 1, 'n': 2} (outros: 6)
  Rabin-Karp com módulo 2^61-1: 3 ocorrências de 'texto', 0 colisões
  Rabin-Karp com módulo 101:    3 ocorrências de 'texto', 5 colisões descartadas pela verificação

Aho-Corasick: vários padrões em uma única passada
-------------------------------------------------
  AhoCorasick(padroes=9, nos=38)
  texto     3x  [256, 620, 785]
  textos    1x  [785]
  padrão    1x  [590]
  padrões   1x  [793]
  prefixo   2x  [343, 530]
  sufixo    1x  [367]
  letra     3x  [282, 292, 405]
  ana       5x  [43, 481, 551, 553, 697]
  na        8x  [44, 86, 395, 482, 552, 554, 650, 698]
  primeiras ocorrências (posição, padrão): [(43, 'ana'), (44, 'na'), (86, 'na'), (256, 'texto'), (282, 'letra'), (292, 'letra')]
  total: 25 ocorrências de 9 padrões com 1 leitura do texto
```

## Benchmark

Saída real de `python main.py benchmark` em uma máquina com Windows 11 e Python 3.15.
**Os tempos variam de máquina para máquina** (e entre versões do Python); o que importa é a
comparação entre as linhas de uma mesma coluna.

```text
=== Benchmark de busca em texto (tempos em ms; menor de 3 repetições; Python 3.15.1) ===
Os tempos variam de máquina para máquina; compare as linhas de uma mesma coluna.

Um padrão
---------
  A: aleatório a-z, n=200000, m=10 (trecho do próprio texto) -> 1 ocorrência(s)
  B: DNA (ACGT), n=200000, m=16 -> 1 ocorrência(s)
  C: 'a'*20000 com 'a'*199+'b' (pior caso da força bruta) -> 0 ocorrência(s)
  D: 'a'*20000 com 'b'+'a'*199 (pior caso do Horspool) -> 0 ocorrência(s)
  E: 'a'*20000 com 'a'*200 (ocorrência em toda posição) -> 19801 ocorrência(s)

  algoritmo (ms)           A         B         C         D         E
  ------------------------------------------------------------------
  forca_bruta          20.64     26.76    292.79      1.78    169.06
  kmp                  10.27     12.99      2.09      0.97      2.38
  rabin_karp           76.56     73.27      6.62      6.44      8.27
  horspool              2.29      5.05      1.42    155.30    162.68
  z                    31.89     39.71      5.79      2.93      6.55
  aho_corasick         18.21     21.74      2.64      1.66      5.82
  str.find (C)          0.13      0.43      0.10      0.01     22.63

Vários padrões: Aho-Corasick x um algoritmo de padrão único repetido
--------------------------------------------------------------------
  texto aleatório a-h com n=100000; padrões de 4 a 8 letras tirados do texto

   padrões  ocorrências  Aho-Corasick  KMP repetido  str.find rep.
         1            2         10.76          5.98           0.20
        10           52         14.92         66.33           2.47
        50          336         17.92        397.89          10.80
```

Leitura dos resultados:

- **Texto aleatório (A, B)**: o **Horspool** é o mais rápido dos algoritmos em Python, porque
  quase sempre o último caractere da janela não casa e ele salta várias posições; com alfabeto
  de 26 letras salta mais do que no DNA (4 letras). O **Rabin–Karp** é o mais lento aqui: cada
  passo faz aritmética com inteiros maiores que 64 bits antes do `% M`.
- **Pior caso da força bruta (C)**: cada alinhamento compara 199 `a` antes de falhar no `b`,
  ~4 milhões de comparações. KMP, Z e Aho–Corasick nunca voltam e ficam de 50 a 140× mais rápidos. O
  Horspool escapa porque compara primeiro o `b` do fim.
- **Pior caso do Horspool (D)**: agora o diferente está no **início** do padrão; o Horspool
  compara 199 caracteres da direita para a esquerda e só desloca 1. A força bruta, que começa
  pela esquerda, falha de imediato.
- **Ocorrência em toda posição (E)**: quem confere cada ocorrência caractere a caractere
  (força bruta, Horspool) paga O(n·m); até o `str.find` em C fica mais lento que o KMP em Python.
  O Rabin–Karp também confere cada uma, mas com `startswith` em C.
- **Vários padrões**: o tempo do Aho–Corasick quase não muda de 1 para 50 padrões (uma leitura
  do texto), enquanto o KMP repetido cresce linearmente: com 50 padrões, ~22× mais lento.
- **`str.find`** em C (no CPython, uma combinação de Boyer–Moore–Horspool com o algoritmo
  *two-way* de Crochemore–Perrin) é, nos cenários A a D, de 10 a 100× mais rápido que o melhor
  laço em Python: use-o na vida real; os algoritmos daqui servem para entender **por que** ele é
  rápido (e o cenário E mostra que nem ele escapa de conferir cada ocorrência).

## Referências

- KNUTH, D. E.; MORRIS, J. H.; PRATT, V. R. Fast pattern matching in strings. *SIAM Journal on
  Computing*, v. 6, n. 2, p. 323–350, 1977.
- KARP, R. M.; RABIN, M. O. Efficient randomized pattern-matching algorithms. *IBM Journal of
  Research and Development*, v. 31, n. 2, p. 249–260, 1987.
- BOYER, R. S.; MOORE, J. S. A fast string searching algorithm. *Communications of the ACM*,
  v. 20, n. 10, p. 762–772, 1977.
- HORSPOOL, R. N. Practical fast searching in strings. *Software: Practice and Experience*,
  v. 10, n. 6, p. 501–506, 1980.
- AHO, A. V.; CORASICK, M. J. Efficient string matching: an aid to bibliographic search.
  *Communications of the ACM*, v. 18, n. 6, p. 333–340, 1975.
- GUSFIELD, D. *Algorithms on Strings, Trees, and Sequences*. Cambridge University Press, 1997.
  Capítulo 1 (algoritmo Z) e Capítulo 3.
- CORMEN, T. H. et al. *Algoritmos: Teoria e Prática*. 3. ed. Elsevier, 2012. Capítulo 32
  (Correspondência de cadeias).
- CROCHEMORE, M.; PERRIN, D. Two-way string-matching. *Journal of the ACM*, v. 38, n. 3,
  p. 650–674, 1991.
- Documentação do Python: [`re`](https://docs.python.org/pt-br/3/library/re.html) (lookahead
  `(?=...)`) e [`time.perf_counter`](https://docs.python.org/pt-br/3/library/time.html#time.perf_counter).

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
