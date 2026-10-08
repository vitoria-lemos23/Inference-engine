"""Interface com o usuário: diálogo em linguagem natural (português) no terminal.

A classe ``Dialogo`` junta os módulos do shell: base de conhecimento, editor, engenho de inferência e
explicação. As entradas/saídas são injetáveis (``entrada``/``saida``), o que permite usá-la no terminal,
em scripts de teste e na geração de transcrições de exemplo.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import explicacao as X
from . import nl
from .editor import Editor
from .modelo import BaseConhecimento, fmt_valor, norm
from .motor import DESCONHECIDO, ConsultaCancelada, Motor, Pergunta
from .parser import ErroSintaxe, carregar, parse_fato, salvar

PASTA_BASES = Path(__file__).parent / "bases"
MODOS = {"frente": "para frente (dirigido por dados)", "tras": "para trás (dirigido por meta)",
         "misto": "misto (frente + trás)"}


def listar_bases(pasta=PASTA_BASES):
    """[(nome_do_arquivo_sem_extensão, caminho, título, descrição)] das bases .kb da pasta."""
    out = []
    for p in sorted(Path(pasta).glob("*.kb")):
        try:
            b = carregar(p)
            out.append((p.stem, p, b.nome, b.descricao))
        except Exception as e:  # base com erro não derruba a listagem
            out.append((p.stem, p, p.stem, f"(erro ao ler: {e})"))
    return out


class Dialogo:
    def __init__(self, base=None, entrada=None, saida=None, modo="misto", pasta_bases=PASTA_BASES, eco=False):
        self._entrada = entrada or input
        self._saida = saida or print
        self.eco = eco
        self.pasta_bases = pasta_bases
        self.modo = modo
        self.caminho = None
        self.base = None
        self.motor = None
        self.editor = None
        self.ultima_meta = None
        self._pergunta_atual = None
        self.pergunta_em_curso = None
        self._nivel_por_que = 0
        if base is not None:
            self.carregar_base(base)

    # ================================================================== entrada/saída
    def _dizer(self, texto=""):
        for linha in str(texto).split("\n"):
            self._saida(linha)

    def _ler(self, prompt="você> "):
        txt = self._entrada(prompt)
        if self.eco:
            self._saida(f"{prompt}{txt}")
        return txt

    # ================================================================== base
    def carregar_base(self, base, caminho=None):
        self.base = base
        self.caminho = caminho
        self.editor = Editor(base)
        self.motor = Motor(base, perguntar=self._perguntar)
        self.ultima_meta = None
        self._pergunta_atual = None

    def _refazer_motor(self):
        """Depois de editar a base: recalcula o que foi derivado, mantendo o que o usuário informou."""
        self.motor.esquecer()

    # ================================================================== laço principal
    def executar(self, banner=True):
        if banner:
            self._banner()
        while True:
            try:
                linha = self._ler()
            except (EOFError, KeyboardInterrupt):
                self._dizer("\nAté logo!")
                return
            try:
                if not self.processar(linha):
                    return
            except ConsultaCancelada:
                self._dizer("Consulta cancelada.")
            except (EOFError, KeyboardInterrupt):      # fim da entrada no meio de uma pergunta
                self._dizer("\nAté logo!")
                return

    def _banner(self):
        b = self.base
        self._dizer("=" * 72)
        self._dizer(" SHELL DE SISTEMA BASEADO EM CONHECIMENTO")
        if b:
            self._dizer(f" Base carregada: {b.nome}   ({len(b.regras)} regras, {len(b.variaveis)} variáveis)")
            if b.descricao:
                self._dizer(f" {b.descricao}")
        else:
            self._dizer(" Nenhuma base carregada — digite «bases» para ver os exemplos e «carregar <nome>».")
        self._dizer(f" Encadeamento: {MODOS[self.modo]}")
        self._dizer(" Digite «ajuda» para ver o que posso fazer, ou «consultar» para começar.")
        self._dizer("=" * 72)

    # ================================================================== processamento de um comando
    def processar(self, linha):
        """Interpreta uma linha. Retorna False quando o usuário pede para sair."""
        intencao, a = nl.reconhecer_comando(linha, self.base or BaseConhecimento())
        if intencao == "vazio":
            return True
        if intencao == "sair":
            self._dizer("Até logo!")
            return False
        if intencao == "ajuda":
            self._dizer(nl.AJUDA)
            return True
        if intencao in ("bases", "carregar"):
            return self._cmd_bases(a) or True
        if self.base is None:
            self._dizer("Primeiro carregue uma base: «bases» lista os exemplos; «carregar <nome>» abre uma.")
            return True
        h = getattr(self, f"_cmd_{intencao}", None)
        if h is None:
            self._dizer("Não entendi. Digite «ajuda» para ver o que posso fazer.")
            return True
        h(a)
        return True

    # ------------------------------------------------------------------ perguntas do motor
    def _perguntar(self, p: Pergunta):
        self.pergunta_em_curso = p            # permite a «usuários automáticos» (testes, transcrições) saber o que se pergunta
        try:
            return self._perguntar_loop(p)
        finally:
            self.pergunta_em_curso = None

    def _perguntar_loop(self, p: Pergunta):
        self._pergunta_atual = p
        nivel = 0
        self._dizer("")
        self._dizer(f"? {p.texto}")
        if p.opcoes:
            for i, o in enumerate(p.opcoes, 1):
                self._dizer(f"    {i}. {fmt_valor(o)}")
        self._dizer("  (responda com o valor ou o número; «por quê?» explica a pergunta; «não sei»; «cancelar»)")
        while True:
            txt = self._ler()
            t = norm(txt)
            if t in ("fatos", "o que voce sabe", "memoria"):
                self._dizer(X.resumo_fatos(self.motor))
                continue
            if t in ("regras", "trilha", "historico"):
                self._dizer(self._texto_regras() if t == "regras" else X.trilha(self.motor))
                continue
            if t in ("ajuda", "help"):
                self._dizer(nl.AJUDA)
                continue
            tipo = nl.interpretar_resposta(txt, p.opcoes, p.tipo)
            if tipo[0] == "valor":
                v = tipo[1]
                if p.opcoes is not None and norm(txt) != norm(v):
                    self._dizer(f"  (entendi: {fmt_valor(v)})")
                return v
            if tipo[0] == "por_que":
                self._dizer(X.por_que(self.motor, p, nivel))
                nivel += 1
                continue
            if tipo[0] == "como":
                self._dizer("Ainda estou coletando dados; use «o que você sabe?» para ver o que já tenho.")
                continue
            if tipo[0] == "desconhecido":
                return DESCONHECIDO
            if tipo[0] == "cancelar":
                raise ConsultaCancelada()
            self._dizer(f"  {tipo[1]}")

    # ------------------------------------------------------------------ consulta
    def _cmd_consultar(self, a):
        modo = a.get("modo") or self.modo
        meta = a.get("meta")
        metas = [meta] if meta else list(self.base.metas)
        if not metas:
            self._dizer("Qual variável devo determinar? Diga, por exemplo, «consultar <variável>». "
                        "Variáveis: " + ", ".join(v.rotulo for v in self.base.variaveis.values()))
            return
        for m in metas:
            self._dizer(f"\nIniciando a consulta sobre «{self.base.rotulo(m)}» — encadeamento {MODOS[modo]}.")
            res = self.motor.consultar(m, modo)
            self.ultima_meta = res.meta
            self._relatar(res)

    def _relatar(self, res):
        rot = self.base.rotulo(res.meta)
        self._dizer("")
        if res.estabelecida:
            self._dizer(f"✔ Conclusão: {rot} = {', '.join(fmt_valor(v) for v in res.valores)}")
            regras = ", ".join(res.regras_disparadas) or "nenhuma regra nova"
            self._dizer(f"   (modo {res.modo} · {res.perguntas} pergunta(s) · regras disparadas: {regras})")
            self._dizer("   Digite «como?» para ver como cheguei a isso.")
        else:
            self._dizer(f"✘ Não consegui estabelecer «{rot}» com as informações disponíveis.")
            self._dizer("   Digite «por que não {0} = <valor>?» para saber o motivo, ou «o que você sabe?».".format(
                norm(rot)))

    def _cmd_modo(self, a):
        self.modo = a["modo"]
        self._dizer(f"Encadeamento {MODOS[self.modo]} selecionado.")

    def _cmd_informar(self, a):
        for atr, val in a["fatos"]:
            r = self.motor.informar(atr, val)
            rot = self.base.rotulo(atr)
            if r == "conflito":
                self._dizer(f"Já tenho «{rot}» = {fmt_valor(self.motor.valores(atr)[0])}; "
                            f"use «limpar» para recomeçar com outros dados.")
            else:
                self._dizer(f"Anotado: {rot} = {fmt_valor(val)}.")
        if self.modo != "tras":
            novas = self.motor.encadear_para_frente()
            if novas:
                self._dizer("Com isso concluí: " + "; ".join(
                    f"{self.base.rotulo(f.atributo)} = {fmt_valor(f.valor)}" for fs in self.motor.fatos.values()
                    for f in fs if f.origem == "regra" and f.regra_id in novas))

    def _cmd_fatos(self, a):
        self._dizer("Fatos na memória de trabalho:\n" + X.resumo_fatos(self.motor))

    def _cmd_limpar(self, a):
        self.motor.reiniciar()
        self.ultima_meta = None
        self._dizer("Memória limpa. Podemos começar uma nova consulta.")

    # ------------------------------------------------------------------ explicações
    def _cmd_por_que(self, a):
        if self._pergunta_atual is None:
            self._dizer("«Por quê?» explica uma pergunta minha — responda-o quando eu estiver perguntando. "
                        "Para saber como cheguei a uma conclusão, use «como?»; para saber por que algo não foi "
                        "concluído, «por que não <variável> = <valor>?».")
            return
        self._nivel_por_que += 1
        self._dizer(X.por_que(self.motor, self._pergunta_atual, self._nivel_por_que))

    def _alvo(self, texto):
        v = nl.escolher_variavel(texto, self.base)
        if v is None:
            return None, None
        val = None
        for atr, x in nl.extrair_fatos(texto, self.base):
            if atr == v.nome:
                val = x
        if val is None:
            m = re.search(r"=\s*(.+)$", texto)
            if m:
                val = m.group(1).strip()
        return v.nome, val

    def _cmd_como(self, a):
        texto = a.get("texto", "")
        if texto:
            atr, val = self._alvo(texto)
            if atr is None:
                self._dizer("Não identifiquei de qual variável você fala. Variáveis: " +
                            ", ".join(v.rotulo for v in self.base.variaveis.values()))
                return
            self._dizer(X.como(self.motor, atr, val))
            return
        alvos = [self.ultima_meta] if self.ultima_meta else [
            n for n, fs in self.motor.fatos.items() if any(f.origem == "regra" for f in fs)]
        if not alvos:
            self._dizer("Ainda não concluí nada. Faça uma consulta primeiro («consultar»).")
            return
        for atr in alvos:
            self._dizer(X.como(self.motor, atr))

    def _cmd_por_que_nao(self, a):
        atr, val = self._alvo(a["texto"])
        if atr is None or val is None:
            self._dizer("Diga qual variável e valor, por exemplo: «por que não risco = Baixo?».")
            return
        self._dizer(X.por_que_nao(self.motor, atr, val))

    def _cmd_trilha(self, a):
        self._dizer("Trilha de inferência:\n" + X.trilha(self.motor))

    # ------------------------------------------------------------------ consulta à base
    def _texto_regras(self):
        if not self.base.regras:
            return "(a base não tem regras)"
        return "\n".join(f"{r.id}: {r.texto(self.base.rotulo)}" for r in self.base.regras)

    def _cmd_regras(self, a):
        self._dizer(f"Regras de «{self.base.nome}» ({len(self.base.regras)}):\n" + self._texto_regras())

    def _cmd_regra(self, a):
        r = self.base.regra(a["id"])
        if r is None:
            self._dizer(f"Não existe a regra {a['id']}.")
            return
        self._dizer(f"{r.id}: {r.texto(self.base.rotulo)}")
        if r.explicacao:
            self._dizer(f"   justificativa: {r.explicacao}")

    def _cmd_variaveis(self, a):
        for v in self.base.variaveis.values():
            vals = f"  valores: {', '.join(fmt_valor(x) for x in v.valores)}" if v.valores else ""
            perg = "pergunto ao usuário" if self.base.perguntavel(v.nome) else "calculada por regras"
            nome = v.rotulo if v.rotulo == v.nome else f"{v.rotulo} [{v.nome}]"
            self._dizer(f"  • {nome} — {perg}.{vals}")
        if self.base.metas:
            self._dizer("Metas: " + ", ".join(self.base.rotulo(m) for m in self.base.metas))

    def _cmd_sobre(self, a):
        self._dizer(f"Base: {self.base.nome}\n{self.base.descricao}\n"
                    f"{len(self.base.regras)} regras, {len(self.base.variaveis)} variáveis, "
                    f"{len(self.base.fatos)} fato(s) inicial(is). Encadeamento atual: {MODOS[self.modo]}.")

    def _cmd_desconhecido(self, a):
        self._dizer("Não entendi. Digite «ajuda» para ver o que posso fazer.")

    # ------------------------------------------------------------------ bases
    def _cmd_bases(self, a):
        if "nome" in a:
            return self._carregar_por_nome(a["nome"])
        bases = listar_bases(self.pasta_bases)
        if not bases:
            self._dizer("Nenhuma base de exemplo encontrada.")
        for nome, _, titulo, desc in bases:
            self._dizer(f"  • {nome:<12} — {titulo}")
        self._dizer("Use «carregar <nome>».")
        return True

    def _carregar_por_nome(self, nome):
        cand = Path(nome)
        achado = None
        if cand.exists():
            achado = cand
        else:
            for stem, caminho, titulo, _ in listar_bases(self.pasta_bases):
                if norm(nome) in (norm(stem), norm(titulo)) or norm(nome) in norm(titulo) or norm(nome) in norm(stem):
                    achado = caminho
                    break
        if achado is None:
            self._dizer(f"Não encontrei a base «{nome}». Digite «bases» para ver as disponíveis.")
            return True
        try:
            b = carregar(achado)
        except Exception as e:
            self._dizer(f"Erro ao ler «{achado}»: {e}")
            return True
        self.carregar_base(b, str(achado))
        self._dizer(f"Base «{b.nome}» carregada: {len(b.regras)} regras, {len(b.variaveis)} variáveis.")
        if b.descricao:
            self._dizer(b.descricao)
        return True

    def _cmd_salvar(self, a):
        destino = a.get("arquivo") or self.caminho or (re.sub(r"\W+", "_", norm(self.base.nome)) + ".kb")
        try:
            salvar(self.base, destino)
        except OSError as e:
            self._dizer(f"Não consegui salvar: {e}")
            return
        self.caminho = str(destino)
        self._dizer(f"Base salva em {destino}.")

    # ------------------------------------------------------------------ edição por comandos
    def _cmd_add_regra(self, a):
        try:
            novas = self.editor.adicionar_regra(a["texto"], a.get("id"))
        except (ErroSintaxe, ValueError) as e:
            self._dizer(f"Regra inválida: {e}")
            return
        for r in novas:
            self._dizer(f"Regra {r.id} adicionada: {r.texto(self.base.rotulo)}")
        self._refazer_motor()
        self._avisos()

    def _cmd_rem_regra(self, a):
        try:
            r = self.editor.remover_regra(a["id"])
        except KeyError as e:
            self._dizer(str(e.args[0]))
            return
        self._dizer(f"Regra {r.id} removida.")
        self._refazer_motor()

    def _cmd_edit_regra(self, a):
        try:
            novas = self.editor.substituir_regra(a["id"], a["texto"])
        except (ErroSintaxe, ValueError, KeyError) as e:
            self._dizer(f"Não foi possível editar: {e.args[0] if isinstance(e, KeyError) else e}")
            return
        self._dizer(f"Regra {novas[0].id} atualizada: {novas[0].texto(self.base.rotulo)}")
        self._refazer_motor()

    def _cmd_add_fato(self, a):
        try:
            atr, val = self.editor.adicionar_fato(a["texto"])
        except ErroSintaxe as e:
            self._dizer(f"Fato inválido: {e}")
            return
        self._dizer(f"Fato inicial adicionado: {self.base.rotulo(atr)} = {fmt_valor(val)}.")
        self.motor.informar(atr, val)

    def _cmd_rem_fato(self, a):
        try:
            self.editor.remover_fato(a["nome"])
        except KeyError as e:
            self._dizer(str(e.args[0]))
            return
        self._dizer("Fato inicial removido.")
        self._refazer_motor()

    def _cmd_validar(self, a):
        probs = self.editor.validar()
        if not probs:
            self._dizer("Base consistente: nenhum problema encontrado.")
        for p in probs:
            self._dizer(str(p))

    def _avisos(self):
        for p in self.editor.validar():
            if p.nivel == "erro":
                self._dizer(str(p))

    # ------------------------------------------------------------------ editor guiado
    def _cmd_editor(self, a):
        self._dizer(f"=== Editor da base «{self.base.nome}» ===")
        while True:
            self._dizer("  1) listar regras   2) nova regra   3) editar regra   4) excluir regra\n"
                        "  5) fatos iniciais  6) variáveis    7) metas          8) validar\n"
                        "  9) salvar          0) voltar")
            op = norm(self._ler("editor> "))
            if op in ("0", "voltar", "sair", ""):
                self._dizer("Saindo do editor.")
                return
            try:
                {"1": self._ed_listar, "2": self._ed_nova, "3": self._ed_editar, "4": self._ed_excluir,
                 "5": self._ed_fatos, "6": self._ed_variaveis, "7": self._ed_metas,
                 "8": lambda: self._cmd_validar({}), "9": lambda: self._cmd_salvar({})}.get(
                    op, lambda: self._dizer("Opção inválida."))()
            except (ErroSintaxe, ValueError, KeyError) as e:
                self._dizer(f"Erro: {e.args[0] if isinstance(e, KeyError) else e}")

    def _ed_listar(self):
        self._dizer(self._texto_regras())

    def _ed_nova(self):
        txt = self._ler("  regra em uma linha (SE ... ENTÃO ...) ou ENTER para montar passo a passo> ").strip()
        if not txt:
            conds = []
            while True:
                c = self._ler(f"  condição {len(conds) + 1} (ex.: renda = Alta; ENTER termina)> ").strip()
                if not c:
                    break
                conds.append(c)
            concl = []
            while True:
                c = self._ler(f"  conclusão {len(concl) + 1} (ex.: risco = Alto; ENTER termina)> ").strip()
                if not c:
                    break
                concl.append(c)
            if not concl:
                self._dizer("A regra precisa de pelo menos uma conclusão.")
                return
            txt = "SE " + (" E ".join(conds) if conds else "VERDADEIRO") + " ENTÃO " + " E ".join(concl)
        expl = self._ler("  justificativa (opcional)> ").strip()
        novas = self.editor.adicionar_regra(txt, None, 0, expl)
        for r in novas:
            self._dizer(f"  Regra {r.id} criada: {r.texto(self.base.rotulo)}")
        self._refazer_motor()
        self._avisos()

    def _ed_editar(self):
        rid = self._ler("  identificador da regra> ").strip()
        r = self.base.regra(rid)
        if r is None:
            self._dizer("  Regra inexistente.")
            return
        self._dizer(f"  atual: {r.texto(self.base.rotulo)}")
        txt = self._ler("  nova regra (SE ... ENTÃO ...; ENTER mantém)> ").strip()
        if txt:
            self.editor.substituir_regra(rid, txt)
            self._dizer("  Regra atualizada.")
            self._refazer_motor()

    def _ed_excluir(self):
        rid = self._ler("  identificador da regra> ").strip()
        r = self.editor.remover_regra(rid)
        self._dizer(f"  Regra {r.id} excluída.")
        self._refazer_motor()

    def _ed_fatos(self):
        for a, v in self.base.fatos:
            self._dizer(f"  {self.base.rotulo(a)} = {fmt_valor(v)}")
        txt = self._ler("  novo fato (variável = valor), «remover <variável>» ou ENTER> ").strip()
        if not txt:
            return
        if norm(txt).startswith("remover"):
            self.editor.remover_fato(txt.split(None, 1)[1])
            self._dizer("  Fato removido.")
        else:
            a, v = self.editor.adicionar_fato(txt)
            self._dizer(f"  Fato adicionado: {self.base.rotulo(a)} = {fmt_valor(v)}")
        self._refazer_motor()

    def _ed_variaveis(self):
        self._cmd_variaveis({})
        nome = self._ler("  variável a criar/editar (ENTER volta)> ").strip()
        if not nome:
            return
        v = self.base.variavel(nome)
        campos = {}
        r = self._ler(f"  rótulo [{v.rotulo if v else nome}]> ").strip()
        if r:
            campos["rotulo"] = r
        p = self._ler("  pergunta ao usuário [mantém]> ").strip()
        if p:
            campos["pergunta"] = p
        vals = self._ler("  valores possíveis, separados por vírgula [mantém]> ").strip()
        if vals:
            campos["valores"] = [x.strip() for x in vals.split(",") if x.strip()]
        t = self._ler("  tipo (texto/numero/booleano) [mantém]> ").strip()
        if t:
            campos["tipo"] = norm(t)
        pg = self._ler("  perguntável? (sim/não/auto) [mantém]> ").strip()
        if pg:
            campos["perguntavel"] = None if norm(pg) == "auto" else norm(pg) in ("sim", "s")
        self.editor.definir_variavel(nome, **campos)
        self._dizer("  Variável atualizada.")

    def _ed_metas(self):
        self._dizer("  metas atuais: " + (", ".join(self.base.rotulo(m) for m in self.base.metas) or "(nenhuma)"))
        txt = self._ler("  novas metas, separadas por vírgula (ENTER mantém)> ").strip()
        if txt:
            self.editor.definir_metas([x.strip() for x in txt.split(",") if x.strip()])
            self._dizer("  Metas atualizadas.")
