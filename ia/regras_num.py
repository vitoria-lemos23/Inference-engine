"""Regras SE...ENTÃO a partir de árvores scikit-learn com atributos numéricos."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .relatorio import br


@dataclass
class RegraNum:
    id: str
    intervalos: list                  # [(atributo, inferior|None, superior|None)]  inferior < x <= superior
    classe: object
    folha: int = 0
    n: int = 0                        # treino coberto
    acertos: int = 0
    n_teste: int = 0
    acertos_teste: int = 0

    @property
    def precisao(self):
        return self.acertos / self.n if self.n else 0.0

    @property
    def precisao_teste(self):
        return self.acertos_teste / self.n_teste if self.n_teste else float("nan")

    def cobre(self, x, nomes):
        for a, lo, hi in self.intervalos:
            v = x[nomes.index(a)]
            if (lo is not None and not v > lo) or (hi is not None and not v <= hi):
                return False
        return True

    def condicoes_texto(self, casas=1):
        out = []
        for a, lo, hi in self.intervalos:
            if lo is not None and hi is not None:
                out.append(f"{br(lo, casas)} < {a} ≤ {br(hi, casas)}")
            elif hi is not None:
                out.append(f"{a} ≤ {br(hi, casas)}")
            else:
                out.append(f"{a} > {br(lo, casas)}")
        return out

    def texto(self, nome_classe, rotulo_classe=lambda c: c, casas=1):
        c = " E ".join(self.condicoes_texto(casas)) or "VERDADEIRO"
        return f"SE {c} ENTÃO {nome_classe} = {rotulo_classe(self.classe)}"

    def para_dict(self):
        return {"id": self.id, "intervalos": [[a, lo, hi] for a, lo, hi in self.intervalos], "classe": str(self.classe),
                "n": self.n, "acertos": self.acertos, "n_teste": self.n_teste, "acertos_teste": self.acertos_teste}


def regras_de_arvore_numerica(modelo, nomes, X_treino, y_treino, X_teste=None, y_teste=None, prefixo="R"):
    """Uma regra por folha. `modelo` é um DecisionTreeClassifier já treinado (X sem NaN)."""
    t = modelo.tree_
    classes = list(modelo.classes_)
    regras = []

    def rec(no, limites):
        if t.children_left[no] == -1:
            valor = t.value[no][0]
            classe = classes[int(np.argmax(valor))]
            ivs = [(a, lo, hi) for a, (lo, hi) in limites.items()]
            regras.append(RegraNum(f"{prefixo}{len(regras) + 1}", ivs, classe, folha=no))
            return
        a = nomes[t.feature[no]]
        thr = float(t.threshold[no])
        lo, hi = limites.get(a, (None, None))
        esq = dict(limites)
        esq[a] = (lo, thr if hi is None else min(hi, thr))
        dir_ = dict(limites)
        dir_[a] = (thr if lo is None else max(lo, thr), hi)
        rec(t.children_left[no], esq)
        rec(t.children_right[no], dir_)

    rec(0, {})
    por_folha = {r.folha: r for r in regras}
    for X, y, suf in ((X_treino, y_treino, ""), (X_teste, y_teste, "_teste")):
        if X is None:
            continue
        folhas = modelo.apply(X)
        for f, real in zip(folhas, y):
            r = por_folha[int(f)]
            setattr(r, "n" + suf, getattr(r, "n" + suf) + 1)
            if real == r.classe:
                setattr(r, "acertos" + suf, getattr(r, "acertos" + suf) + 1)
    return regras


def classificar_num(regras, x, nomes, padrao):
    for r in regras:
        if r.cobre(x, nomes):
            return r.classe
    return padrao
