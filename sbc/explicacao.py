"""Módulo de explicação: Como?, Por quê?, Por que não? e trilha de inferência."""
from __future__ import annotations

from .modelo import fmt_valor, valores_iguais


def _rot(motor):
    return motor.base.rotulo


# ====================================================================== COMO?
def arvore_como(motor, atributo, valor=None, _vistos=None):
    """Árvore de justificativa de um fato: dict {fato, origem, regra, premissas:[...]}."""
    _vistos = _vistos if _vistos is not None else set()
    f = motor.fato(atributo, valor)
    if f is None:
        return None
    no = {"atributo": f.atributo, "valor": f.valor, "origem": f.origem, "regra": f.regra_id, "passo": f.passo,
          "premissas": [], "repetido": False}
    chave = (f.atributo, str(f.valor))
    if chave in _vistos:
        no["repetido"] = True
        return no
    _vistos.add(chave)
    if f.origem == "regra":
        for a, v in f.premissas:
            sub = arvore_como(motor, a, v, _vistos)
            if sub is not None:
                no["premissas"].append(sub)
    return no


def como(motor, atributo, valor=None):
    """Explica COMO um fato foi estabelecido (de onde veio e por qual cadeia de regras)."""
    rot = _rot(motor)
    if atributo not in motor.base.variaveis:
        v = motor.base.variavel(atributo)
        atributo = v.nome if v else atributo
    arv = arvore_como(motor, atributo, valor)
    if arv is None:
        alvo = f"{rot(atributo)}" + (f" = {fmt_valor(valor)}" if valor is not None else "")
        if atributo in motor.desconhecidos:
            return f"Não concluí «{alvo}»: o usuário informou que não sabe."
        return f"Não tenho «{alvo}» na memória: ainda não foi informado nem concluído."
    linhas = []

    def rec(no, ind):
        pad = "    " * ind
        nome = f"{rot(no['atributo'])} = {fmt_valor(no['valor'])}"
        if no["origem"] == "usuario":
            linhas.append(f"{pad}• {nome} — informado pelo usuário.")
        elif no["origem"] == "inicial":
            linhas.append(f"{pad}• {nome} — fato inicial da base de conhecimento.")
        else:
            r = motor.base.regra(no["regra"])
            texto = r.texto(rot) if r else "?"
            if no["repetido"]:
                linhas.append(f"{pad}• {nome} — (explicado acima; regra {no['regra']}).")
                return
            linhas.append(f"{pad}• {nome} — concluído pela regra {no['regra']}:")
            linhas.append(f"{pad}    {texto}")
            if r and r.explicacao:
                linhas.append(f"{pad}    (justificativa da regra: {r.explicacao})")
            if no["premissas"]:
                linhas.append(f"{pad}    porque:")
                for p in no["premissas"]:
                    rec(p, ind + 2)

    rec(arv, 0)
    return "\n".join(linhas)


# ====================================================================== POR QUÊ?
def por_que(motor, pergunta, nivel=0):
    """Explica POR QUE o sistema está fazendo a pergunta `pergunta`.
    nivel 0: motivo imediato; cada novo "por quê?" sobe um degrau na cadeia de objetivos."""
    rot = _rot(motor)
    ctx = pergunta.contexto
    alvo = rot(pergunta.atributo)
    if not ctx:
        return (f"Estou perguntando «{alvo}» porque é a própria meta da consulta e nenhuma regra "
                f"conseguiu concluí-la.")
    i = len(ctx) - 1 - nivel
    if i < 0:
        meta = ctx[0]
        return (f"Chegamos ao topo da cadeia: o objetivo desta consulta é estabelecer «{rot(meta.atributo)}»"
                + (f" = {fmt_valor(meta.desejado)}" if meta.desejado is not None else "") + ".")
    f = ctx[i]
    r = f.regra
    cond = r.condicoes[f.indice]
    meta_txt = rot(f.atributo) + (f" = {fmt_valor(f.desejado)}" if f.desejado is not None else "")
    concl = " E ".join(c.texto(rot) for c in r.conclusoes)
    if nivel == 0:
        s = (f"Estou perguntando «{alvo}» porque preciso verificar a condição «{cond.texto(rot)}» "
             f"da regra {r.id}:\n    {r.texto(rot)}\n"
             f"Se ela se confirmar (e as demais condições também), concluo «{concl}»"
             + ("." if concl == meta_txt else f", que ajuda a estabelecer «{meta_txt}»."))
    else:
        s = (f"Subindo um nível: a regra {r.id} está sendo avaliada para estabelecer «{meta_txt}»; "
             f"neste momento ela precisa verificar a condição «{cond.texto(rot)}»:\n    {r.texto(rot)}")
    if i == 0:
        s += f"\n(Este é o objetivo principal da consulta: «{rot(ctx[0].atributo)}».)"
    return s


# ====================================================================== POR QUE NÃO?
def por_que_nao(motor, atributo, valor):
    """Explica por que `atributo = valor` NÃO foi concluído."""
    rot = _rot(motor)
    v = motor.base.variavel(atributo)
    if v:
        atributo = v.nome
    alvo = f"{rot(atributo)} = {fmt_valor(valor)}"
    if motor.fato(atributo, valor):
        return f"Mas «{alvo}» foi estabelecido!\n" + como(motor, atributo, valor)
    L = []
    atual = motor.fato(atributo)
    if atual is not None and not motor._multi(atributo):
        L.append(f"«{rot(atributo)}» já tem o valor {fmt_valor(atual.valor)}, "
                 f"e a variável admite um único valor.")
    regras = [r for r in motor.base.regras
              if any(c.atributo == atributo and valores_iguais(c.valor, valor) for c in r.conclusoes)]
    if not regras:
        if L:
            L.append(f"Além disso, nenhuma regra conclui «{alvo}».")
            L.append("Veja como o valor atual foi obtido:")
            L.append(como(motor, atributo, atual.valor))
            return "\n".join(L)
        if motor.base.perguntavel(atributo):
            return f"Nenhuma regra conclui «{alvo}»; esse dado só poderia vir do usuário, e não foi informado."
        return f"Nenhuma regra da base conclui «{alvo}»."
    L.append(f"As regras que concluiriam «{alvo}» e o motivo de não terem sido aplicadas:")
    for r in regras:
        falha = None
        for c in r.condicoes:
            res = c.avaliar(motor.valores(c.atributo))
            if res is not True:
                falha = (c, res)
                break
        if falha is None:
            L.append(f"  • {r.id}: todas as condições são verdadeiras, mas a regra ainda não foi disparada "
                     f"(execute o encadeamento).")
        else:
            c, res = falha
            if res is None:
                motivo = f"«{rot(c.atributo)}» é desconhecido"
            else:
                motivo = (f"a condição «{c.texto(rot)}» é falsa (valor atual: "
                          f"{', '.join(fmt_valor(x) for x in motor.valores(c.atributo))})")
            L.append(f"  • {r.id} ({r.texto(rot)}): {motivo}.")
    if atual is not None and not motor._multi(atributo):
        L.append("Veja como o valor atual foi obtido:")
        L.append(como(motor, atributo, atual.valor))
    return "\n".join(L)


# ====================================================================== trilha
def trilha(motor, ultimos=None):
    ev = motor.eventos if not ultimos else motor.eventos[-ultimos:]
    if not ev:
        return "(nenhum evento registrado ainda)"
    return "\n".join(f"{e.passo:>3}. {e.texto}" for e in ev)


def resumo_fatos(motor):
    if not motor.fatos and not motor.desconhecidos:
        return "(memória vazia: nada informado nem concluído)"
    L = []
    for a, fs in motor.fatos.items():
        for f in fs:
            origem = {"usuario": "informado", "inicial": "fato inicial", "regra": f"regra {f.regra_id}"}[f.origem]
            L.append(f"  {motor.base.rotulo(a)} = {fmt_valor(f.valor)}   [{origem}]")
    for a in sorted(motor.desconhecidos):
        L.append(f"  {motor.base.rotulo(a)} = (desconhecido)")
    return "\n".join(L)
