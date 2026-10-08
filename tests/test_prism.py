"""Testes do PRISM, das métricas e das Questões 3 e 4 (com dados sintéticos de mesmo esquema)."""
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ia import metricas as M
from ia.base import Base
from ia.prism import cortes_frequencia_igual, faixa, prism
from tests.luger import base_luger
from tests.sintetico import pima_sintetico


class TestPrism(unittest.TestCase):
    def test_regras_puras_e_cobrem_tudo_em_base_consistente(self):
        b = base_luger()
        m = prism(b)
        for r in m.regras:
            self.assertEqual(r.acertos, r.n, r.texto())           # PRISM clássico: regras 100% puras
        for l in b.linhas:
            self.assertTrue(any(r.cobre(l) and r.classe == l["Risco"] for r in m.regras), l["ID"])
            self.assertEqual(m.prever(l), l["Risco"])

    def test_primeira_regra_do_luger_calculada_a_mao(self):
        """Classe Baixo: melhor condição inicial é Renda = Acima de $35k (5/6); depois História = Boa (3/3)."""
        b = base_luger()
        m = prism(b, rastrear=True)
        r1 = m.regras[0]
        self.assertEqual(r1.classe, "Baixo")
        self.assertEqual(r1.condicoes, [("Renda", "Acima de $35k"), ("História de Crédito", "Boa")])
        self.assertEqual((r1.n, r1.acertos), (3, 3))
        tabela = {(a, v): (p, t) for a, v, p, t in m.historico[0]["passos"][0]["tabela"]}
        self.assertEqual(tabela[("Renda", "Acima de $35k")], (5, 6))
        self.assertEqual(tabela[("Renda", "$0 a $15k")], (0, 4))

    def test_determinismo(self):
        b = base_luger()
        self.assertEqual([r.texto() for r in prism(b).regras], [r.texto() for r in prism(b).regras])

    def test_parametros_de_regularizacao(self):
        b = base_luger()
        puro = prism(b)
        curto = prism(b, max_condicoes=1)
        self.assertTrue(all(len(r.condicoes) <= 1 for r in curto.regras))
        raro = prism(b, cobertura_min=2)
        self.assertLessEqual(len(raro.regras), len(puro.regras))
        self.assertTrue(all(r.acertos >= 2 for r in raro.regras[1:]))       # (a 1ª regra é sempre mantida)
        folgado = prism(b, precisao_min=0.7)
        self.assertLessEqual(max(len(r.condicoes) for r in folgado.regras), max(len(r.condicoes) for r in puro.regras))

    def test_conflito_resolvido_por_laplace(self):
        b = base_luger()
        m = prism(b)
        ex = b.linhas[0]
        cls, regra = m.prever(ex, com_regra=True)
        self.assertEqual(cls, regra.classe)

    def test_discretizacao(self):
        v = list(range(1, 101))
        c = cortes_frequencia_igual(v, 4)
        self.assertEqual(len(c), 3)
        self.assertEqual([faixa(x, c) for x in (1, 25, 26, 50, 51, 75, 76, 100)][0], 0)
        contagem = [0] * 4
        for x in v:
            contagem[faixa(x, c)] += 1
        self.assertTrue(all(abs(k - 25) <= 1 for k in contagem), contagem)
        self.assertEqual(cortes_frequencia_igual([5] * 10, 3), [5])   # sem repetir cortes


class TestMetricas(unittest.TestCase):
    def test_contra_sklearn(self):
        from sklearn import metrics as skm
        rng = np.random.default_rng(1)
        for _ in range(20):
            y = rng.integers(0, 2, 60)
            p = rng.integers(0, 2, 60)
            s = rng.random(60)
            m = M.metricas(y, p)
            self.assertAlmostEqual(m["acuracia"], skm.accuracy_score(y, p))
            self.assertAlmostEqual(m["precisao"], skm.precision_score(y, p, zero_division=0))
            self.assertAlmostEqual(m["recall"], skm.recall_score(y, p, zero_division=0))
            self.assertAlmostEqual(m["f1"], skm.f1_score(y, p, zero_division=0))
            self.assertAlmostEqual(m["f1_macro"], skm.f1_score(y, p, average="macro", zero_division=0))
            self.assertAlmostEqual(m["mcc"], skm.matthews_corrcoef(y, p))
            self.assertAlmostEqual(M.auc_roc(y, s), skm.roc_auc_score(y, s))
            tn, fp, fn, tp = skm.confusion_matrix(y, p).ravel()
            self.assertEqual((m["VN"], m["FP"], m["FN"], m["VP"]), (tn, fp, fn, tp))

    def test_casos_limite(self):
        m = M.metricas([0, 0, 0], [0, 0, 0])
        self.assertEqual((m["precisao"], m["recall"], m["f1"]), (0.0, 0.0, 0.0))
        self.assertTrue(math.isnan(M.auc_roc([1, 1], [0.2, 0.3])))      # AUC indefinida sem negativos


class TestQuestoes3e4(unittest.TestCase):
    """Executa os pipelines completos (grade reduzida) com dados SINTÉTICOS e confere artefatos e coerência."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.csv = cls.dir / "diabetes.csv"
        pima_sintetico().to_csv(cls.csv, index=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_q3_e_q4(self):
        import warnings
        warnings.simplefilter("ignore")
        from q3 import executar as q3
        from q4 import executar as q4
        s3, s4 = self.dir / "q3", self.dir / "q4"
        m3 = q3.main(["--dados", str(self.csv), "--saida", str(s3), "--relatorio", str(self.dir / "r3.md"), "--rapido"])
        for nome in ("arvore.png", "arvore.txt", "regras.txt", "regras.json", "metricas.json", "divisao.json",
                     "matriz_confusao.png", "curva_roc.png"):
            self.assertTrue((s3 / nome).exists(), nome)
        for k in ("acuracia", "precisao", "recall", "f1"):
            self.assertTrue(0 <= m3["teste"][k] <= 1)
        self.assertEqual(m3["teste"]["VP"] + m3["teste"]["FP"] + m3["teste"]["FN"] + m3["teste"]["VN"], 192)
        div = json.loads((s3 / "divisao.json").read_text())
        self.assertEqual(len(div["treino"]) + len(div["teste"]), 768)
        self.assertFalse(set(div["treino"]) & set(div["teste"]))
        regras = json.loads((s3 / "regras.json").read_text())["regras"]
        self.assertEqual(sum(r["n"] for r in regras), 576)             # as regras particionam o treino
        self.assertEqual(sum(r["n_teste"] for r in regras), 192)       # ... e o teste
        rel3 = (self.dir / "r3.md").read_text()
        self.assertIn("SE ", rel3)
        self.assertNotIn("nan%", rel3.lower().replace("—", ""))

        m4 = q4.main(["--dados", str(self.csv), "--saida", str(s4), "--relatorio", str(self.dir / "r4.md"),
                      "--q3", str(s3 / "metricas.json"), "--rapido"])
        self.assertEqual(m4["teste"]["VP"] + m4["teste"]["FP"] + m4["teste"]["FN"] + m4["teste"]["VN"], 192)
        self.assertGreater(m4["n_regras_classico"], m4["n_regras"] - 1)
        self.assertGreater(m4["classico_treino"]["acuracia"], 0.9)       # PRISM puro decora o treino
        self.assertTrue((s4 / "diabetes_prism.kb").exists())
        rel4 = (self.dir / "r4.md").read_text()
        self.assertIn("PRISM", rel4)
        self.assertIn("Árvore de decisão (Questão 3)", rel4)

        # a base .kb gerada é carregável e decide como o modelo (cada regra vira regra do shell)
        from sbc.editor import Editor
        from sbc.parser import carregar
        kb = carregar(s4 / "diabetes_prism.kb")
        self.assertEqual(len(kb.regras), m4["n_regras"])
        self.assertEqual([p for p in Editor(kb).validar() if p.nivel == "erro"], [])


if __name__ == "__main__":
    unittest.main()
