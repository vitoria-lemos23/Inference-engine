import itertools
import tempfile
import unittest
from pathlib import Path

from sbc.dialogo import PASTA_BASES
from sbc.modelo import Condicao
from sbc.parser import ErroSintaxe, carregar, de_dict, escrever_kb, ler_kb, para_dict, parse_regra, salvar

BASES = sorted(PASTA_BASES.glob("*.kb"))


class TestCondicao(unittest.TestCase):
    def test_tres_valores(self):
        c = Condicao("a", "=", "x")
        self.assertIsNone(c.avaliar([]))
        self.assertTrue(c.avaliar(["x"]))
        self.assertFalse(c.avaliar(["y"]))

    def test_sem_acentos_e_maiusculas(self):
        self.assertTrue(Condicao("a", "=", "Médio").avaliar(["medio"]))

    def test_numericos(self):
        self.assertTrue(Condicao("n", "<", 10).avaliar([9]))
        self.assertFalse(Condicao("n", "<", 10).avaliar([10]))
        self.assertTrue(Condicao("n", ">=", 10).avaliar([10]))
        self.assertTrue(Condicao("n", "<=", "10").avaliar(["10"]))

    def test_negacao_e_em(self):
        self.assertTrue(Condicao("a", "em", ("x", "y")).avaliar(["y"]))
        self.assertFalse(Condicao("a", "em", ("x", "y"), negada=True).avaliar(["y"]))
        self.assertTrue(Condicao("a", "!=", "x").avaliar(["z"]))
        self.assertIsNone(Condicao("a", "!=", "x").avaliar([]))     # desconhecido não é «diferente»


class TestParserRegra(unittest.TestCase):
    def test_simples(self):
        (r,) = parse_regra("SE a = x E b > 3 ENTÃO c = y E d = z", "R1")
        self.assertEqual(len(r.condicoes), 2)
        self.assertEqual([(c.atributo, c.valor) for c in r.conclusoes], [("c", "y"), ("d", "z")])
        self.assertEqual(r.condicoes[1].valor, 3)

    def test_ou_expande_em_varias_regras(self):
        rs = parse_regra("SE a = 1 E b = 2 OU c = 3 ENTÃO d = 4", "R7")
        self.assertEqual([r.id for r in rs], ["R7", "R7.2"])
        self.assertEqual(len(rs[0].condicoes), 2)
        self.assertEqual(len(rs[1].condicoes), 1)

    def test_nao_como_valor_e_como_negacao(self):
        (r,) = parse_regra("SE voa = não E NÃO cor = azul ENTÃO x = não", "R1")
        self.assertEqual(r.condicoes[0].valor, "não")
        self.assertTrue(r.condicoes[1].negada)
        self.assertEqual(r.conclusoes[0].valor, "não")

    def test_e_ou_dentro_de_valores(self):
        (r,) = parse_regra("SE a = cabo e fonte E b = 1 ENTÃO c = disco desconectado ou sem sistema "
                           "E d = limpar espaço em disco", "R1")
        self.assertEqual(r.condicoes[0].valor, "cabo e fonte")
        self.assertEqual(r.conclusoes[0].valor, "disco desconectado ou sem sistema")
        self.assertEqual(r.conclusoes[1].valor, "limpar espaço em disco")

    def test_lista_em(self):
        (r,) = parse_regra("SE a EM [x, y z] E b NÃO EM [1, 2] ENTÃO c = 1", "R1")
        self.assertEqual(r.condicoes[0].operador, "em")
        self.assertEqual(r.condicoes[0].valor, ("x", "y z"))
        self.assertTrue(r.condicoes[1].negada)

    def test_aspas_e_simbolos(self):
        (r,) = parse_regra('SE renda = "$15 a $35k" E x ≠ 3 ENTÃO y = "a, b"', "R1")
        self.assertEqual(r.condicoes[0].valor, "$15 a $35k")
        self.assertEqual(r.condicoes[1].operador, "!=")
        self.assertEqual(r.conclusoes[0].valor, "a, b")

    def test_erros(self):
        for ruim in ["a = 1 ENTÃO b = 2", "SE a = 1", "SE a ENTÃO b = 2", "SE a = 1 ENTÃO b > 2",
                     "SE a EM x ENTÃO b = 1", "SE a = 1 ENTÃO"]:
            with self.assertRaises(ErroSintaxe, msg=ruim):
                parse_regra(ruim)


class TestArquivosKB(unittest.TestCase):
    def test_ha_bases_de_exemplo(self):
        self.assertGreaterEqual(len(BASES), 5)

    def test_todas_carregam_e_sao_consistentes(self):
        from sbc.editor import Editor
        for caminho in BASES:
            with self.subTest(base=caminho.stem):
                b = carregar(caminho)
                self.assertTrue(b.regras and b.metas)
                erros = [p for p in Editor(b).validar() if p.nivel == "erro"]
                self.assertEqual(erros, [])

    def test_ida_e_volta_kb(self):
        for caminho in BASES:
            with self.subTest(base=caminho.stem):
                b = carregar(caminho)
                b2 = ler_kb(escrever_kb(b))
                self.assertEqual([r.texto() for r in b.regras], [r.texto() for r in b2.regras])
                self.assertEqual([r.id for r in b.regras], [r.id for r in b2.regras])
                self.assertEqual(b.metas, b2.metas)
                self.assertEqual({k: v.valores for k, v in b.variaveis.items()},
                                 {k: v.valores for k, v in b2.variaveis.items()})

    def test_ida_e_volta_json(self):
        for caminho in BASES:
            with self.subTest(base=caminho.stem):
                b = carregar(caminho)
                with tempfile.TemporaryDirectory() as d:
                    p = Path(d) / "x.json"
                    salvar(b, p)
                    b2 = carregar(p)
                self.assertEqual([r.texto() for r in b.regras], [r.texto() for r in b2.regras])
                self.assertEqual(para_dict(b)["metas"], para_dict(b2)["metas"])

    def test_erro_com_numero_de_linha(self):
        with self.assertRaises(ErroSintaxe) as cm:
            ler_kb("BASE: x\nREGRA R1: SE a = 1 ENTÃO\n")
        self.assertIn("R1", str(cm.exception))

    def test_comentarios_e_explicacao_em_varias_linhas(self):
        b = ler_kb("# comentário\nREGRA R1: SE a = 1  # outro\n   E b = 2 ENTÃO c = 3\n"
                   "    EXPLICAÇÃO: primeira parte\n      segunda parte\n")
        r = b.regra("R1")
        self.assertEqual(len(r.condicoes), 2)
        self.assertEqual(r.explicacao, "primeira parte segunda parte")


if __name__ == "__main__":
    unittest.main()
