"""Integração Questões 1 ↔ 5: a base de conhecimento do shell, gerada das regras ID3, decide como a árvore."""
import itertools
import tempfile
import unittest
from pathlib import Path

from ia import arvores as A
from ia.base import Base
from q1.executar import CLASSES, DOMINIOS
from sbc.dialogo import PASTA_BASES
from sbc.importar import importar
from sbc.motor import Motor
from sbc.parser import carregar, escrever_kb, ler_kb


class TestCreditoArvoreXShell(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = Base.de_csv("q1/dados/credito_ampliado.csv", "Risco", dominios=DOMINIOS, ordem_classes=CLASSES)
        cls.raiz = A.construir(cls.base, "ID3")[0]
        cls.kb = carregar(PASTA_BASES / "credito.kb")
        cls.espaco = [dict(zip(cls.base.atributos, c))
                      for c in itertools.product(*[cls.base.dominios[a] for a in cls.base.atributos])]

    def _classificar_no_shell(self, exemplo, modo):
        m = Motor(self.kb, perguntar=lambda p: exemplo[p.atributo])
        for a, v in exemplo.items():
            m.informar(a, v)
        m.consultar("Risco", modo)
        return m.valores("Risco")

    def test_216_combinacoes(self):
        self.assertEqual(len(self.espaco), 216)
        cobertas = 0
        for ex in self.espaco:
            trilha, folha = A.caminho_decisao(self.raiz, ex)
            vistos = self._classificar_no_shell(ex, "frente")
            if folha.folha and len(trilha) and self._cobre(ex):
                cobertas += 1
                self.assertEqual(vistos, [A.prever(self.raiz, ex)], ex)
            else:
                self.assertEqual(vistos, [], ex)       # sem ramo na árvore => nenhuma regra dispara
        self.assertGreater(cobertas, 100)

    def _cobre(self, ex):
        no = self.raiz
        while not no.folha:
            for _, valores, filho in no.ramos:
                if ex[no.atributo] in valores:
                    no = filho
                    break
            else:
                return False
        return True

    def test_modos_para_tras_e_misto_tambem(self):
        for ex in self.espaco[::7]:
            esperado = self._classificar_no_shell(ex, "frente")
            for modo in ("tras", "misto"):
                self.assertEqual(self._classificar_no_shell(ex, modo), esperado, (modo, ex))

    def test_para_tras_nao_repete_perguntas_e_faz_menos_que_o_total(self):
        medias = []
        for ex in self.espaco:
            perguntas = []
            m = Motor(self.kb, perguntar=lambda p: (perguntas.append(p.atributo), ex[p.atributo])[1])
            m.consultar("Risco", "tras")
            self.assertEqual(len(set(perguntas)), len(perguntas))
            medias.append(len(perguntas))
        self.assertLess(sum(medias) / len(medias), len(self.base.atributos))     # em média pergunta menos que tudo

    def test_importador_reproduz_o_arquivo_versionado(self):
        kb = importar("q1/resultados/regras_id3.json", "q1/dados/credito_ampliado.csv", "Risco",
                      self.kb.nome, self.kb.descricao, dominios=DOMINIOS, ordem_classes=CLASSES,
                      perguntas={a: v.pergunta for a, v in self.kb.variaveis.items()})
        self.assertEqual([r.texto() for r in kb.regras], [r.texto() for r in self.kb.regras])

    def test_kb_de_outra_arvore(self):
        """O shell aceita qualquer base de regras: aqui, a da árvore CART da Questão 1."""
        kb = importar("q1/resultados/regras_cart.json", "q1/dados/credito_ampliado.csv", "Risco", "CART",
                      dominios=DOMINIOS, ordem_classes=CLASSES)
        kb = ler_kb(escrever_kb(kb))
        raiz = A.construir(self.base, "CART")[0]
        for l in self.base.linhas:
            m = Motor(kb)
            for a in self.base.atributos:
                m.informar(a, l[a])
            m.consultar("Risco", "frente")
            self.assertEqual(m.valores("Risco"), [A.prever(raiz, l)])


if __name__ == "__main__":
    unittest.main()
