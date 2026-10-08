"""Modelo de dados do shell de sistemas baseados em conhecimento (SBC).

A ferramenta NÃO conhece nenhum domínio: tudo o que é específico (variáveis, regras, fatos, perguntas)
vive em uma ``BaseConhecimento`` carregada de um arquivo ``.kb`` (ou JSON) ou criada pelo editor.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ====================================================================== utilidades de texto/valores
_NUM = re.compile(r"^[+-]?\d+([.,]\d+)?$")


def norm(s) -> str:
    """Minúsculas, sem acentos e sem espaços repetidos (comparação tolerante de textos)."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def como_numero(x):
    """Converte para número se possível (aceita vírgula decimal); senão devolve None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if _NUM.match(s):
        return float(s.replace(",", "."))
    return None


def valores_iguais(a, b) -> bool:
    na, nb = como_numero(a), como_numero(b)
    if na is not None and nb is not None:
        return na == nb
    return norm(a) == norm(b)


def fmt_valor(v) -> str:
    """Texto de um valor para exibição (inteiros sem '.0')."""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


OPERADORES = ("=", "!=", "<", "<=", ">", ">=", "em")
SIMBOLO = {"=": "=", "!=": "≠", "<": "<", "<=": "≤", ">": ">", ">=": "≥", "em": "∈"}


# ====================================================================== condições e regras
@dataclass(frozen=True)
class Condicao:
    atributo: str
    operador: str
    valor: object              # escalar, ou tupla de escalares quando operador == "em"
    negada: bool = False

    def avaliar(self, conhecidos):
        """True/False; None quando o atributo ainda não tem valor ("desconhecido")."""
        if not conhecidos:
            return None
        op, v = self.operador, self.valor
        if op == "=":
            r = any(valores_iguais(x, v) for x in conhecidos)
        elif op == "!=":
            r = not any(valores_iguais(x, v) for x in conhecidos)
        elif op == "em":
            r = any(valores_iguais(x, w) for x in conhecidos for w in v)
        else:
            nv = como_numero(v)
            nums = [como_numero(x) for x in conhecidos]
            nums = [n for n in nums if n is not None]
            if nv is None or not nums:
                r = False
            elif op == "<":
                r = any(n < nv for n in nums)
            elif op == "<=":
                r = any(n <= nv for n in nums)
            elif op == ">":
                r = any(n > nv for n in nums)
            else:
                r = any(n >= nv for n in nums)
        return (not r) if self.negada else r

    def texto(self, rotulo=lambda a: a):
        v = self.valor
        val = "{" + ", ".join(fmt_valor(x) for x in v) + "}" if self.operador == "em" else fmt_valor(v)
        t = f"{rotulo(self.atributo)} {SIMBOLO[self.operador]} {val}"
        return f"NÃO ({t})" if self.negada else t


@dataclass(frozen=True)
class Conclusao:
    atributo: str
    valor: object

    def texto(self, rotulo=lambda a: a):
        return f"{rotulo(self.atributo)} = {fmt_valor(self.valor)}"


@dataclass
class Regra:
    id: str
    condicoes: list
    conclusoes: list
    prioridade: int = 0
    explicacao: str = ""

    @property
    def especificidade(self):
        return len(self.condicoes)

    def concluidos(self):
        return {c.atributo for c in self.conclusoes}

    def texto(self, rotulo=lambda a: a):
        se = " E ".join(c.texto(rotulo) for c in self.condicoes) or "VERDADEIRO"
        entao = " E ".join(c.texto(rotulo) for c in self.conclusoes)
        return f"SE {se} ENTÃO {entao}"


# ====================================================================== variáveis e base
@dataclass
class Variavel:
    nome: str
    rotulo: str = ""
    valores: list = field(default_factory=list)
    pergunta: str = ""
    tipo: str = "texto"                # texto | numero | booleano
    perguntavel: object = None         # None = automático (perguntável se nenhuma regra a conclui)
    multivalorada: bool = False
    descricao: str = ""
    automatica: bool = False           # declarada implicitamente (ao ser usada numa regra); o domínio cresce sozinho

    def __post_init__(self):
        if not self.rotulo:
            self.rotulo = self.nome


@dataclass
class BaseConhecimento:
    nome: str = "Base sem nome"
    descricao: str = ""
    variaveis: dict = field(default_factory=dict)      # nome -> Variavel
    regras: list = field(default_factory=list)
    fatos: list = field(default_factory=list)          # [(atributo, valor)] conhecidos desde o início
    metas: list = field(default_factory=list)          # variáveis-objetivo sugeridas
    estrategia: str = "ordem"                          # ordem | especificidade | prioridade

    # -------------------------------------------------------------- consulta
    def variavel(self, nome):
        """Busca por nome ou rótulo (sem distinguir acentos/maiúsculas)."""
        if nome in self.variaveis:
            return self.variaveis[nome]
        n = norm(nome)
        for v in self.variaveis.values():
            if norm(v.nome) == n or norm(v.rotulo) == n:
                return v
        return None

    def rotulo(self, atributo):
        v = self.variaveis.get(atributo)
        return v.rotulo if v else atributo

    def regra(self, rid):
        for r in self.regras:
            if norm(r.id) == norm(rid):
                return r
        return None

    def regras_que_concluem(self, atributo):
        return [r for r in self.regras if atributo in r.concluidos()]

    def e_conclusao(self, atributo):
        return bool(self.regras_que_concluem(atributo))

    def perguntavel(self, atributo):
        v = self.variaveis.get(atributo)
        if v is None:
            return True
        if v.perguntavel is not None:
            return bool(v.perguntavel)
        return not self.e_conclusao(atributo)

    def proximo_id_regra(self, prefixo="R"):
        usados = {norm(r.id) for r in self.regras}
        i = len(self.regras) + 1
        while norm(f"{prefixo}{i}") in usados:
            i += 1
        return f"{prefixo}{i}"

    def garantir_variavel(self, atributo, valor=None):
        """Declara automaticamente uma variável usada numa regra/fato e acrescenta o valor ao domínio."""
        v = self.variaveis.get(atributo)
        if v is None:
            v = self.variaveis[atributo] = Variavel(atributo, automatica=True)
        if not v.automatica:                  # variável declarada: o domínio é o declarado (validar() avisa sobre o resto)
            return v
        vals = valor if isinstance(valor, tuple) else ((valor,) if valor is not None else ())
        for x in vals:
            if como_numero(x) is not None and isinstance(x, (int, float)):
                v.tipo = "numero"
            elif not any(valores_iguais(x, y) for y in v.valores) and v.tipo != "numero":
                v.valores.append(x)
        return v
