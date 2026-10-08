"""Engenho de inferência: encadeamento para frente, para trás e misto.

* Memória de trabalho: fatos (atributo = valor) com a justificativa de cada um (usuário, base ou regra),
  que alimenta o módulo de explicação (Como?).
* Lógica de três valores nas condições: verdadeira / falsa / desconhecida. Uma regra só dispara se TODAS
  as condições forem verdadeiras; no encadeamento para trás, uma condição desconhecida leva a derivar o
  atributo por outras regras ou a perguntar ao usuário (se a variável for "perguntável").
* Para trás: busca dirigida por meta, com detecção de ciclos, memória de regras já tentadas e pilha de
  objetivos (usada pelo Por quê?).
* Misto: faz primeiro o encadeamento para frente com o que já se sabe e, para o que faltar, o encadeamento
  para trás; a cada resposta do usuário volta a propagar para frente, o que costuma reduzir as perguntas.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .modelo import BaseConhecimento, Condicao, Regra, fmt_valor, norm, valores_iguais


class _Desconhecido:
    def __repr__(self):
        return "DESCONHECIDO"


DESCONHECIDO = _Desconhecido()      # resposta "não sei" do usuário


class ConsultaCancelada(Exception):
    """O usuário desistiu da consulta durante uma pergunta."""


@dataclass
class Fato:
    atributo: str
    valor: object
    origem: str                       # 'inicial' | 'usuario' | 'regra'
    regra_id: str | None = None
    premissas: list = field(default_factory=list)   # [(atributo, valor)] usadas para concluir
    passo: int = 0


@dataclass
class Evento:
    passo: int
    tipo: str      # fato_inicial | pergunta | resposta | regra_disparada | regra_falhou | conflito | meta | propagacao
    texto: str
    dados: dict = field(default_factory=dict)


@dataclass
class Frame:
    """Um objetivo em andamento: tentando estabelecer `atributo` pela regra `regra` (condição nº `indice`)."""
    atributo: str
    desejado: object
    regra: Regra | None
    indice: int


@dataclass
class Pergunta:
    atributo: str
    texto: str
    opcoes: list | None
    tipo: str
    contexto: list                    # pilha de Frames (do objetivo mais externo ao mais interno)


@dataclass
class Resultado:
    meta: str
    desejado: object
    estabelecida: bool
    valores: list
    modo: str
    perguntas: int = 0
    regras_disparadas: list = field(default_factory=list)


class Motor:
    def __init__(self, base: BaseConhecimento, perguntar=None, estrategia=None):
        self.base = base
        self.perguntar = perguntar           # callback(Pergunta) -> valor | lista de valores | DESCONHECIDO
        self.estrategia = estrategia or base.estrategia or "ordem"
        self.reiniciar()

    # ================================================================== memória de trabalho
    def reiniciar(self, com_fatos_iniciais=True):
        self.fatos = {}
        self.desconhecidos = set()
        self.eventos = []
        self.passo = 0
        self.n_perguntas = 0
        self.disparadas = []                 # ids na ordem de disparo
        self._ja_disparou = set()
        self._falhas = set()
        self._perguntadas = set()
        self._pilha = []
        self._em_progresso = set()
        self._cortes = 0
        if com_fatos_iniciais:
            for a, v in self.base.fatos:
                self._adicionar(a, v, "inicial")

    def _registrar(self, tipo, texto, **dados):
        self.passo += 1
        self.eventos.append(Evento(self.passo, tipo, texto, dados))

    def valores(self, atributo):
        return [f.valor for f in self.fatos.get(atributo, [])]

    def conhece(self, atributo):
        return bool(self.fatos.get(atributo))

    def fato(self, atributo, valor=None):
        for f in self.fatos.get(atributo, []):
            if valor is None or valores_iguais(f.valor, valor):
                return f
        return None

    def _multi(self, atributo):
        v = self.base.variaveis.get(atributo)
        return bool(v and v.multivalorada)

    def _adicionar(self, atributo, valor, origem, regra=None, premissas=None):
        """Insere um fato. Retorna 'novo', 'repetido' ou 'conflito' (valor diferente em var. de valor único)."""
        existentes = self.fatos.get(atributo, [])
        if any(valores_iguais(f.valor, valor) for f in existentes):
            return "repetido"
        rot = self.base.rotulo(atributo)
        if existentes and not self._multi(atributo):
            self._registrar("conflito", f"conflito: {rot} já é {fmt_valor(existentes[0].valor)}; "
                                        f"ignorado o novo valor {fmt_valor(valor)}"
                                        + (f" (regra {regra.id})" if regra else ""),
                            atributo=atributo, valor=valor, regra=regra.id if regra else None)
            return "conflito"
        self.passo += 1
        f = Fato(atributo, valor, origem, regra.id if regra else None, list(premissas or []), self.passo)
        self.fatos.setdefault(atributo, []).append(f)
        self.desconhecidos.discard(atributo)
        txt = {"inicial": f"fato inicial: {rot} = {fmt_valor(valor)}",
               "usuario": f"informado: {rot} = {fmt_valor(valor)}",
               "regra": f"concluído: {rot} = {fmt_valor(valor)} (regra {regra.id if regra else '?'})"}[origem]
        self.eventos.append(Evento(self.passo, "fato_" + origem, txt, {"atributo": atributo, "valor": valor,
                                                                      "regra": regra.id if regra else None}))
        return "novo"

    def informar(self, atributo, valor):
        """Fato fornecido pelo usuário (fora de uma pergunta)."""
        self.base.garantir_variavel(atributo, valor) if atributo not in self.base.variaveis else None
        return self._adicionar(atributo, valor, "usuario")

    def esquecer(self, atributo=None):
        """Remove um fato informado e tudo o que foi derivado (reinicia a derivação mantendo os dados do usuário)."""
        dados = [(f.atributo, f.valor) for fs in self.fatos.values() for f in fs if f.origem in ("usuario",)
                 and (atributo is None or f.atributo != atributo)]
        self.reiniciar()
        for a, v in dados:
            self._adicionar(a, v, "usuario")

    # ================================================================== avaliação de regras
    def _aplicavel(self, r):
        return all(c.avaliar(self.valores(c.atributo)) is True for c in r.condicoes)

    def _premissas(self, r):
        prem = []
        for c in r.condicoes:
            vals = self.valores(c.atributo)
            escolhido = vals[0] if vals else None
            for v in vals:
                if Condicao(c.atributo, c.operador, c.valor, c.negada).avaliar([v]) is True:
                    escolhido = v
                    break
            if (c.atributo, escolhido) not in prem:
                prem.append((c.atributo, escolhido))
        return prem

    def _disparar(self, r):
        self._ja_disparou.add(r.id)
        prem = self._premissas(r)
        novos = []
        for c in r.conclusoes:
            if self._adicionar(c.atributo, c.valor, "regra", r, prem) == "novo":
                novos.append(c)
        self.disparadas.append(r.id)
        self._registrar("regra_disparada", f"regra {r.id} disparada: {r.texto(self.base.rotulo)}",
                        regra=r.id, novos=[(c.atributo, c.valor) for c in novos])
        return novos

    def _ordenar(self, regras):
        e = norm(self.estrategia)
        if e.startswith("especific"):
            return sorted(regras, key=lambda r: -r.especificidade)
        if e.startswith("priorid"):
            return sorted(regras, key=lambda r: -r.prioridade)
        return list(regras)

    # ================================================================== encadeamento para frente
    def encadear_para_frente(self):
        """Dispara regras aplicáveis até o ponto fixo. Retorna os ids disparados nesta chamada."""
        agora = []
        while True:
            candidatas = [r for r in self.base.regras if r.id not in self._ja_disparou and self._aplicavel(r)]
            if not candidatas:
                break
            r = self._ordenar(candidatas)[0]
            self._disparar(r)
            agora.append(r.id)
        return agora

    def coletar_todos(self):
        """Pergunta ao usuário todas as variáveis perguntáveis ainda desconhecidas (usado no modo 'frente')."""
        for nome in list(self.base.variaveis):
            if self.base.perguntavel(nome) and not self.conhece(nome) and nome not in self._perguntadas:
                self._perguntar(nome)

    # ================================================================== encadeamento para trás
    def _satisfeito(self, atributo, desejado):
        vals = self.valores(atributo)
        if not vals:
            return False
        return True if desejado is None else any(valores_iguais(v, desejado) for v in vals)

    def _candidatas(self, atributo, desejado):
        out = []
        for r in self.base.regras:
            for c in r.conclusoes:
                if c.atributo == atributo and (desejado is None or valores_iguais(c.valor, desejado)):
                    out.append(r)
                    break
        return self._ordenar(out)

    def _decidir(self, c, propagar):
        desej = c.valor if (c.operador == "=" and not c.negada) else None
        self._obter(c.atributo, desej, propagar)
        return c.avaliar(self.valores(c.atributo)) is True

    def _testar(self, r, atributo, desejado, propagar):
        """True se todas as condições se confirmam; False se alguma falha; None se a meta já foi estabelecida
        por outro caminho (só no modo misto, com propagação)."""
        for i, c in enumerate(r.condicoes):
            if propagar and self._satisfeito(atributo, desejado) and not (desejado is None and self._multi(atributo)):
                return None
            self._pilha.append(Frame(atributo, desejado, r, i))
            try:
                ok = self._decidir(c, propagar)
            finally:
                self._pilha.pop()
            if not ok:
                self._registrar("regra_falhou", f"regra {r.id} descartada: condição «{c.texto(self.base.rotulo)}» "
                                                f"não se confirmou", regra=r.id)
                return False
        return True

    def _obter(self, atributo, desejado=None, propagar=False):
        """Tenta estabelecer `atributo` (= `desejado`). Retorna True se, ao final, a meta vale."""
        todos = desejado is None and self._multi(atributo)      # meta multivalorada: procurar todos os valores
        if self._satisfeito(atributo, desejado) and not todos:
            return True
        if self.conhece(atributo) and not self._multi(atributo):
            return False                      # variável de valor único já tem outro valor
        chave = (atributo, None if desejado is None else norm(desejado))
        if chave in self._em_progresso:
            self._cortes += 1                 # ciclo: não insistir
            return False
        self._em_progresso.add(chave)
        try:
            for r in self._candidatas(atributo, desejado):
                if r.id in self._ja_disparou or r.id in self._falhas:
                    continue
                cortes_antes = self._cortes
                res = self._testar(r, atributo, desejado, propagar)
                if res is None:
                    return True
                if res:
                    if r.id not in self._ja_disparou:     # a propagação pode já tê-la disparado
                        self._disparar(r)
                    if propagar:
                        self.encadear_para_frente()
                    if self._satisfeito(atributo, desejado) and not (desejado is None and self._multi(atributo)):
                        return True
                elif self._cortes == cortes_antes:
                    self._falhas.add(r.id)    # falha definitiva (não causada por ciclo)
            if self._satisfeito(atributo, desejado):
                return True
            if (self.base.perguntavel(atributo) and atributo not in self._perguntadas
                    and atributo not in self.desconhecidos):
                self._perguntar(atributo)
                if propagar:
                    self.encadear_para_frente()
                return self._satisfeito(atributo, desejado)
            return False
        finally:
            self._em_progresso.discard(chave)

    def _perguntar(self, atributo):
        self._perguntadas.add(atributo)
        if self.perguntar is None:
            return
        var = self.base.variaveis.get(atributo)
        rot = self.base.rotulo(atributo)
        texto = (var.pergunta if var and var.pergunta else f"Qual é o valor de «{rot}»?")
        tipo = var.tipo if var else "texto"
        opcoes = list(var.valores) if var and var.valores else None
        if tipo == "booleano" and not opcoes:
            opcoes = ["sim", "não"]
        p = Pergunta(atributo, texto, opcoes, tipo, list(self._pilha))
        self.n_perguntas += 1
        self._registrar("pergunta", f"pergunta ao usuário: {texto}", atributo=atributo)
        resp = self.perguntar(p)
        if resp is DESCONHECIDO or resp is None:
            self.desconhecidos.add(atributo)
            self._registrar("resposta", f"resposta: não sei ({rot})", atributo=atributo)
            return
        for v in (resp if isinstance(resp, (list, tuple)) else [resp]):
            self._adicionar(atributo, v, "usuario")

    # ================================================================== consulta
    def consultar(self, meta, modo="misto", desejado=None):
        """Executa uma consulta pelo modo escolhido ('frente', 'tras' ou 'misto')."""
        if meta not in self.base.variaveis:
            v = self.base.variavel(meta)
            if v is None:
                raise KeyError(f"variável desconhecida: {meta}")
            meta = v.nome
        modo = {"para frente": "frente", "forward": "frente", "para tras": "tras", "para trás": "tras",
                "backward": "tras", "mixed": "misto", "hibrido": "misto", "híbrido": "misto"}.get(norm(modo), norm(modo))
        perg0, disp0 = self.n_perguntas, len(self.disparadas)
        self._registrar("meta", f"consulta: meta «{self.base.rotulo(meta)}»"
                                + (f" = {fmt_valor(desejado)}" if desejado is not None else "") + f" — modo {modo}")
        if modo == "frente":
            self.coletar_todos()
            self.encadear_para_frente()
        elif modo == "tras":
            self._obter(meta, desejado, propagar=False)
        elif modo == "misto":
            self.encadear_para_frente()
            if not self._satisfeito(meta, desejado) or (desejado is None and self._multi(meta)):
                self._obter(meta, desejado, propagar=True)
        else:
            raise ValueError("modo deve ser 'frente', 'tras' ou 'misto'")
        ok = self._satisfeito(meta, desejado)
        self._registrar("meta", f"meta «{self.base.rotulo(meta)}» "
                                + ("estabelecida: " + ", ".join(fmt_valor(v) for v in self.valores(meta)) if ok
                                   else "NÃO pôde ser estabelecida"))
        return Resultado(meta, desejado, ok, self.valores(meta), modo, self.n_perguntas - perg0,
                         self.disparadas[disp0:])
