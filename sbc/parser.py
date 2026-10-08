"""Leitura/escrita de bases de conhecimento (.kb texto e JSON) e do texto de regras SE ... ENTÃO ...

Sintaxe resumida (veja sbc/README.md):

    BASE: Nome
    DESCRIÇÃO: texto
    META: variavel1, variavel2
    ESTRATÉGIA: ordem | especificidade | prioridade

    VARIÁVEL renda
        RÓTULO: Renda do cliente
        PERGUNTA: Qual é a faixa de renda?
        VALORES: "$0 a $15k", "$15 a $35k", "Acima de $35k"
        TIPO: texto | numero | booleano
        PERGUNTÁVEL: sim | não          (padrão: sim se nenhuma regra conclui a variável)
        MULTIVALORADA: sim | não

    FATO: variavel = valor
    REGRA R1 [prioridade 2]: SE a = x E b > 3 OU NÃO c EM [p, q] ENTÃO d = y E e = z
        EXPLICAÇÃO: texto livre
"""
from __future__ import annotations

import json
import re

from .modelo import (BaseConhecimento, Condicao, Conclusao, Regra, Variavel, como_numero, fmt_valor, norm)


class ErroSintaxe(ValueError):
    def __init__(self, mensagem, linha=None):
        self.linha = linha
        super().__init__(f"linha {linha}: {mensagem}" if linha else mensagem)


# ====================================================================== tokenização
_TOKEN = re.compile(r'''\s*(?:
    (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<op><=|>=|!=|≠|≤|≥|∈|=|<|>)
  | (?P<punct>[\[\](){},])
  | (?P<word>[^\s=<>!,\[\](){}"≠≤≥∈]+)
)''', re.X)
_PALAVRAS = {"se": "SE", "entao": "ENTAO", "e": "E", "ou": "OU", "nao": "NAO", "em": "EM"}
_OPS = {"≠": "!=", "≤": "<=", "≥": ">=", "∈": "em"}


class Kw(str):
    """Palavra-chave (SE, E, OU...) que lembra como foi escrita, para poder voltar a ser texto de um valor."""
    orig = ""


def _tokens(texto):
    pos, out = 0, []
    texto = texto.strip()
    while pos < len(texto):
        m = _TOKEN.match(texto, pos)
        if not m or m.end() == pos:
            raise ErroSintaxe(f"caractere inesperado em «{texto[pos:pos + 12]}»")
        pos = m.end()
        if m.group("str") is not None:
            out.append(("str", m.group("str")[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        elif m.group("op") is not None:
            out.append(("op", _OPS.get(m.group("op"), m.group("op"))))
        elif m.group("punct") is not None:
            out.append(("punct", m.group("punct")))
        else:
            w = m.group("word")
            kw = _PALAVRAS.get(norm(w))
            if kw:
                k = Kw(kw)
                k.orig = w
                out.append(("kw", k))
            else:
                out.append(("word", w))
    return out


def _escalar(tipo, texto):
    if tipo == "str":
        return texto
    n = como_numero(texto)
    if n is not None:
        return int(n) if n == int(n) and "," not in texto and "." not in texto else n
    return texto


class _Leitor:
    def __init__(self, tokens):
        self.t, self.i = tokens, 0

    def ver(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else (None, None)

    def pegar(self):
        tok = self.ver()
        self.i += 1
        return tok

    def fim(self):
        return self.i >= len(self.t)

    def _comeca_condicao(self, j):
        """True se, a partir de t[j], há «palavras… operador» (ou EM): o início de uma nova condição."""
        t = self.t
        if j < len(t) and t[j] == ("kw", "NAO"):
            j += 1
        n = 0
        while j < len(t) and t[j][0] in ("word", "str"):
            n += 1
            j += 1
        if n == 0 or j >= len(t):
            return False
        if t[j][0] == "op":
            return True
        if t[j] == ("kw", "NAO"):
            j += 1
        return j + 1 < len(t) and t[j] == ("kw", "EM") and t[j + 1][0] == "punct" and t[j + 1][1] in "[{("

    # nomes e valores aceitam várias palavras seguidas ("Acima de $35k") quando sem aspas
    def texto_livre(self, valor=False):
        partes = []
        while not self.fim():
            tipo, tx = self.ver()
            if valor and not partes and (tipo, tx) == ("kw", "NAO"):
                partes.append("não")              # «não» como valor (ex.: tem_penas = não; acao = não insistir)
                self.pegar()
                continue
            if valor and partes and tipo == "kw" and (tx == "SE" or (tx in ("E", "OU", "EM")
                                                             and not self._comeca_condicao(self.i + 1)
                                                             and not (tx == "EM" and self.ver(1)[0] == "punct"))):
                partes.append(tx.orig or str(tx).lower())     # «e»/«ou» dentro de um valor ("cabo e fonte")
                self.pegar()
                continue
            if tipo == "str":
                if partes:
                    break
                self.pegar()
                return ("str", tx)
            if tipo == "word":
                partes.append(tx)
                self.pegar()
                continue
            break
        if not partes:
            raise ErroSintaxe("esperava um nome ou valor")
        return ("word", " ".join(partes))


def _lista(L):
    abre = L.pegar()
    if abre[0] != "punct" or abre[1] not in "[{(":
        raise ErroSintaxe("esperava '[' após EM")
    fecha = {"[": "]", "{": "}", "(": ")"}[abre[1]]
    itens = []
    while True:
        tipo, tx = L.ver()
        if tipo == "punct" and tx == fecha:
            L.pegar()
            break
        if tipo == "punct" and tx == ",":
            L.pegar()
            continue
        if L.fim():
            raise ErroSintaxe("lista sem fechamento")
        itens.append(_escalar(*L.texto_livre(valor=True)))
    if not itens:
        raise ErroSintaxe("lista vazia")
    return tuple(itens)


def _condicao(L):
    negada = False
    if L.ver() == ("kw", "NAO"):
        L.pegar()
        negada = True
    if L.ver() == ("punct", "("):          # NÃO (a = b)
        L.pegar()
        c = _condicao(L)
        if L.pegar() != ("punct", ")"):
            raise ErroSintaxe("faltou ')'")
        return Condicao(c.atributo, c.operador, c.valor, not c.negada if negada else c.negada)
    atributo = L.texto_livre()[1]
    tipo, tx = L.ver()
    if (tipo, tx) == ("kw", "NAO") and L.ver(1) == ("kw", "EM"):
        L.pegar()
        negada = not negada
        tipo, tx = L.ver()
    if (tipo, tx) == ("kw", "EM"):
        L.pegar()
        return Condicao(atributo, "em", _lista(L), negada)
    if tipo != "op":
        raise ErroSintaxe(f"esperava um operador depois de «{atributo}»")
    L.pegar()
    if tx == "em":
        return Condicao(atributo, "em", _lista(L), negada)
    valor = _escalar(*L.texto_livre(valor=True))
    return Condicao(atributo, tx, valor, negada)


def _parse_se_entao(texto):
    """Retorna (lista de conjunções, lista de conclusões). Cada conjunção é uma lista de Condicao."""
    toks = _tokens(texto)
    L = _Leitor(toks)
    if L.pegar() != ("kw", "SE"):
        raise ErroSintaxe("a regra deve começar com SE")
    conjs, atual = [], []
    while True:
        if L.ver() == ("word", "VERDADEIRO") or (L.ver()[0] == "word" and norm(L.ver()[1]) == "verdadeiro"):
            L.pegar()
        else:
            atual.append(_condicao(L))
        tipo, tx = L.ver()
        if (tipo, tx) == ("kw", "E"):
            L.pegar()
            continue
        if (tipo, tx) == ("kw", "OU"):
            L.pegar()
            conjs.append(atual)
            atual = []
            continue
        if (tipo, tx) == ("kw", "ENTAO"):
            L.pegar()
            conjs.append(atual)
            break
        raise ErroSintaxe("esperava E, OU ou ENTÃO")
    concl = []
    while True:
        c = _condicao(L)
        if c.operador != "=" or c.negada:
            raise ErroSintaxe("a conclusão deve ter a forma  variável = valor")
        concl.append(Conclusao(c.atributo, c.valor))
        if L.fim():
            break
        if L.pegar() != ("kw", "E"):
            raise ErroSintaxe("conclusões devem ser separadas por E")
    return conjs, concl


def parse_regra(texto, rid="R1", prioridade=0, explicacao=""):
    """Interpreta 'SE ... ENTÃO ...'. Com OU, expande em várias regras (R1, R1.2, R1.3...)."""
    conjs, concl = _parse_se_entao(texto)
    regras = []
    for k, conj in enumerate(conjs, 1):
        regras.append(Regra(rid if k == 1 else f"{rid}.{k}", conj, list(concl), prioridade, explicacao))
    return regras


def parse_condicao(texto):
    L = _Leitor(_tokens(texto))
    c = _condicao(L)
    if not L.fim():
        raise ErroSintaxe("texto sobrando depois da condição")
    return c


def parse_fato(texto):
    c = parse_condicao(texto)
    if c.operador != "=" or c.negada:
        raise ErroSintaxe("um fato tem a forma  variável = valor")
    return c.atributo, c.valor


# ====================================================================== leitura do .kb
_KW_TOPO = {"base", "descricao", "meta", "metas", "estrategia", "fato"}
_KW_VAR = {"rotulo", "pergunta", "valores", "tipo", "perguntavel", "multivalorada", "descricao"}


def _tira_comentario(linha):
    emq = False
    for i, ch in enumerate(linha):
        if ch == '"' and (i == 0 or linha[i - 1] != "\\"):
            emq = not emq
        elif ch == "#" and not emq:
            return linha[:i]
    return linha


def _itens(texto):
    itens = []
    for m in re.finditer(r'\s*(?:"((?:[^"\\]|\\.)*)"|([^,]+))', texto):
        if m.group(1) is not None:
            itens.append(m.group(1).replace('\\"', '"'))
        else:
            s = m.group(2).strip()
            if s:
                itens.append(_escalar("word", s))
    return itens


def _sim(txt):
    return norm(txt) in ("sim", "s", "true", "verdadeiro", "yes", "1")


def ler_kb(texto):
    base = BaseConhecimento()
    bloco = None            # ("var", Variavel) | ("regra", dict)
    regras_pendentes = []

    def fechar():
        nonlocal bloco
        if bloco and bloco[0] == "regra":
            d = bloco[1]
            try:
                base.regras.extend(parse_regra(d["texto"], d["id"], d["prioridade"], d["explicacao"].strip()))
            except ErroSintaxe as e:
                raise ErroSintaxe(f"regra {d['id']}: {e}", d["linha"]) from None
        bloco = None

    for n, bruta in enumerate(texto.splitlines(), 1):
        linha = _tira_comentario(bruta).rstrip()
        if not linha.strip():
            continue
        indentada = linha[0] in " \t"
        corpo = linha.strip()
        try:
            if not indentada:
                fechar()
                m = re.match(r"^REGRA\s+(\S+?)\s*(?:\[\s*prioridade\s+(-?\d+)\s*\])?\s*:\s*(.*)$", corpo, re.I)
                if m:
                    bloco = ("regra", {"id": m.group(1), "prioridade": int(m.group(2) or 0), "texto": m.group(3),
                                       "explicacao": "", "linha": n, "em_expl": False})
                    continue
                m = re.match(r"^VARI[ÁA]VEL\s+(.+)$", corpo, re.I)
                if m:
                    nome = _Leitor(_tokens(m.group(1))).texto_livre()[1]
                    v = base.variaveis.setdefault(nome, Variavel(nome))
                    bloco = ("var", v)
                    continue
                m = re.match(r"^([A-Za-zÀ-ÿ_]+)\s*:\s*(.*)$", corpo)
                if not m or norm(m.group(1)) not in _KW_TOPO:
                    raise ErroSintaxe(f"linha não reconhecida: «{corpo[:40]}»")
                k, v = norm(m.group(1)), m.group(2).strip()
                if k == "base":
                    base.nome = v
                elif k == "descricao":
                    base.descricao = (base.descricao + " " + v).strip()
                elif k in ("meta", "metas"):
                    base.metas += [str(x) for x in _itens(v)]
                elif k == "estrategia":
                    base.estrategia = norm(v)
                elif k == "fato":
                    a, val = parse_fato(v)
                    base.fatos.append((a, val))
                continue
            # linha indentada: propriedade do bloco atual ou continuação de regra
            if bloco is None:
                raise ErroSintaxe("linha indentada fora de um bloco")
            m = re.match(r"^([A-Za-zÀ-ÿ_]+)\s*:\s*(.*)$", corpo)
            if bloco[0] == "var":
                v = bloco[1]
                if not m or norm(m.group(1)) not in _KW_VAR:
                    raise ErroSintaxe(f"propriedade desconhecida da variável: «{corpo[:30]}»")
                k, val = norm(m.group(1)), m.group(2).strip()
                if k == "rotulo":
                    v.rotulo = val
                elif k == "pergunta":
                    v.pergunta = val
                elif k == "valores":
                    v.valores = _itens(val)
                elif k == "tipo":
                    v.tipo = norm(val)
                elif k == "perguntavel":
                    v.perguntavel = _sim(val)
                elif k == "multivalorada":
                    v.multivalorada = _sim(val)
                elif k == "descricao":
                    v.descricao = val
            else:
                d = bloco[1]
                if m and norm(m.group(1)) == "explicacao":
                    d["explicacao"] = m.group(2).strip()
                    d["em_expl"] = True
                elif d["em_expl"]:
                    d["explicacao"] += " " + corpo
                else:
                    d["texto"] += " " + corpo
        except ErroSintaxe as e:
            if e.linha:
                raise
            raise ErroSintaxe(str(e), n) from None
    fechar()
    # variáveis usadas nas regras/fatos e não declaradas
    for r in base.regras:
        for c in r.condicoes:
            base.garantir_variavel(c.atributo, c.valor)
        for c in r.conclusoes:
            base.garantir_variavel(c.atributo, c.valor)
    for a, val in base.fatos:
        base.garantir_variavel(a, val)
    return base


# ====================================================================== escrita do .kb
_RESERVADAS = {"se", "entao", "e", "ou", "nao", "em", "verdadeiro"}


def q(valor):
    """Texto de um valor/atributo no .kb: com aspas se necessário."""
    if isinstance(valor, bool):
        valor = "sim" if valor else "não"
    if isinstance(valor, (int, float)):
        return fmt_valor(valor)
    s = str(valor)
    if re.fullmatch(r"[\wÀ-ÿ.\-/%$]+", s) and norm(s) not in _RESERVADAS and como_numero(s) is None:
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _cond_kb(c):
    if c.operador == "em":
        t = f"{q(c.atributo)} EM [{', '.join(q(x) for x in c.valor)}]"
        return t.replace(" EM [", " NÃO EM [") if c.negada else t
    t = f"{q(c.atributo)} {c.operador} {q(c.valor)}"
    return f"NÃO ({t})" if c.negada else t


def regra_kb(r):
    se = " E ".join(_cond_kb(c) for c in r.condicoes) or "VERDADEIRO"
    entao = " E ".join(f"{q(c.atributo)} = {q(c.valor)}" for c in r.conclusoes)
    cab = f"REGRA {r.id}" + (f" [prioridade {r.prioridade}]" if r.prioridade else "")
    s = f"{cab}: SE {se} ENTÃO {entao}"
    if r.explicacao:
        s += f"\n    EXPLICAÇÃO: {r.explicacao}"
    return s


def escrever_kb(base):
    L = [f"BASE: {base.nome}"]
    if base.descricao:
        L.append(f"DESCRIÇÃO: {base.descricao}")
    if base.metas:
        L.append("META: " + ", ".join(q(m) for m in base.metas))
    L.append(f"ESTRATÉGIA: {base.estrategia}")
    L.append("")
    for v in base.variaveis.values():
        L.append(f"VARIÁVEL {q(v.nome)}")
        if v.rotulo and v.rotulo != v.nome:
            L.append(f"    RÓTULO: {v.rotulo}")
        if v.descricao:
            L.append(f"    DESCRIÇÃO: {v.descricao}")
        if v.pergunta:
            L.append(f"    PERGUNTA: {v.pergunta}")
        if v.valores:
            L.append("    VALORES: " + ", ".join(q(x) for x in v.valores))
        if v.tipo != "texto":
            L.append(f"    TIPO: {v.tipo}")
        if v.perguntavel is not None:
            L.append(f"    PERGUNTÁVEL: {'sim' if v.perguntavel else 'não'}")
        if v.multivalorada:
            L.append("    MULTIVALORADA: sim")
        L.append("")
    for a, val in base.fatos:
        L.append(f"FATO: {q(a)} = {q(val)}")
    if base.fatos:
        L.append("")
    for r in base.regras:
        L.append(regra_kb(r))
    return "\n".join(L) + "\n"


# ====================================================================== JSON
def para_dict(base):
    return {
        "nome": base.nome, "descricao": base.descricao, "metas": base.metas, "estrategia": base.estrategia,
        "variaveis": [{"nome": v.nome, "rotulo": v.rotulo, "valores": v.valores, "pergunta": v.pergunta,
                       "tipo": v.tipo, "perguntavel": v.perguntavel, "multivalorada": v.multivalorada,
                       "descricao": v.descricao} for v in base.variaveis.values()],
        "fatos": [[a, v] for a, v in base.fatos],
        "regras": [{"id": r.id, "prioridade": r.prioridade, "explicacao": r.explicacao,
                    "se": [{"atributo": c.atributo, "operador": c.operador,
                            "valor": list(c.valor) if c.operador == "em" else c.valor, "negada": c.negada}
                           for c in r.condicoes],
                    "entao": [{"atributo": c.atributo, "valor": c.valor} for c in r.conclusoes]}
                   for r in base.regras],
    }


def de_dict(d):
    b = BaseConhecimento(d.get("nome", "Base"), d.get("descricao", ""), {}, [], [], list(d.get("metas", [])),
                         d.get("estrategia", "ordem"))
    for v in d.get("variaveis", []):
        b.variaveis[v["nome"]] = Variavel(v["nome"], v.get("rotulo", ""), list(v.get("valores", [])),
                                          v.get("pergunta", ""), v.get("tipo", "texto"), v.get("perguntavel"),
                                          v.get("multivalorada", False), v.get("descricao", ""))
    b.fatos = [(a, v) for a, v in d.get("fatos", [])]
    for r in d.get("regras", []):
        conds = [Condicao(c["atributo"], c["operador"], tuple(c["valor"]) if c["operador"] == "em" else c["valor"],
                          c.get("negada", False)) for c in r["se"]]
        b.regras.append(Regra(r["id"], conds, [Conclusao(c["atributo"], c["valor"]) for c in r["entao"]],
                              r.get("prioridade", 0), r.get("explicacao", "")))
    return b


def salvar(base, caminho):
    caminho = str(caminho)
    if caminho.lower().endswith(".json"):
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(para_dict(base), f, ensure_ascii=False, indent=2)
    else:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(escrever_kb(base))


def carregar(caminho):
    with open(caminho, encoding="utf-8") as f:
        txt = f.read()
    if str(caminho).lower().endswith(".json"):
        return de_dict(json.loads(txt))
    return ler_kb(txt)
