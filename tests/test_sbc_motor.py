import itertools
import random
import unittest

from sbc import explicacao as X
from sbc.editor import Editor
from sbc.motor import DESCONHECIDO, ConsultaCancelada, Motor
from sbc.parser import carregar, ler_kb
from sbc.dialogo import PASTA_BASES

KB_PAI = """
BASE: Exemplo
META: z
VARIÁVEL a
    VALORES: 1, 2
REGRA R1: SE a = 1 E b = 1 ENTÃO x = ok
REGRA R2: SE x = ok E c = sim ENTÃO y = ok
REGRA R3: SE y = ok ENTÃO z = fim
REGRA R4: SE a = 2 ENTÃO z = outro
"""


def roteiro(respostas, log=None):
    """Função `perguntar` que responde segundo um dicionário e registra as perguntas feitas."""
    def f(p):
        if log is not None:
            log.append(p.atributo)
        r = respostas.get(p.atributo, DESCONHECIDO)
        return r
    return f


class TestEncadeamento(unittest.TestCase):
    def setUp(self):
        self.kb = ler_kb(KB_PAI)

    def test_para_frente_chega_ao_ponto_fixo(self):
        m = Motor(self.kb)
        for a, v in (("a", 1), ("b", 1), ("c", "sim")):
            m.informar(a, v)
        disparadas = m.encadear_para_frente()
        self.assertEqual(disparadas, ["R1", "R2", "R3"])
        self.assertEqual(m.valores("z"), ["fim"])

    def test_refracao_nao_dispara_duas_vezes(self):
        m = Motor(self.kb)
        for a, v in (("a", 1), ("b", 1), ("c", "sim")):
            m.informar(a, v)
        m.encadear_para_frente()
        self.assertEqual(m.encadear_para_frente(), [])
        self.assertEqual(len(m.disparadas), len(set(m.disparadas)))

    def test_para_tras_pergunta_so_o_necessario(self):
        log = []
        m = Motor(self.kb, roteiro({"a": 2}, log))
        r = m.consultar("z", "tras")
        self.assertTrue(r.estabelecida)
        self.assertEqual(r.valores, ["outro"] or r.valores)
        self.assertEqual(log, ["a"])                                  # R1..R3 nem foram necessárias

    def test_para_tras_percorre_cadeia(self):
        log = []
        m = Motor(self.kb, roteiro({"a": 1, "b": 1, "c": "sim"}, log))
        r = m.consultar("z", "tras")
        self.assertEqual(r.valores, ["fim"])
        self.assertEqual(log, ["a", "b", "c"])
        self.assertEqual(r.regras_disparadas, ["R1", "R2", "R3"])

    def test_desconhecido_impede_conclusao(self):
        m = Motor(self.kb, roteiro({"a": 1, "b": 1}))                  # c: «não sei»
        r = m.consultar("z", "tras")
        self.assertFalse(r.estabelecida)
        self.assertIn("c", m.desconhecidos)

    def test_nao_pergunta_duas_vezes_a_mesma_coisa(self):
        log = []
        m = Motor(self.kb, roteiro({"a": 1, "b": 2}, log))
        m.consultar("z", "tras")
        self.assertEqual(len(log), len(set(log)))

    def test_misto_aproveita_o_que_ja_se_sabe(self):
        log = []
        m = Motor(self.kb, roteiro({"b": 1, "c": "sim"}, log))
        m.informar("a", 1)
        r = m.consultar("z", "misto")
        self.assertEqual(r.valores, ["fim"])
        self.assertNotIn("a", log)

    def test_frente_pergunta_todas_as_perguntaveis(self):
        log = []
        m = Motor(self.kb, roteiro({"a": 1, "b": 1, "c": "sim"}, log))
        r = m.consultar("z", "frente")
        self.assertEqual(set(log), {"a", "b", "c"})
        self.assertEqual(r.valores, ["fim"])

    def test_tres_modos_concordam_em_todas_as_bases(self):
        """Com as mesmas respostas, frente, trás e misto chegam às mesmas conclusões para as metas —
        desde que não haja conflito (duas regras concluindo valores diferentes de uma variável de valor único,
        caso em que o resultado depende da ordem de disparo, que difere entre os modos)."""
        rng = random.Random(7)
        comparadas = {}
        for caminho in sorted(PASTA_BASES.glob("*.kb")):
            kb = carregar(caminho)
            for rodada in range(40):
                respostas = {}
                for nome, v in kb.variaveis.items():
                    if kb.perguntavel(nome):
                        respostas[nome] = rng.choice(v.valores) if v.valores else rng.choice([40, 90])
                if "orcamento" in respostas:
                    respostas["orcamento"] = rng.choice([500, 2000, 4000, 8000])
                if "temperatura" in respostas:
                    respostas["temperatura"] = rng.choice([40, 70, 80, 90])
                if "velocidade" in respostas:
                    respostas["velocidade"] = rng.choice([10, 100])
                resultados, conflito = {}, False
                for modo in ("frente", "tras", "misto"):
                    m = Motor(kb, roteiro(respostas))
                    for meta in kb.metas:
                        m.consultar(meta, modo)
                    conflito |= any(e.tipo == "conflito" for e in m.eventos)
                    resultados[modo] = {meta: sorted(map(str, m.valores(meta))) for meta in kb.metas}
                if conflito:
                    continue
                comparadas[caminho.stem] = comparadas.get(caminho.stem, 0) + 1
                with self.subTest(base=caminho.stem, rodada=rodada):
                    self.assertEqual(resultados["frente"], resultados["tras"])
                    self.assertEqual(resultados["tras"], resultados["misto"])
        self.assertGreaterEqual(min(comparadas.values()), 5, comparadas)
        self.assertEqual(len(comparadas), len(list(PASTA_BASES.glob("*.kb"))))

    def test_meta_com_valor_desejado(self):
        m = Motor(self.kb, roteiro({"a": 1, "b": 1, "c": "sim"}))
        self.assertTrue(m.consultar("z", "tras", desejado="fim").estabelecida)
        m2 = Motor(self.kb, roteiro({"a": 1, "b": 1, "c": "sim"}))
        self.assertFalse(m2.consultar("z", "tras", desejado="outro").estabelecida)

    def test_cancelar_propaga_excecao(self):
        def f(p):
            raise ConsultaCancelada()
        with self.assertRaises(ConsultaCancelada):
            Motor(self.kb, f).consultar("z", "tras")

    def test_ciclo_nao_trava(self):
        kb = ler_kb("REGRA R1: SE a = 1 ENTÃO b = 1\nREGRA R2: SE b = 1 ENTÃO a = 1\n"
                    "REGRA R3: SE c = 1 ENTÃO a = 1\n")
        m = Motor(kb, roteiro({"c": 1}))
        self.assertTrue(m.consultar("b", "tras").estabelecida)
        m = Motor(kb, roteiro({}))
        self.assertFalse(m.consultar("b", "tras").estabelecida)

    def test_variavel_multivalorada_acumula(self):
        kb = ler_kb("VARIÁVEL v\n    MULTIVALORADA: sim\n"
                    "REGRA R1: SE a = 1 ENTÃO v = x\nREGRA R2: SE a = 1 ENTÃO v = y\nREGRA R3: SE a = 2 ENTÃO v = w\n")
        for modo in ("frente", "tras", "misto"):
            m = Motor(kb, roteiro({"a": 1}))
            m.consultar("v", modo)
            self.assertEqual(sorted(m.valores("v")), ["x", "y"], modo)

    def test_estrategias_de_conflito(self):
        texto = ("REGRA G: SE a = 1 ENTÃO r = geral\n"
                 "REGRA E: SE a = 1 E b = 1 ENTÃO r = especifica\n"
                 "REGRA P [prioridade 9]: SE a = 1 ENTÃO r = prioritaria\n")
        esperado = {"ordem": "geral", "especificidade": "especifica", "prioridade": "prioritaria"}
        for est, valor in esperado.items():
            kb = ler_kb(texto)
            m = Motor(kb, estrategia=est)
            m.informar("a", 1)
            m.informar("b", 1)
            m.encadear_para_frente()
            self.assertEqual(m.valores("r")[0], valor, est)

    def test_reiniciar_mantem_fatos_iniciais(self):
        kb = ler_kb("FATO: a = 1\nREGRA R1: SE a = 1 ENTÃO b = 2\n")
        m = Motor(kb)
        m.encadear_para_frente()
        self.assertEqual(m.valores("b"), [2])
        m.reiniciar()
        self.assertEqual(m.valores("a"), [1])
        self.assertEqual(m.valores("b"), [])

    def test_esquecer_recalcula(self):
        m = Motor(self.kb)
        for a, v in (("a", 1), ("b", 1), ("c", "sim")):
            m.informar(a, v)
        m.encadear_para_frente()
        m.esquecer("c")
        self.assertEqual(m.valores("c"), [])
        self.assertEqual(m.valores("y"), [])
        self.assertEqual(m.valores("x"), [])        # derivados são recalculados na próxima inferência
        m.encadear_para_frente()
        self.assertEqual(m.valores("x"), ["ok"])


class TestExplicacao(unittest.TestCase):
    def setUp(self):
        self.kb = ler_kb(KB_PAI)
        self.perguntas = []
        self.m = Motor(self.kb, lambda p: (self.perguntas.append(p), {"a": 1, "b": 1, "c": "sim"}[p.atributo])[1])
        self.m.consultar("z", "tras")

    def test_como_mostra_cadeia_de_regras(self):
        t = X.como(self.m, "z")
        for rid in ("R3", "R2", "R1"):
            self.assertIn(rid, t)
        self.assertIn("informado pelo usuário", t)
        self.assertLess(t.index("R3"), t.index("R2"))
        self.assertLess(t.index("R2"), t.index("R1"))

    def test_como_de_fato_inexistente(self):
        self.assertIn("Não tenho", X.como(self.m, "w"))

    def test_arvore_como(self):
        arv = X.arvore_como(self.m, "z")
        self.assertEqual(arv["regra"], "R3")
        self.assertEqual(arv["premissas"][0]["regra"], "R2")
        self.assertEqual({p["atributo"] for p in arv["premissas"][0]["premissas"]}, {"x", "c"})

    def test_por_que_sobe_a_cadeia_de_objetivos(self):
        p = self.perguntas[0]                       # primeira pergunta: «a» (por causa de R1, dentro de R2, de R3)
        self.assertEqual(p.atributo, "a")
        n0 = X.por_que(self.m, p, 0)
        self.assertIn("R1", n0)
        n1 = X.por_que(self.m, p, 1)
        self.assertIn("R2", n1)
        n2 = X.por_que(self.m, p, 2)
        self.assertIn("R3", n2)
        self.assertIn("topo", X.por_que(self.m, p, 3))

    def test_por_que_nao(self):
        t = X.por_que_nao(self.m, "z", "outro")
        self.assertIn("R4", t)
        self.assertIn("falsa", t)
        self.assertIn("já tem o valor", t)
        kb = ler_kb(KB_PAI)
        m = Motor(kb)
        m.informar("a", 1)
        self.assertIn("desconhecido", X.por_que_nao(m, "z", "fim"))
        self.assertIn("Nenhuma regra", X.por_que_nao(m, "z", "inexistente"))

    def test_trilha_registra_eventos(self):
        t = X.trilha(self.m)
        self.assertIn("pergunta", t)
        self.assertIn("R1", t)
        self.assertIn("estabelecida", t)


class TestEditor(unittest.TestCase):
    def setUp(self):
        self.kb = ler_kb(KB_PAI)
        self.ed = Editor(self.kb)

    def test_adicionar_regra_declara_variaveis(self):
        (r,) = self.ed.adicionar_regra("SE k = 3 ENTÃO z = novo")
        self.assertIn("k", self.kb.variaveis)
        self.assertEqual(r.id, "R5")
        self.assertEqual(len(self.kb.regras), 5)

    def test_id_repetido(self):
        with self.assertRaises(ValueError):
            self.ed.adicionar_regra("SE k = 3 ENTÃO z = 1", rid="R1")

    def test_substituir_e_remover(self):
        self.ed.substituir_regra("R4", "SE a = 2 E b = 2 ENTÃO z = outro")
        self.assertEqual(len(self.kb.regra("R4").condicoes), 2)
        self.ed.remover_regra("R4")
        self.assertIsNone(self.kb.regra("R4"))
        with self.assertRaises(KeyError):
            self.ed.remover_regra("R4")

    def test_fatos(self):
        self.ed.adicionar_fato("a = 1")
        self.assertIn(("a", 1), self.kb.fatos)
        self.ed.remover_fato("a")
        self.assertEqual(self.kb.fatos, [])

    def test_validacao_detecta_problemas(self):
        self.ed.adicionar_regra("SE a = 1 E b = 1 ENTÃO x = ok", rid="R10")             # duplicada
        self.ed.adicionar_regra("SE a = 1 E b = 1 ENTÃO x = outro", rid="R11")          # contradiz
        self.ed.adicionar_regra("SE p = 1 ENTÃO q = 1", rid="R12")
        self.ed.adicionar_regra("SE q = 1 ENTÃO p = 1", rid="R13")                      # ciclo
        self.ed.definir_variavel("naoperguntavel", perguntavel=False)
        self.ed.adicionar_regra("SE naoperguntavel = 1 ENTÃO z = nunca", rid="R14")     # nunca dispara
        msgs = " | ".join(str(p) for p in self.ed.validar())
        self.assertIn("idênticas", msgs)
        self.assertIn("valores diferentes", msgs)
        self.assertIn("circular", msgs)
        self.assertIn("nunca dispara", msgs)

    def test_validacao_de_dominio(self):
        self.ed.adicionar_regra("SE a = 99 ENTÃO z = 1", rid="R20")
        self.assertTrue(any("não está entre os valores" in str(p) for p in self.ed.validar()))

    def test_base_dos_exemplos_sem_erros(self):
        for caminho in sorted(PASTA_BASES.glob("*.kb")):
            erros = [p for p in Editor(carregar(caminho)).validar() if p.nivel == "erro"]
            self.assertEqual(erros, [], caminho.name)


if __name__ == "__main__":
    unittest.main()
