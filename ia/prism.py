"""PRISM (Cendrowska, 1987): geração direta de regras por "separar e conquistar", para atributos categóricos.

Para cada classe c: enquanto houver exemplos de c ainda não cobertos, constrói UMA regra
    SE a1 = v1 E a2 = v2 ... ENTÃO classe = c
acrescentando, a cada passo, a condição (atributo = valor) de maior precisão p/t entre os exemplos que a regra
já cobre (p = positivos, t = cobertos; desempate: maior p, depois ordem dos atributos/valores), até a regra ficar
pura (p = t) ou acabarem os atributos. Remove os exemplos cobertos e repete.

Extensões opcionais (desligadas = PRISM clássico):
  * precisao_min : encerra a regra quando p/t >= precisao_min (não exige pureza total);
  * cobertura_min: descarta regras que cobrem menos que `cobertura_min` exemplos da classe (poda pré-descarte);
  * max_condicoes: limite de condições por regra.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RegraPrism:
    id: str
    condicoes: list                  # [(atributo, valor)]
    classe: str
    n: int = 0                       # exemplos de treino cobertos
    acertos: int = 0                 # ... da classe prevista
    ordem_aprendizado: int = 0

    @property
    def precisao(self):
        return self.acertos / self.n if self.n else 0.0

    @property
    def laplace(self):
        return (self.acertos + 1) / (self.n + 2)           # estimativa de Laplace (binária); usada p/ resolver conflitos

    def cobre(self, ex):
        return all(ex[a] == v for a, v in self.condicoes)

    def texto(self, nome_classe="Classe"):
        c = " E ".join(f"{a} = {v}" for a, v in self.condicoes) or "VERDADEIRO"
        return f"SE {c} ENTÃO {nome_classe} = {self.classe}"


@dataclass
class ModeloPrism:
    regras: list
    classe_padrao: str
    classes: list
    atributo_classe: str = "Classe"
    historico: list = field(default_factory=list)            # passo a passo (para o relatório)

    def regras_ativas(self, ex):
        return [r for r in self.regras if r.cobre(ex)]

    def prever(self, ex, com_regra=False):
        """Entre as regras que cobrem o exemplo, vence a de maior precisão (Laplace), depois a de maior cobertura;
        sem nenhuma regra aplicável, a classe padrão (majoritária no treino)."""
        ativas = self.regras_ativas(ex)
        if not ativas:
            return (self.classe_padrao, None) if com_regra else self.classe_padrao
        r = max(ativas, key=lambda r: (r.laplace, r.n, -r.ordem_aprendizado))
        return (r.classe, r) if com_regra else r.classe

    def escore(self, ex, classe_positiva):
        """Escore em [0,1] para a classe positiva (para AUC): Laplace da melhor regra; 0.5 se nenhuma cobre."""
        ativas = self.regras_ativas(ex)
        if not ativas:
            return 0.5                                     # sem informação: neutro
        r = max(ativas, key=lambda r: (r.laplace, r.n, -r.ordem_aprendizado))
        return r.laplace if r.classe == classe_positiva else 1.0 - r.laplace


def prism(base, classes=None, precisao_min=1.0, cobertura_min=1, max_condicoes=None, rastrear=False):
    """Aprende o conjunto de regras. `base` é uma ia.base.Base (atributos categóricos).
    Implementação com máscaras booleanas (numpy) para ser rápida; a lógica é exatamente a descrita no cabeçalho."""
    import numpy as np

    classes = classes or list(base.classes)
    n = len(base.linhas)
    y = np.array([l[base.classe] for l in base.linhas])
    mascaras = {(a, v): np.array([l[a] == v for l in base.linhas]) for a in base.atributos for v in base.dominios[a]}
    candidatos = [(a, v) for a in base.atributos for v in base.dominios[a] if mascaras[(a, v)].any()]
    regras, historico = [], []
    contagem = base.contar()
    padrao = max(base.classes, key=lambda c: (contagem[c], base.classes.index(c)))
    for c in classes:
        eh_c = y == c
        restantes = np.ones(n, dtype=bool)                     # cada classe recomeça de todos os exemplos
        while (eh_c & restantes).any():
            cobertos = restantes.copy()
            condicoes, passos, usados = [], [], set()
            while True:
                p, t = int((eh_c & cobertos).sum()), int(cobertos.sum())
                if p == t or (t and p / t >= precisao_min) or (max_condicoes and len(condicoes) >= max_condicoes):
                    break
                melhor, tabela = None, []
                for a, v in candidatos:
                    if a in usados:
                        continue
                    sub = cobertos & mascaras[(a, v)]
                    ts = int(sub.sum())
                    if ts == 0:
                        continue
                    pp = int((eh_c & sub).sum())
                    if rastrear:
                        tabela.append((a, v, pp, ts))
                    chave = (pp / ts, pp)
                    if melhor is None or chave > melhor[0]:
                        melhor = (chave, a, v, sub)
                if melhor is None:
                    break
                _, a, v, sub = melhor
                if rastrear:
                    passos.append({"tabela": tabela, "escolhida": (a, v), "antes": (p, t)})
                condicoes.append((a, v))
                usados.add(a)
                cobertos = sub
            p = int((eh_c & cobertos).sum())
            if p >= cobertura_min or not regras:
                r = RegraPrism(f"R{len(regras) + 1}", condicoes, c, int(cobertos.sum()), p, len(regras) + 1)
                regras.append(r)
                if rastrear:
                    historico.append({"regra": r.id, "classe": c, "passos": passos})
            novo = restantes & ~cobertos
            if novo.sum() == restantes.sum():                  # sem progresso (segurança)
                break
            restantes = novo
    return ModeloPrism(regras, padrao, list(base.classes), base.classe, historico)


# ====================================================================== discretização
def cortes_frequencia_igual(valores, k):
    """k-1 pontos de corte por quantis (frequência igual), sem repetições."""
    xs = sorted(valores)
    n = len(xs)
    cortes = []
    for j in range(1, k):
        c = xs[min(n - 1, round(j * n / k))]
        # ponto médio entre vizinhos distintos, para o corte ficar entre valores observados
        i = xs.index(c)
        ant = xs[i - 1] if i > 0 else c
        corte = (ant + c) / 2 if ant != c else c
        if not cortes or corte > cortes[-1]:
            cortes.append(corte)
    return cortes


def faixa(valor, cortes):
    """Índice da faixa (0..len(cortes)) em que cai `valor`: faixa i = (cortes[i-1], cortes[i]]."""
    for i, c in enumerate(cortes):
        if valor <= c:
            return i
    return len(cortes)


def rotulo_faixa(i, cortes, nome_faixas=None, fmt=lambda x: f"{x:g}"):
    if nome_faixas and len(nome_faixas) == len(cortes) + 1:
        base = nome_faixas[i]
    else:
        base = f"F{i + 1}"
    if not cortes:
        return base
    if i == 0:
        return f"{base} (≤ {fmt(cortes[0])})"
    if i == len(cortes):
        return f"{base} (> {fmt(cortes[-1])})"
    return f"{base} ({fmt(cortes[i - 1])} < x ≤ {fmt(cortes[i])})"
