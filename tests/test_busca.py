"""Testes: bordas, exemplos clássicos e testes aleatórios contra força bruta e ``re``."""

import io
import random
import re
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from busca_texto import (  # noqa: E402
    ALGORITMOS,
    AhoCorasick,
    buscar,
    forca_bruta,
    funcao_prefixo,
    funcao_z,
    rabin_karp,
    rabin_karp_com_colisoes,
    str_find,
    tabela_horspool,
)
from busca_texto import benchmark, demo  # noqa: E402
from busca_texto.cli import principal  # noqa: E402

# ----------------------------------------------------------------- oráculos


def oraculo_re(texto: str, padrao: str) -> list[int]:
    """Lookahead de largura zero: acha ocorrências sobrepostas sem consumir o texto."""
    return [m.start() for m in re.finditer(f"(?={re.escape(padrao)})", texto)]


def oraculo_fatias(texto: str, padrao: str) -> list[int]:
    m = len(padrao)
    return [i for i in range(len(texto) - m + 1) if texto[i:i + m] == padrao]


ALFABETOS = ["ab", "abc", "aab", "01", "áàç", "αβ", "a\U0001F600"]


def cadeia(rnd: random.Random, alfabeto: str, maximo: int) -> str:
    return "".join(rnd.choices(alfabeto, k=rnd.randint(0, maximo)))


# ----------------------------------------------------------------- bordas


class TestBordas(unittest.TestCase):
    def test_padrao_vazio_ocorre_em_toda_posicao(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("abc", ""), [0, 1, 2, 3])
                self.assertEqual(f("", ""), [0])
                self.assertEqual(f("abc", ""), oraculo_re("abc", ""))

    def test_texto_vazio(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("", "a"), [])

    def test_padrao_maior_que_texto(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("abc", "abcd"), [])
                self.assertEqual(f("a", "aa"), [])

    def test_padrao_igual_ao_texto(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("banana", "banana"), [0])
                self.assertEqual(f("x", "x"), [0])

    def test_sobrepostas(self):
        casos = [
            ("aaaa", "aa", [0, 1, 2]),
            ("banana", "ana", [1, 3]),
            ("abababab", "abab", [0, 2, 4]),
            ("aaaaa", "a", [0, 1, 2, 3, 4]),
            ("abcabcabc", "abcabc", [0, 3]),
        ]
        for nome, f in ALGORITMOS.items():
            for texto, padrao, esperado in casos:
                with self.subTest(algoritmo=nome, texto=texto, padrao=padrao):
                    self.assertEqual(f(texto, padrao), esperado)

    def test_inicio_e_fim(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("abxab", "ab"), [0, 3])
                self.assertEqual(f("xyz", "z"), [2])
                self.assertEqual(f("xyz", "w"), [])

    def test_unicode(self):
        casos = [
            ("ação e reação", "ção", [1, 10]),
            ("😀a😀😀", "😀😀", [2]),          # fora do BMP: 1 caractere por emoji
            ("pão, pao, PÃO", "pão", [0]),     # sem normalização de caixa ou acento
            ("café café", "é", [9]),    # 'e' + acento combinante não é 'é'
            ("日本語の本", "本", [1, 4]),
        ]
        for nome, f in ALGORITMOS.items():
            for texto, padrao, esperado in casos:
                with self.subTest(algoritmo=nome, padrao=padrao):
                    self.assertEqual(f(texto, padrao), esperado)
                    self.assertEqual(f(texto, padrao), oraculo_re(texto, padrao))

    def test_caracteres_especiais_de_regex(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertEqual(f("a.b*c.b*", ".b*"), [1, 5])
                self.assertEqual(f("(a)(a)", "(a)"), [0, 3])
                self.assertEqual(f("x\ny\n", "\n"), [1, 3])

    def test_tipos_invalidos(self):
        for nome, f in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                self.assertRaises(TypeError, f, b"abc", "a")
                self.assertRaises(TypeError, f, "abc", None)
                self.assertRaises(TypeError, f, "abc", 1)
        self.assertRaises(TypeError, AhoCorasick, "abc")       # str solta, não coleção
        self.assertRaises(TypeError, AhoCorasick, ["a", 2])
        self.assertRaises(TypeError, AhoCorasick(["a"]).buscar, None)

    def test_buscar_por_nome(self):
        self.assertEqual(buscar("banana", "na"), [2, 4])
        self.assertEqual(buscar("banana", "na", "horspool"), [2, 4])
        with self.assertRaises(ValueError):
            buscar("banana", "na", "inexistente")


# ----------------------------------------------------------------- estruturas internas


class TestEstruturasInternas(unittest.TestCase):
    def test_funcao_prefixo(self):
        self.assertEqual(funcao_prefixo("ababaca"), [0, 0, 1, 2, 3, 0, 1])
        self.assertEqual(funcao_prefixo("aaaa"), [0, 1, 2, 3])
        self.assertEqual(funcao_prefixo("abcd"), [0, 0, 0, 0])
        self.assertEqual(funcao_prefixo(""), [])

    def test_funcao_prefixo_contra_definicao(self):
        rnd = random.Random(3)
        for _ in range(300):
            p = cadeia(rnd, "ab", 15)
            # maior k <= q tal que o prefixo de tamanho k é sufixo de p[:q + 1] (borda própria)
            esperado = [
                max(k for k in range(q + 1) if p[:k] == p[q + 1 - k:q + 1]) for q in range(len(p))
            ]
            self.assertEqual(funcao_prefixo(p), esperado, p)

    def test_funcao_z(self):
        self.assertEqual(funcao_z("aabcaabxaaaz"), [12, 1, 0, 0, 3, 1, 0, 0, 2, 2, 1, 0])
        self.assertEqual(funcao_z("aaaaa"), [5, 4, 3, 2, 1])
        self.assertEqual(funcao_z(""), [])
        self.assertEqual(funcao_z(["a", None, "a"]), [3, 0, 1])

    def test_funcao_z_contra_definicao(self):
        rnd = random.Random(4)
        for _ in range(300):
            s = cadeia(rnd, "abc", 20)
            esperado = []
            for i in range(len(s)):
                k = 0
                while i + k < len(s) and s[k] == s[i + k]:
                    k += 1
                esperado.append(k)
            self.assertEqual(funcao_z(s), esperado, s)

    def test_tabela_horspool(self):
        self.assertEqual(tabela_horspool("abcab"), {"a": 1, "b": 3, "c": 2})
        self.assertEqual(tabela_horspool("a"), {})
        self.assertEqual(tabela_horspool("aaab"), {"a": 1})

    def test_rabin_karp_modulo_pequeno_verifica_colisoes(self):
        rnd = random.Random(5)
        total_colisoes = 0
        for _ in range(300):
            texto = cadeia(rnd, "abcd", 60)
            padrao = cadeia(rnd, "abcd", 4) or "a"
            for modulo in (2, 3, 7, 101):
                ocorrencias, colisoes = rabin_karp_com_colisoes(texto, padrao, modulo=modulo)
                self.assertEqual(ocorrencias, oraculo_fatias(texto, padrao))
                total_colisoes += colisoes
        # com módulos minúsculos as colisões acontecem, e mesmo assim o resultado é exato
        self.assertGreater(total_colisoes, 1000)

    def test_rabin_karp_modulo_grande_sem_colisoes(self):
        rnd = random.Random(6)
        texto = "".join(rnd.choices("abcdefgh", k=50_000))
        padrao = texto[1234:1250]
        ocorrencias, colisoes = rabin_karp_com_colisoes(texto, padrao)
        self.assertEqual(ocorrencias, str_find(texto, padrao))
        self.assertEqual(colisoes, 0)

    def test_rabin_karp_parametros_invalidos(self):
        self.assertRaises(ValueError, rabin_karp, "abc", "b", modulo=1)
        self.assertRaises(ValueError, rabin_karp, "abc", "b", base=1)


# ----------------------------------------------------------------- aleatórios


class TestAleatorios(unittest.TestCase):
    def test_forca_bruta_contra_re_e_fatias(self):
        rnd = random.Random(10)
        for _ in range(2_000):
            alfabeto = rnd.choice(ALFABETOS)
            texto = cadeia(rnd, alfabeto, 40)
            padrao = cadeia(rnd, alfabeto, 5)
            esperado = oraculo_re(texto, padrao)
            self.assertEqual(forca_bruta(texto, padrao), esperado)
            self.assertEqual(oraculo_fatias(texto, padrao) if padrao else esperado, esperado)

    def test_todos_contra_forca_bruta_e_re(self):
        rnd = random.Random(11)
        for rodada in range(3_000):
            alfabeto = rnd.choice(ALFABETOS)
            texto = cadeia(rnd, alfabeto, 60)
            # metade das vezes o padrão é um trecho do texto (garante ocorrências)
            if texto and rodada % 2 == 0:
                i = rnd.randrange(len(texto))
                padrao = texto[i:i + rnd.randint(1, 8)]
            else:
                padrao = cadeia(rnd, alfabeto, 8)
            esperado = forca_bruta(texto, padrao)
            self.assertEqual(esperado, oraculo_re(texto, padrao))
            for nome, f in ALGORITMOS.items():
                self.assertEqual(f(texto, padrao), esperado,
                                 f"{nome}: texto={texto!r} padrao={padrao!r}")
            self.assertEqual(str_find(texto, padrao), esperado)

    def test_textos_periodicos(self):
        """Textos como (ab)^k e a^k exercitam bordas longas no KMP/Z e saltos curtos no Horspool."""
        for base in ("a", "ab", "aab", "abcab"):
            texto = base * 30 + "x" + base * 7
            for t in range(1, 3 * len(base) + 2):
                padrao = (base * 5)[:t]
                esperado = oraculo_re(texto, padrao)
                for nome, f in ALGORITMOS.items():
                    with self.subTest(algoritmo=nome, base=base, t=t):
                        self.assertEqual(f(texto, padrao), esperado)

    def test_texto_longo(self):
        rnd = random.Random(12)
        texto = "".join(rnd.choices("ab", k=20_000))
        for padrao in ("abba", "aaaaaaa", "ab" * 6, texto[777:800]):
            esperado = str_find(texto, padrao)
            for nome, f in ALGORITMOS.items():
                with self.subTest(algoritmo=nome, padrao=padrao):
                    self.assertEqual(f(texto, padrao), esperado)


# ----------------------------------------------------------------- Aho-Corasick


class TestAhoCorasick(unittest.TestCase):
    def esperado(self, texto: str, padroes: list[str]) -> list[tuple[int, str]]:
        return sorted((pos, p) for p in set(padroes) for pos in oraculo_re(texto, p))

    def test_exemplo_classico(self):
        # exemplo do artigo original: he, she, his, hers em "ushers"
        ac = AhoCorasick(["he", "she", "his", "hers"])
        self.assertEqual(ac.buscar("ushers"), [(1, "she"), (2, "he"), (2, "hers")])
        self.assertEqual(ac.buscar_por_padrao("ushers"),
                         {"he": [2], "she": [1], "his": [], "hers": [2]})

    def test_ordem_por_fim_e_mais_longo_primeiro(self):
        ac = AhoCorasick(["a", "aa", "aaa"])
        self.assertEqual(ac.buscar("aaa"),
                         [(0, "a"), (0, "aa"), (1, "a"), (0, "aaa"), (1, "aa"), (2, "a")])

    def test_padroes_que_sao_sufixos_e_prefixos_uns_dos_outros(self):
        padroes = ["abc", "bc", "c", "ab", "a", "bca", "cab"]
        texto = "abcabcab"
        self.assertEqual(sorted(AhoCorasick(padroes).buscar(texto)), self.esperado(texto, padroes))

    def test_duplicados_e_vazio(self):
        ac = AhoCorasick(["na", "na", "", "ba"])
        self.assertEqual(ac.padroes, ("na", "", "ba"))
        self.assertEqual(sorted(ac.buscar("bana")),
                         [(0, ""), (0, "ba"), (1, ""), (2, ""), (2, "na"), (3, ""), (4, "")])
        self.assertEqual(AhoCorasick([""]).buscar(""), [(0, "")])

    def test_sem_padroes(self):
        ac = AhoCorasick([])
        self.assertEqual(ac.buscar("qualquer texto"), [])
        self.assertEqual(ac.buscar_por_padrao("abc"), {})
        self.assertEqual(len(ac), 1)

    def test_aceita_iteraveis(self):
        self.assertEqual(sorted(AhoCorasick({"x", "y"}).buscar("xy")), [(0, "x"), (1, "y")])
        self.assertEqual(AhoCorasick(p for p in ["ab"]).buscar("aab"), [(1, "ab")])

    def test_quantidade_de_nos(self):
        # raiz + c-a-s-a + o (caso) + e-l-a (cela) = 1 + 4 + 1 + 3
        self.assertEqual(len(AhoCorasick(["casa", "caso", "cela"])), 9)
        self.assertIn("nos=9", repr(AhoCorasick(["casa", "caso", "cela"])))

    def test_aleatorio_contra_oraculo(self):
        rnd = random.Random(13)
        for _ in range(800):
            alfabeto = rnd.choice(ALFABETOS)
            texto = cadeia(rnd, alfabeto, 50)
            padroes = [cadeia(rnd, alfabeto, 5) for _ in range(rnd.randint(0, 8))]
            if texto:
                i = rnd.randrange(len(texto))
                padroes.append(texto[i:i + rnd.randint(1, 6)])
            obtido = AhoCorasick(padroes).buscar(texto)
            self.assertEqual(sorted(obtido), self.esperado(texto, padroes),
                             f"texto={texto!r} padroes={padroes!r}")
            # ordem: posição final não decrescente
            fins = [pos + len(p) for pos, p in obtido]
            self.assertEqual(fins, sorted(fins))


# ----------------------------------------------------------------- demo, benchmark e CLI


class TestExecucao(unittest.TestCase):
    def test_demo_executa(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            demo.executar()
        texto = saida.getvalue()
        self.assertIn("Aho-Corasick", texto)
        self.assertNotIn("DIVERGÊNCIA", texto)
        self.assertRegex(texto, r"'ana' +em 'ananas' +-> \[0, 2\]")

    def test_demo_contagens(self):
        minusculo = demo.TEXTO.lower()
        self.assertEqual(len(minusculo), len(demo.TEXTO))
        self.assertEqual(len(ALGORITMOS["kmp"](minusculo, "biblioteca")), 2)

    def test_benchmark_em_escala_reduzida(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            benchmark.tabela_padrao_unico(benchmark.montar_cenarios(escala=0.01), repeticoes=1)
            benchmark.tabela_varios_padroes(escala=0.01, quantidades=(1, 3), repeticoes=1)
        texto = saida.getvalue()
        for nome in ALGORITMOS:
            self.assertIn(nome, texto)
        self.assertIn("str.find (C)", texto)

    def test_medir_devolve_tempo_positivo(self):
        self.assertGreaterEqual(benchmark.medir(lambda: sum(range(100)), repeticoes=2), 0.0)

    def test_cli(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(principal(["demo"]), 0)
        erro = io.StringIO()
        with redirect_stderr(erro):
            self.assertEqual(principal(["outra-coisa"]), 2)
        self.assertIn("uso:", erro.getvalue())


if __name__ == "__main__":
    unittest.main()
