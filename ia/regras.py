"""Extração e avaliação de regras SE ... ENTÃO ... a partir de árvores de decisão."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .arvores import No


@dataclass
class Regra:
    id: str
    condicoes: list            # [(atributo, (valores...))]  -- conjunção
    classe: str
    n: int = 0                 # exemplos de treino cobertos pela regra
    acertos: int = 0           # ... dos quais da classe prevista

    @property
    def confianca(self):
        return self.acertos / self.n if self.n else 0.0

    def cobre(self, exemplo):
        return all(exemplo[a] in vals for a, vals in self.condicoes)

    def texto_condicao(self, cond):
        a, vals = cond
        return f"{a} = {vals[0]}" if len(vals) == 1 else f"{a} ∈ {{{', '.join(vals)}}}"

    def texto(self, nome_classe):
        conds = " E ".join(self.texto_condicao(c) for c in self.condicoes) or "VERDADEIRO"
        return f"SE {conds} ENTÃO {nome_classe} = {self.classe}"

    def para_dict(self):
        return {"id": self.id, "condicoes": [[a, list(v)] for a, v in self.condicoes],
                "classe": self.classe, "n": self.n, "acertos": self.acertos}


def _mesclar(caminho):
    """Junta condições repetidas sobre o mesmo atributo (interseção de conjuntos de valores)."""
    ordem, vals = [], {}
    for a, v in caminho:
        if a not in vals:
            ordem.append(a)
            vals[a] = tuple(v)
        else:
            vals[a] = tuple(x for x in vals[a] if x in v)
    return [(a, vals[a]) for a in ordem]


def extrair_regras(raiz, prefixo="R"):
    """Uma regra por folha (caminho raiz -> folha). Ordem: percurso em profundidade, da esquerda p/ direita."""
    regras = []

    def rec(no, caminho):
        if no.folha:
            regras.append(Regra(f"{prefixo}{len(regras) + 1}", _mesclar(caminho), no.classe,
                                no.n, no.contagem[no.classe]))
            return
        for _, valores, filho in no.ramos:
            rec(filho, caminho + [(no.atributo, valores)])

    rec(raiz, [])
    return regras


def classificar(regras, exemplo, padrao):
    """Primeira regra que cobre o exemplo; senão, a classe padrão."""
    for r in regras:
        if r.cobre(exemplo):
            return r.classe, r
    return padrao, None


def estatisticas(regras):
    k = len(regras)
    tot = sum(len(r.condicoes) for r in regras)
    return {"regras": k, "condicoes_total": tot, "condicoes_media": tot / k if k else 0.0,
            "condicoes_max": max((len(r.condicoes) for r in regras), default=0)}


def salvar_json(regras, caminho, meta=None):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"meta": meta or {}, "regras": [r.para_dict() for r in regras]}, f,
                  ensure_ascii=False, indent=2)


def carregar_json(caminho):
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("meta", {}), [Regra(r["id"], [(a, tuple(v)) for a, v in r["condicoes"]], r["classe"],
                                     r.get("n", 0), r.get("acertos", 0)) for r in d["regras"]]
