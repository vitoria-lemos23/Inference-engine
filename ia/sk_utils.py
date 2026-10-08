"""Utilidades para usar scikit-learn com bases categóricas e obter regras SE...ENTÃO legíveis."""
from __future__ import annotations

import numpy as np

from .regras import Regra


def nomes_dummies(base):
    """[(atributo, valor)] na ordem das colunas one-hot."""
    return [(a, v) for a in base.atributos for v in base.dominios[a]]


def codificar(base, linhas=None):
    """One-hot determinístico (os domínios são fixos, não dependem do conjunto de treino)."""
    linhas = base.linhas if linhas is None else linhas
    cols = nomes_dummies(base)
    X = np.zeros((len(linhas), len(cols)), dtype=float)
    for i, l in enumerate(linhas):
        for j, (a, v) in enumerate(cols):
            X[i, j] = 1.0 if l[a] == v else 0.0
    return X


def rotulos(base, linhas=None):
    linhas = base.linhas if linhas is None else linhas
    return np.array([l[base.classe] for l in linhas])


def nome_dummy(a, v):
    return f"{a} = {v}"


def regras_de_arvore_sklearn(modelo, base, prefixo="R"):
    """Converte um DecisionTreeClassifier treinado em one-hot para regras com condições do tipo
    `atributo = valor` ou `atributo ∈ {valores}` (condições "≠" viram o conjunto dos valores restantes)."""
    t = modelo.tree_
    feats = nomes_dummies(base)
    regras = []

    def condicoes(caminho):
        ordem, permitido = [], {}
        for f, igual in caminho:
            a, v = feats[f]
            if a not in permitido:
                permitido[a] = list(base.dominios[a])
                ordem.append(a)
            permitido[a] = [v] if (igual and v in permitido[a]) else ([] if igual else [x for x in permitido[a] if x != v])
        if any(not permitido[a] for a in ordem):
            return None   # caminho impossível
        return [(a, tuple(permitido[a])) for a in ordem]

    def rec(no, caminho):
        if t.children_left[no] == -1:
            conds = condicoes(caminho)
            if conds is None:
                return
            classe = modelo.classes_[int(np.argmax(t.value[no][0]))]
            regras.append(Regra(f"{prefixo}{len(regras) + 1}", conds, str(classe)))
            return
        f = int(t.feature[no])
        rec(t.children_left[no], caminho + [(f, False)])    # valor_dummy <= 0.5  ->  atributo != valor
        rec(t.children_right[no], caminho + [(f, True)])    # valor_dummy >  0.5  ->  atributo  = valor

    rec(0, [])
    # cobertura e acertos medidos sobre a base de treino
    for r in regras:
        cobertos = [l for l in base.linhas if r.cobre(l)]
        r.n = len(cobertos)
        r.acertos = sum(l[base.classe] == r.classe for l in cobertos)
    return regras
