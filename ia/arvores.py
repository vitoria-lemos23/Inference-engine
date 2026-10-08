"""Indução de árvores de decisão -- ID3, C4.5 e CART implementados do zero.

Todos os algoritmos registram um *passo a passo* (lista de ``Passo``) com TODOS os números
calculados em cada nó (entropia, ganho, razão de ganho, Gini...), de modo que a construção
"manual" pode ser conferida e reproduzida (ver ``ia.relatorio``).

Resumo das diferenças implementadas
-----------------------------------
ID3   : critério = ganho de informação (entropia); divisão multivalorada (um ramo por valor);
        pára quando o nó é puro ou não há mais atributos; sem poda.
C4.5  : critério = razão de ganho (ganho / informação da divisão), restrita aos atributos
        cujo ganho >= ganho médio (heurística de Quinlan); divisão multivalorada;
        poda pessimista (erro superior do intervalo de confiança binomial, CF = 25 %).
CART  : critério = impureza de Gini; divisão SEMPRE binária (subconjunto de valores vs. resto),
        testando todas as 2^(k-1)-1 partições de um atributo com k valores; sem poda
        (a poda por custo-complexidade é discutida no relatório).
"""
from __future__ import annotations

import copy
import itertools
import math
from dataclasses import dataclass, field
from statistics import NormalDist

EPS = 1e-12


# ====================================================================== medidas
def entropia(contagens):
    """H = -sum p_i log2 p_i  (contagens por classe)."""
    n = sum(contagens)
    if n == 0:
        return 0.0
    return max(0.0, -sum((c / n) * math.log2(c / n) for c in contagens if c > 0))


def gini(contagens):
    """G = 1 - sum p_i^2."""
    n = sum(contagens)
    if n == 0:
        return 0.0
    return 1.0 - sum((c / n) ** 2 for c in contagens)


def info_divisao(tamanhos):
    """SplitInfo = -sum |S_v|/|S| log2(|S_v|/|S|)."""
    n = sum(tamanhos)
    return max(0.0, -sum((t / n) * math.log2(t / n) for t in tamanhos if t > 0))


# ====================================================================== estruturas
@dataclass
class No:
    id: int
    contagem: dict          # classe -> nº de exemplos de treino que chegaram ao nó
    classe: str             # classe majoritária
    atributo: str | None = None
    # lista de (rotulo, valores, filho). Multivalorada: valores=(v,). Binária: (S) e (complemento).
    ramos: list = field(default_factory=list)

    @property
    def folha(self):
        return not self.ramos

    @property
    def n(self):
        return sum(self.contagem.values())

    @property
    def erros(self):
        return self.n - self.contagem[self.classe]


@dataclass
class Passo:
    """Registro de tudo o que foi calculado em um nó (para o passo a passo)."""
    no_id: int
    caminho: list           # [(atributo, valores)] condições até chegar aqui
    ids: list               # IDs dos exemplos no nó
    contagem: dict
    impureza: float         # entropia (ID3/C4.5) ou Gini (CART)
    candidatos: list = field(default_factory=list)
    escolhido: str | None = None
    detalhe: dict = field(default_factory=dict)   # ex.: média dos ganhos, partição escolhida
    motivo: str = ""        # 'puro' | 'sem atributos' | 'sem ganho' | 'dividido'


# ====================================================================== construção
class _Construtor:
    def __init__(self, base, algoritmo):
        self.base = base
        self.alg = algoritmo
        self.passos = []
        self._prox = 0

    def novo_id(self):
        self._prox += 1
        return self._prox

    # -------------------------------------------------------------- nó genérico
    def _no(self, linhas):
        cont = self.base.contar(linhas)
        return No(self.novo_id(), dict(cont), self.base.maioria(cont))

    def construir(self, linhas, atributos, caminho):
        b = self.base
        no = self._no(linhas)
        impureza = gini(no.contagem.values()) if self.alg == "CART" else entropia(no.contagem.values())
        passo = Passo(no.id, list(caminho), [l[b.id_col] for l in linhas], dict(no.contagem), impureza)
        self.passos.append(passo)

        if sum(1 for v in no.contagem.values() if v > 0) == 1:
            passo.motivo = "puro"
            return no
        cands = [a for a in atributos if len(b.valores(a, linhas)) >= 2]
        if not cands:
            passo.motivo = "sem atributos"
            return no

        if self.alg == "CART":
            escolha = self._escolher_cart(linhas, cands, passo)
        else:
            escolha = self._escolher_multi(linhas, cands, passo)

        if escolha is None:
            passo.motivo = "sem ganho"
            return no
        passo.motivo = "dividido"
        passo.escolhido = escolha["atributo"]
        no.atributo = escolha["atributo"]

        if self.alg == "CART":
            S = escolha["esq"]
            comp = tuple(v for v in b.valores(no.atributo, linhas) if v not in S)
            for valores in (S, comp):
                sub = [l for l in linhas if l[no.atributo] in valores]
                filho = self.construir(sub, atributos, caminho + [(no.atributo, valores)])
                no.ramos.append((_rotulo(valores), valores, filho))
        else:
            restantes = [a for a in atributos if a != no.atributo]
            for v in b.valores(no.atributo, linhas):
                sub = [l for l in linhas if l[no.atributo] == v]
                filho = self.construir(sub, restantes, caminho + [(no.atributo, (v,))])
                no.ramos.append((v, (v,), filho))
        return no

    # -------------------------------------------------------------- ID3 / C4.5
    def _escolher_multi(self, linhas, cands, passo):
        b = self.base
        H = passo.impureza
        n = len(linhas)
        avals = []
        for a in cands:
            ramos, soma = [], 0.0
            for v in b.valores(a, linhas):
                sub = [l for l in linhas if l[a] == v]
                c = b.contar(sub)
                h = entropia(c.values())
                soma += len(sub) / n * h
                ramos.append({"valor": v, "n": len(sub), "contagem": dict(c), "entropia": h})
            ganho = H - soma
            si = info_divisao([r["n"] for r in ramos])
            avals.append({"atributo": a, "ramos": ramos, "entropia_condicional": soma, "ganho": ganho,
                          "info_divisao": si, "razao_ganho": (ganho / si) if si > EPS else 0.0})
        passo.candidatos = avals

        if self.alg == "ID3":
            melhor = None
            for av in avals:
                if melhor is None or av["ganho"] > melhor["ganho"] + EPS:
                    melhor = av
            return melhor
        # C4.5: heurística do ganho médio + maior razão de ganho
        media = sum(av["ganho"] for av in avals) / len(avals)
        passo.detalhe["ganho_medio"] = media
        for av in avals:
            av["elegivel"] = av["ganho"] >= media - 1e-9
        melhor = None
        for av in avals:
            if av["elegivel"] and (melhor is None or av["razao_ganho"] > melhor["razao_ganho"] + EPS):
                melhor = av
        if melhor is None or melhor["ganho"] <= EPS:
            return None
        return melhor

    # -------------------------------------------------------------- CART
    def _escolher_cart(self, linhas, cands, passo):
        b = self.base
        G = passo.impureza
        n = len(linhas)
        avals, melhor_global = [], None
        for a in cands:
            vals = b.valores(a, linhas)
            particoes, melhor = [], None
            for k in range(1, len(vals)):
                for S in itertools.combinations(vals, k):
                    if vals[0] not in S:        # evita partições simétricas repetidas
                        continue
                    esq = [l for l in linhas if l[a] in S]
                    dire = [l for l in linhas if l[a] not in S]
                    ce, cd = b.contar(esq), b.contar(dire)
                    ge, gd = gini(ce.values()), gini(cd.values())
                    gp = len(esq) / n * ge + len(dire) / n * gd
                    p = {"esq": S, "dir": tuple(v for v in vals if v not in S),
                         "n_esq": len(esq), "cont_esq": dict(ce), "gini_esq": ge,
                         "n_dir": len(dire), "cont_dir": dict(cd), "gini_dir": gd,
                         "gini_ponderado": gp, "delta": G - gp}
                    particoes.append(p)
                    if melhor is None or gp < melhor["gini_ponderado"] - EPS:
                        melhor = p
            av = {"atributo": a, "particoes": particoes, "melhor": melhor}
            avals.append(av)
            if melhor_global is None or melhor["gini_ponderado"] < melhor_global[1]["gini_ponderado"] - EPS:
                melhor_global = (a, melhor)
        passo.candidatos = avals
        if melhor_global is None or melhor_global[1]["delta"] <= EPS:
            return None
        passo.detalhe["particao"] = melhor_global[1]
        return {"atributo": melhor_global[0], "esq": melhor_global[1]["esq"]}


def _rotulo(valores):
    return valores[0] if len(valores) == 1 else "{" + ", ".join(valores) + "}"


def construir(base, algoritmo, podar=False, cf=0.25):
    """Constrói a árvore. algoritmo ∈ {'ID3','C4.5','CART'}. Retorna (raiz, passos[, log_poda])."""
    algoritmo = algoritmo.upper()
    if algoritmo not in ("ID3", "C4.5", "CART"):
        raise ValueError("algoritmo deve ser ID3, C4.5 ou CART")
    c = _Construtor(base, algoritmo)
    raiz = c.construir(base.linhas, list(base.atributos), [])
    if podar:
        raiz, log = podar_pessimista(raiz, cf)
        return raiz, c.passos, log
    return raiz, c.passos


# ====================================================================== poda (C4.5)
def erros_adicionais(N, e, cf=0.25):
    """Termo ``AddErrs`` do C4.5: limite superior (conf. 1-CF) do nº de erros esperados em N casos
    com e erros observados (aproximação normal do intervalo binomial, como no código de Quinlan)."""
    if N <= 0:
        return 0.0
    if e < 1e-6:
        return N * (1 - math.exp(math.log(cf) / N))
    if e < 0.9999:
        v0 = N * (1 - math.exp(math.log(cf) / N))
        return v0 + e * (erros_adicionais(N, 1.0, cf) - v0)
    if e + 0.5 >= N:
        return 0.67 * (N - e)
    z = NormalDist().inv_cdf(1 - cf)
    pr = (e + 0.5 + z * z / 2 + math.sqrt(z * ((e + 0.5) * (1 - (e + 0.5) / N) + z * z / 4))) / (N + z * z)
    return N * pr - e


def _estimativa_folha(no, cf):
    return no.erros + erros_adicionais(no.n, no.erros, cf)


def podar_pessimista(raiz, cf=0.25):
    """Poda por substituição de subárvore (erro pessimista do C4.5). Retorna (nova_raiz, log)."""
    raiz = copy.deepcopy(raiz)
    log = []

    def rec(no):
        if no.folha:
            return _estimativa_folha(no, cf)
        est_sub = sum(rec(f) for _, _, f in no.ramos)
        est_folha = _estimativa_folha(no, cf)
        podado = est_folha <= est_sub + 0.1
        log.append({"no_id": no.id, "atributo": no.atributo, "n": no.n, "erros_folha": no.erros,
                    "est_folha": est_folha, "est_subarvore": est_sub, "podado": podado,
                    "classe": no.classe})
        if podado:
            no.ramos = []
            no.atributo = None
            return est_folha
        return est_sub

    rec(raiz)
    return raiz, log


# ====================================================================== uso da árvore
def prever(no, exemplo):
    """Classifica um exemplo. Valor nunca visto no nó -> classe majoritária do nó."""
    while not no.folha:
        for _, valores, filho in no.ramos:
            if exemplo[no.atributo] in valores:
                no = filho
                break
        else:
            return no.classe
    return no.classe


def caminho_decisao(no, exemplo):
    """Lista de (atributo, valores) seguidos pelo exemplo até a folha, e a folha."""
    trilha = []
    while not no.folha:
        for _, valores, filho in no.ramos:
            if exemplo[no.atributo] in valores:
                trilha.append((no.atributo, valores))
                no = filho
                break
        else:
            break
    return trilha, no


def acuracia(no, base, linhas=None):
    linhas = base.linhas if linhas is None else linhas
    return sum(prever(no, l) == l[base.classe] for l in linhas) / len(linhas)


def leave_one_out(base, algoritmo, **kw):
    """Validação leave-one-out. Retorna (acurácia, lista de (id, real, previsto))."""
    res = []
    for i, l in enumerate(base.linhas):
        sub = base.sem_linha(i)
        r = construir(sub, algoritmo, **kw)[0]
        res.append((l[base.id_col], l[base.classe], prever(r, l)))
    return sum(r == p for _, r, p in res) / len(res), res


# ====================================================================== métricas da árvore
def folhas(no):
    if no.folha:
        return [no]
    return [f for _, _, filho in no.ramos for f in folhas(filho)]


def profundidade(no):
    return 0 if no.folha else 1 + max(profundidade(f) for _, _, f in no.ramos)


def nos_internos(no):
    if no.folha:
        return 0
    return 1 + sum(nos_internos(f) for _, _, f in no.ramos)


def atributos_usados(no):
    if no.folha:
        return []
    usados = [no.atributo]
    for _, _, f in no.ramos:
        for a in atributos_usados(f):
            if a not in usados:
                usados.append(a)
    return usados


# ====================================================================== validação cruzada
def validacao_cruzada(base, algoritmo, k=5, repeticoes=20, semente=42, **kw):
    """k-fold estratificado repetido. Retorna (média, desvio-padrão, lista de acurácias)."""
    import random
    import statistics

    rng = random.Random(semente)
    por_classe = {c: [i for i, l in enumerate(base.linhas) if l[base.classe] == c] for c in base.classes}
    acuracias = []
    for _ in range(repeticoes):
        dobras = [[] for _ in range(k)]
        for c, idx in por_classe.items():
            idx = idx[:]
            rng.shuffle(idx)
            for j, i in enumerate(idx):
                dobras[j % k].append(i)
        certos = 0
        for teste in dobras:
            treino = [l for i, l in enumerate(base.linhas) if i not in set(teste)]
            r = construir(base.com_linhas(treino), algoritmo, **kw)[0]
            certos += sum(prever(r, base.linhas[i]) == base.linhas[i][base.classe] for i in teste)
        acuracias.append(certos / len(base.linhas))
    return statistics.mean(acuracias), statistics.pstdev(acuracias), acuracias
