"""Testes das implementações próprias de ID3, C4.5 e CART e da extração de regras (Questões 1 e 2)."""
import itertools
import math
import unittest

from ia import arvores as A
from ia import regras as G
from ia.base import Base
from q1.executar import CLASSES, DOMINIOS
from tests.luger import ATRIBUTOS, base_luger


def ganho(base, atributo, linhas=None):
    linhas = base.linhas if linhas is None else linhas
    H = A.entropia(list(base.contar(linhas).values()))
    for v in base.dominios[atributo]:
        sub = [l for l in linhas if l[atributo] == v]
        if sub:
            H -= len(sub) / len(linhas) * A.entropia(list(base.contar(sub).values()))
    return H


class TestMedidas(unittest.TestCase):
    def test_entropia(self):
        self.assertAlmostEqual(A.entropia([5, 5]), 1.0)
        self.assertAlmostEqual(A.entropia([10, 0]), 0.0)
        self.assertAlmostEqual(A.entropia([1, 1, 1, 1]), 2.0)
        self.assertAlmostEqual(A.entropia([5, 3, 6]), 1.5306189948, places=9)

    def test_gini(self):
        self.assertAlmostEqual(A.gini([5, 5]), 0.5)
        self.assertAlmostEqual(A.gini([10, 0]), 0.0)
        self.assertAlmostEqual(A.gini([1, 1, 1, 1]), 0.75)

    def test_info_divisao(self):
        self.assertAlmostEqual(A.info_divisao([7, 7]), 1.0)
        self.assertAlmostEqual(A.info_divisao([14]), 0.0)

    def test_erros_adicionais_quinlan(self):
        # valores de referência do C4.5 (AddErrs, CF = 25%): N=6,e=0 -> 1.3, N=9,e=0 -> 1.9 (aprox.)
        self.assertAlmostEqual(A.erros_adicionais(6, 0), 6 * (1 - 0.25 ** (1 / 6)), places=6)
        self.assertGreater(A.erros_adicionais(10, 3), 0)
        self.assertLess(A.erros_adicionais(100, 3), A.erros_adicionais(10, 3) * 10)


class TestLuger(unittest.TestCase):
    """A tabela clássica de Luger (14 exemplos): ganhos publicados e raiz Renda."""

    def setUp(self):
        self.b = base_luger()

    def test_ganhos(self):
        esperado = {"História de Crédito": 0.266, "Dívida": 0.063, "Garantia": 0.206, "Renda": 0.966}
        for a, g in esperado.items():
            self.assertAlmostEqual(ganho(self.b, a), g, places=3, msg=a)

    def test_raiz_dos_tres_algoritmos(self):
        for alg in ("ID3", "C4.5", "CART"):
            raiz = A.construir(self.b, alg)[0]
            self.assertEqual(raiz.atributo, "Renda", alg)

    def test_id3_e_consistente_com_o_treino(self):
        raiz = A.construir(self.b, "ID3")[0]
        self.assertEqual(A.acuracia(raiz, self.b), 1.0)
        self.assertEqual(A.profundidade(raiz), 3)
        self.assertEqual(len(A.folhas(raiz)), 8)

    def test_folhas_do_id3_sao_puras_ou_sem_atributos(self):
        raiz = A.construir(self.b, "ID3")[0]
        for f in A.folhas(raiz):
            self.assertEqual(sum(1 for v in f.contagem.values() if v > 0), 1)

    def test_cart_e_binaria(self):
        raiz = A.construir(self.b, "CART")[0]

        def checa(no):
            if not no.folha:
                self.assertEqual(len(no.ramos), 2)
                for _, _, f in no.ramos:
                    checa(f)
        checa(raiz)

    def test_poda_nunca_aumenta_a_arvore(self):
        base = Base.de_csv("q1/dados/credito_ampliado.csv", "Risco", dominios=DOMINIOS, ordem_classes=CLASSES)
        cheia = A.construir(base, "C4.5")[0]
        podada = A.construir(base, "C4.5", podar=True)[0]
        self.assertLessEqual(len(A.folhas(podada)), len(A.folhas(cheia)))


class TestBaseAmpliada(unittest.TestCase):
    def setUp(self):
        self.b = Base.de_csv("q1/dados/credito_ampliado.csv", "Risco", dominios=DOMINIOS, ordem_classes=CLASSES)

    def test_formato_pedido_na_questao_1(self):
        self.assertEqual(len(self.b.linhas), 30)
        self.assertEqual(len(self.b.atributos), 6)
        cont = self.b.contar()
        self.assertTrue(all(v >= 5 for v in cont.values()), cont)       # as três classes bem representadas
        ids = [l["ID"] for l in self.b.linhas]
        self.assertEqual(ids, [f"E{i}" for i in range(1, 31)])
        self.assertGreaterEqual(len({tuple(l[a] for a in self.b.atributos) for l in self.b.linhas}), 29)

    def test_sem_conflitos(self):
        self.assertEqual(self.b.conflitos(), [])        # nenhum par de exemplos iguais com classes diferentes

    def test_original_do_luger_preservado(self):
        luger = base_luger()
        for i, l in enumerate(luger.linhas):
            for a in ATRIBUTOS:
                self.assertEqual(self.b.linhas[i][a], l[a], (i, a))
            self.assertEqual(self.b.linhas[i]["Risco"], l["Risco"])

    def test_regras_equivalem_a_arvore(self):
        for alg, podar in (("ID3", False), ("C4.5", False), ("C4.5", True), ("CART", False)):
            raiz = A.construir(self.b, alg, podar=podar)[0]
            regras = G.extrair_regras(raiz)
            self.assertEqual(len(regras), len(A.folhas(raiz)))
            for l in self.b.linhas:
                cls, r = G.classificar(regras, l, "?")
                self.assertEqual(cls, A.prever(raiz, l), (alg, podar, l["ID"]))
            # exatamente uma regra cobre cada exemplo (caminhos disjuntos)
            for l in self.b.linhas:
                self.assertEqual(sum(r.cobre(l) for r in regras), 1)
            self.assertEqual(sum(r.n for r in regras), 30)

    def test_regras_gravadas_em_q1_batem_com_o_codigo(self):
        meta, salvas = G.carregar_json("q1/resultados/regras_id3.json")
        atuais = G.extrair_regras(A.construir(self.b, "ID3")[0])
        self.assertEqual([r.para_dict() for r in salvas], [r.para_dict() for r in atuais])

    def test_dobras_estratificadas_e_reprodutiveis(self):
        a = list(A.gerar_dobras(self.b, 5, 3, 42))
        b = list(A.gerar_dobras(self.b, 5, 3, 42))
        self.assertEqual(a, b)
        for dobras in a:
            self.assertEqual(sorted(i for d in dobras for i in d), list(range(30)))
            for d in dobras:
                self.assertTrue(all(any(self.b.linhas[i]["Risco"] == c for i in d) for c in self.b.classes))

    def test_leave_one_out_tem_um_resultado_por_exemplo(self):
        acc, res = A.leave_one_out(self.b, "ID3")
        self.assertEqual(len(res), 30)
        self.assertEqual(acc, sum(r == p for _, r, p in res) / 30)


class TestSklearn(unittest.TestCase):
    def test_arvore_sklearn_concorda_na_raiz_e_acerta_o_treino(self):
        try:
            from sklearn.tree import DecisionTreeClassifier
        except ImportError:
            self.skipTest("scikit-learn indisponível")
        from ia.sk_utils import codificar, nomes_dummies, rotulos
        base = base_luger()
        X, y = codificar(base), rotulos(base)
        nomes = [f"{a}={v}" for a, v in nomes_dummies(base)]
        for crit in ("gini", "entropy"):
            m = DecisionTreeClassifier(criterion=crit, random_state=0).fit(X, y)
            self.assertEqual(m.score(X, y), 1.0)
            raiz = nomes[m.tree_.feature[0]]
            self.assertTrue(raiz.startswith("Renda"), (crit, raiz))


if __name__ == "__main__":
    unittest.main()
