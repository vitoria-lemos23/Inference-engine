import tempfile
import unittest
from pathlib import Path

from sbc import nl
from sbc.dialogo import PASTA_BASES, Dialogo
from sbc.parser import carregar


def sessao(base, comandos, modo="misto"):
    """Executa um roteiro de entradas no diálogo e devolve toda a saída como um único texto."""
    saida, it = [], iter(comandos)

    def entrada(_):
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    d = Dialogo(carregar(PASTA_BASES / f"{base}.kb") if isinstance(base, str) else base,
                entrada=entrada, saida=saida.append, modo=modo, eco=True)
    d.executar()
    return "\n".join(saida), d


class TestRespostas(unittest.TestCase):
    def test_booleanas(self):
        op = ["sim", "não"]
        for txt, esp in [("sim", "sim"), ("Sim!", "sim"), ("claro", "sim"), ("não", "não"), ("nao", "não"),
                         ("n", "não"), ("1", "sim"), ("2", "não"), ("acho que não", "não")]:
            self.assertEqual(nl.interpretar_resposta(txt.rstrip("!"), op), ("valor", esp), txt)

    def test_opcoes_por_numero_nome_e_aproximacao(self):
        op = ["Curto", "Médio", "Longo"]
        self.assertEqual(nl.interpretar_resposta("2", op), ("valor", "Médio"))
        self.assertEqual(nl.interpretar_resposta("medio", op), ("valor", "Médio"))
        self.assertEqual(nl.interpretar_resposta("acho que é longo", op), ("valor", "Longo"))
        self.assertEqual(nl.interpretar_resposta("curtto", op), ("valor", "Curto"))
        self.assertEqual(nl.interpretar_resposta("banana", op)[0], "invalido")

    def test_comandos_durante_pergunta(self):
        self.assertEqual(nl.interpretar_resposta("por quê?", ["a"]), ("por_que",))
        self.assertEqual(nl.interpretar_resposta("não sei", ["sim", "não"]), ("desconhecido",))
        self.assertEqual(nl.interpretar_resposta("cancelar", ["a"]), ("cancelar",))

    def test_opcao_literal_vence_palavra_de_comando(self):
        self.assertEqual(nl.interpretar_resposta("indiferente", ["android", "ios", "indiferente"]),
                         ("valor", "indiferente"))

    def test_numeros(self):
        for txt, n in [("3500", 3500), ("R$ 2.500", 2500), ("1.234,5", 1234.5), ("uns 80 graus", 80)]:
            self.assertEqual(nl.interpretar_resposta(txt, None, "numero"), ("valor", n), txt)
        self.assertEqual(nl.interpretar_resposta("muito", None, "numero")[0], "invalido")


class TestFatosEmLinguagemNatural(unittest.TestCase):
    def test_varios_fatos_numa_frase(self):
        b = carregar(PASTA_BASES / "credito.kb")
        f = nl.extrair_fatos("a renda é de $0 a $15k e o tempo de emprego é curto", b)
        self.assertEqual(f, [("Renda", "$0 a $15k"), ("Tempo de Emprego", "Curto")])
        f = nl.extrair_fatos("sei que a história de crédito é boa, dívida baixa", b)
        self.assertEqual(f, [("História de Crédito", "Boa"), ("Dívida", "Baixa")])

    def test_negacao_em_variaveis_sim_nao(self):
        b = carregar(PASTA_BASES / "animais.kb")
        f = dict(nl.extrair_fatos("o animal tem penas e não voa, vive na água", b))
        self.assertEqual(f, {"tem_penas": "sim", "voa": "não", "vive_na_agua": "sim"})
        f = dict(nl.extrair_fatos("não tem penas, tem pelos e amamenta", b))
        self.assertEqual(f, {"tem_penas": "não", "tem_pelos": "sim", "amamenta": "sim"})

    def test_numero_e_valor_sem_nome_da_variavel(self):
        b = carregar(PASTA_BASES / "celular.kb")
        f = dict(nl.extrair_fatos("meu orçamento é de R$ 2.500 e prefiro android, uso para jogos", b))
        self.assertEqual(f, {"orcamento": 2500, "uso": "jogos", "sistema": "android"})


class TestComandos(unittest.TestCase):
    def setUp(self):
        self.kb = carregar(PASTA_BASES / "animais.kb")

    def intencao(self, txt):
        return nl.reconhecer_comando(txt, self.kb)[0]

    def test_intencoes(self):
        casos = {
            "sair": "sair", "ajuda": "ajuda", "consultar": "consultar", "qual é o animal?": "consultar",
            "por quê?": "por_que", "como": "como", "como chegou ao animal?": "como",
            "por que não animal = girafa?": "por_que_nao", "regras": "regras", "regra A1": "regra",
            "remover regra A1": "rem_regra", "SE a = 1 ENTÃO b = 2": "add_regra",
            "adicionar regra R50: SE a = 1 ENTÃO b = 2": "add_regra", "editar regra A1: SE a = 1 ENTÃO b = 2": "edit_regra",
            "adicionar fato voa = sim": "add_fato", "o que você sabe?": "fatos", "trilha": "trilha",
            "validar": "validar", "salvar x.kb": "salvar", "bases": "bases", "carregar animais": "carregar",
            "limpar": "limpar", "modo para frente": "modo", "editor": "editor", "variáveis": "variaveis",
        }
        for txt, esperado in casos.items():
            self.assertEqual(self.intencao(txt), esperado, txt)

    def test_argumentos(self):
        self.assertEqual(nl.reconhecer_comando("remover regra A1", self.kb), ("rem_regra", {"id": "A1"}))
        self.assertEqual(nl.reconhecer_comando("modo para trás", self.kb)[1].get("modo"), "tras")


class TestDialogoCompleto(unittest.TestCase):
    def test_consulta_para_tras_com_por_que_e_como(self):
        txt, d = sessao("animais", [
            "consultar animal", "não", "sim", "sim", "por quê?", "sim", "não sei"], modo="tras")
        self.assertIn("pelos", txt)                       # primeira pergunta
        self.assertIn("Estou perguntando", txt)           # explicação do «por quê?»
        self.assertIn("regra", txt)

    def test_credito_conclui_e_explica(self):
        txt, d = sessao("credito", [
            "consultar", "$15 a $35k", "Boa", "Baixa", "como", "por que não risco = alto?"], modo="tras")
        self.assertIn("Risco = Baixo", txt)
        self.assertIn("concluído pela regra R5", txt)
        self.assertIn("«Risco» já tem o valor Baixo", txt)

    def test_nao_sei_e_nova_tentativa(self):
        txt, _ = sessao("credito", ["consultar", "$15 a $35k", "Boa", "não sei"], modo="tras")
        self.assertIn("Não consegui estabelecer", txt)

    def test_cancelar(self):
        txt, _ = sessao("credito", ["consultar", "cancelar", "fatos"], modo="tras")
        self.assertIn("cancelada", txt.lower())

    def test_informar_em_linguagem_natural_e_conclusao_imediata(self):
        txt, d = sessao("credito", ["a renda é de $0 a $15k e o tempo de emprego é curto"])
        self.assertIn("Com isso concluí: Risco = Alto", txt)
        self.assertEqual(d.motor.valores("Risco"), ["Alto"])

    def test_editar_a_base_pelo_dialogo(self):
        txt, d = sessao("animais", [
            "adicionar regra: SE tem_penas = sim E nada_bem = sim E voa = não ENTÃO animal = ave aquática",
            "remover regra A1", "validar", "regra A2"])
        self.assertIn("adicionada", txt)
        self.assertIn("removida", txt)
        self.assertIsNone(d.base.regra("A1"))
        self.assertTrue(any("ave aquática" in str(c.valor) for r in d.base.regras for c in r.conclusoes))

    def test_regra_invalida_nao_altera_a_base(self):
        txt, d = sessao("animais", ["adicionar regra: SE tem_penas ENTÃO"])
        n = len(carregar(PASTA_BASES / "animais.kb").regras)
        self.assertEqual(len(d.base.regras), n)

    def test_salvar_e_recarregar(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "minha.kb"
            _, d = sessao("animais", ["adicionar fato tem_penas = sim", f"salvar {destino}"])
            self.assertTrue(destino.exists())
            b2 = carregar(destino)
            self.assertIn(("tem_penas", "sim"), b2.fatos)
            txt, d2 = sessao(b2, ["sobre"])
            self.assertIn("Classificação de animais", txt)

    def test_carregar_outra_base(self):
        txt, d = sessao("animais", ["carregar celular", "sobre"])
        self.assertEqual(d.base.nome, "Escolha de smartphone")

    def test_editor_guiado(self):
        txt, d = sessao("credito", ["editor", "1", "8", "0"])
        self.assertIn("Editor", txt)

    def test_roda_todas_as_bases_nos_tres_modos_sem_erro(self):
        """Usuário automático: responde a cada pergunta com a escolha (cíclica) de uma opção da própria tela."""
        import re
        for caminho in sorted(PASTA_BASES.glob("*.kb")):
            for modo in ("frente", "tras", "misto"):
                for deslocamento in (0, 1, 2):
                    saida, extras = [], iter(["fatos", "trilha", "regras", "variáveis", "validar"])
                    primeira = [True]

                    def entrada(_):
                        if primeira[0]:
                            primeira[0] = False
                            return "consultar"
                        if saida and saida[-1].strip().startswith("(responda"):
                            opcoes = []
                            for linha in reversed(saida):
                                m = re.match(r"^\s+(\d+)\. (.*)$", linha)
                                if m:
                                    opcoes.insert(0, m.group(2))
                                elif linha.startswith("? "):
                                    break
                            return opcoes[deslocamento % len(opcoes)].strip('"') if opcoes else "1000"
                        try:
                            return next(extras)
                        except StopIteration:
                            raise EOFError from None

                    kb = carregar(caminho)
                    d = Dialogo(kb, entrada=entrada, saida=saida.append, modo=modo)
                    d.executar()
                    txt = "\n".join(saida)
                    with self.subTest(base=caminho.stem, modo=modo, desloc=deslocamento):
                        self.assertNotIn("Traceback", txt)
                        self.assertRegex(txt, r"Conclusão|Não consegui estabelecer")
                        self.assertNotIn("Não reconheci", txt)


if __name__ == "__main__":
    unittest.main()
