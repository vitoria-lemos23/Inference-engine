"""Métricas de classificação binária calculadas à mão (conferidas com scikit-learn nos testes)."""
from __future__ import annotations

import math


def matriz_confusao(reais, previstos, positivo=1):
    """Retorna dict com VP, FP, FN, VN (classe `positivo` = positiva)."""
    vp = fp = fn = vn = 0
    for r, p in zip(reais, previstos):
        if r == positivo and p == positivo:
            vp += 1
        elif r != positivo and p == positivo:
            fp += 1
        elif r == positivo:
            fn += 1
        else:
            vn += 1
    return {"VP": vp, "FP": fp, "FN": fn, "VN": vn}


def _div(a, b):
    return a / b if b else 0.0


def metricas(reais, previstos, positivo=1):
    m = matriz_confusao(reais, previstos, positivo)
    vp, fp, fn, vn = m["VP"], m["FP"], m["FN"], m["VN"]
    prec = _div(vp, vp + fp)
    rev = _div(vp, vp + fn)                       # recall / sensibilidade
    esp = _div(vn, vn + fp)                       # especificidade (recall da classe negativa)
    f1 = _div(2 * prec * rev, prec + rev)
    prec_neg = _div(vn, vn + fn)
    f1_neg = _div(2 * prec_neg * esp, prec_neg + esp)
    return {**m, "n": vp + fp + fn + vn,
            "acuracia": _div(vp + vn, vp + fp + fn + vn),
            "precisao": prec, "recall": rev, "f1": f1,
            "especificidade": esp, "precisao_neg": prec_neg, "f1_neg": f1_neg,
            "f1_macro": (f1 + f1_neg) / 2,
            "acuracia_balanceada": (rev + esp) / 2,
            "mcc": _div(vp * vn - fp * fn, math.sqrt((vp + fp) * (vp + fn) * (vn + fp) * (vn + fn)))}


def auc_roc(reais, escores, positivo=1):
    """Área sob a curva ROC pela estatística de Mann-Whitney (empates contam 1/2)."""
    pos = [s for r, s in zip(reais, escores) if r == positivo]
    neg = [s for r, s in zip(reais, escores) if r != positivo]
    if not pos or not neg:
        return float("nan")
    total = 0.0
    for p in pos:
        for n in neg:
            total += 1.0 if p > n else 0.5 if p == n else 0.0
    return total / (len(pos) * len(neg))
