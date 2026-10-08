"""Questão 4 -- geração direta de regras (PRISM) no conjunto Pima Indians Diabetes.

Uso (na raiz do repositório):  python -m q4.executar [--dados data/diabetes.csv]
Usa a MESMA divisão treino/teste da Questão 3 (q3.dados.dividir).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import metrics as skm
from sklearn.model_selection import RepeatedStratifiedKFold

from ia import metricas as M
from ia.base import Base
from ia.prism import cortes_frequencia_igual, faixa, prism
from ia.relatorio import br
from q3 import dados as D
from q3.executar import bootstrap_ic, pct, tabela_md

AQUI = Path(__file__).parent
ROT = D.CLASSES
ROTULOS_CLASSE = [ROT[0], ROT[1]]
AUSENTE = "ausente"


# ====================================================================== discretização
class Discretizador:
    """Equal-frequency com k faixas por atributo (cortes aprendidos só no treino); NaN -> «ausente»."""

    def __init__(self, k):
        self.k = k
        self.cortes = {}

    def ajustar(self, df):
        for a in D.ATRIBUTOS:
            v = df[a].dropna().to_numpy()
            self.cortes[a] = cortes_frequencia_igual(list(v), self.k)
        return self

    def rotulo(self, a, valor):
        if pd.isna(valor):
            return AUSENTE
        return f"F{faixa(valor, self.cortes[a]) + 1}"

    def dominio(self, a, com_ausente):
        d = [f"F{i + 1}" for i in range(len(self.cortes[a]) + 1)]
        return d + [AUSENTE] if com_ausente else d

    def condicao_texto(self, a, rot, casas=1):
        """Traduz (atributo, 'F2') para «99,5 < Glicose ≤ 127,5»."""
        if rot == AUSENTE:
            return f"{a} ausente"
        i = int(rot[1:]) - 1
        c = self.cortes[a]
        f = lambda x: br(x, casas if abs(x - round(x)) > 1e-9 else 0)
        if not c:
            return f"{a} (qualquer valor)"
        if i == 0:
            return f"{a} ≤ {f(c[0])}"
        if i == len(c):
            return f"{a} > {f(c[-1])}"
        return f"{f(c[i - 1])} < {a} ≤ {f(c[i])}"

    def etiqueta(self, a, rot, casas=1):
        """Rótulo curto da faixa, p.ex. «≤ 105,5», «105,5 a 131,5», «> 131,5», «ausente»."""
        if rot == AUSENTE:
            return AUSENTE
        i = int(rot[1:]) - 1
        c = self.cortes[a]
        f = lambda x: br(x, casas if abs(x - round(x)) > 1e-9 else 0)
        if not c:
            return "qualquer valor"
        if i == 0:
            return f"≤ {f(c[0])}"
        if i == len(c):
            return f"> {f(c[-1])}"
        return f"{f(c[i - 1])} a {f(c[i])}"

    def intervalo(self, a, rot):
        if rot == AUSENTE:
            return None
        i = int(rot[1:]) - 1
        c = self.cortes[a]
        return (c[i - 1] if i > 0 else None, c[i] if i < len(c) else None)


def construir_base(df, disc, ausentes_para):
    linhas = []
    for idx, (_, r) in enumerate(df.iterrows(), 1):
        l = {"ID": f"P{idx}"}
        for a in D.ATRIBUTOS:
            l[a] = disc.rotulo(a, r[a])
        l["Resultado"] = ROT[int(r["Diabetes"])]
        linhas.append(l)
    doms = {a: disc.dominio(a, a in ausentes_para) for a in D.ATRIBUTOS}
    return Base(list(D.ATRIBUTOS), "Resultado", [ROT[0], ROT[1]], linhas, doms, "ID")


def codificar_exemplo(row, disc):
    return {a: disc.rotulo(a, row[a]) for a in D.ATRIBUTOS}


def avaliar(modelo, df, disc):
    y = df["Diabetes"].to_numpy()
    ex = [codificar_exemplo(r, disc) for _, r in df.iterrows()]
    prev = np.array([1 if modelo.prever(e) == ROT[1] else 0 for e in ex])
    esc = [modelo.escore(e, ROT[1]) for e in ex]
    m = M.metricas(y, prev, 1)
    m["auc"] = M.auc_roc(y, esc, 1)
    assert abs(m["f1"] - skm.f1_score(y, prev, zero_division=0)) < 1e-12
    assert abs(m["acuracia"] - skm.accuracy_score(y, prev)) < 1e-12
    assert abs(m["auc"] - skm.roc_auc_score(y, esc)) < 1e-9
    cobertos = np.mean([bool(modelo.regras_ativas(e)) for e in ex])
    m["cobertura_regras"] = float(cobertos)
    return m, prev, esc


def ajustar_prism(df_tr, k, **kw):
    disc = Discretizador(k).ajustar(df_tr)
    aus = {a for a in D.ATRIBUTOS if df_tr[a].isna().any()}
    base = construir_base(df_tr, disc, aus)
    return prism(base, **kw), disc, base


def contar_regras_teste(modelo, df_te, disc):
    ex = [codificar_exemplo(r, disc) for _, r in df_te.iterrows()]
    y = [ROT[int(v)] for v in df_te["Diabetes"]]
    for r in modelo.regras:
        r.n_teste = r.acertos_teste = 0
    for e, real in zip(ex, y):
        for r in modelo.regras:
            if r.cobre(e):
                r.n_teste += 1
                r.acertos_teste += int(real == r.classe)


def texto_regra(r, disc):
    c = " E ".join(disc.condicao_texto(a, v) for a, v in r.condicoes)
    return f"SE {c or 'VERDADEIRO'} ENTÃO Resultado = {r.classe}"


# ====================================================================== seleção de hiperparâmetros
GRADE = {"k": [3, 4, 5], "precisao_min": [1.0, 0.9, 0.8, 0.7], "cobertura_min": [1, 5, 10, 20], "max_condicoes": [None, 2, 3]}


def validar_config(df_tr, cfg, cv_split):
    y = df_tr["Diabetes"].to_numpy()
    f1s, n_regras = [], []
    for itr, ite in cv_split.split(df_tr, y):
        a, b = df_tr.iloc[itr], df_tr.iloc[ite]
        mod, disc, _ = ajustar_prism(a, cfg["k"], precisao_min=cfg["precisao_min"], cobertura_min=cfg["cobertura_min"],
                                     max_condicoes=cfg["max_condicoes"])
        ex = [codificar_exemplo(r, disc) for _, r in b.iterrows()]
        prev = np.array([1 if mod.prever(e) == ROT[1] else 0 for e in ex])
        f1s.append(M.metricas(b["Diabetes"].to_numpy(), prev, 1)["f1"])
        n_regras.append(len(mod.regras))
    return float(np.mean(f1s)), float(np.std(f1s)), float(np.mean(n_regras))


def kb_do_modelo(modelo, disc, nome):
    """Converte a base de regras PRISM em uma base de conhecimento do shell da Questão 5 (.kb)."""
    from sbc.modelo import BaseConhecimento, Condicao, Conclusao, Regra, Variavel
    kb = BaseConhecimento(nome=nome, metas=["Resultado"], estrategia="prioridade",
                          descricao="Regras geradas pelo PRISM (Questão 4) sobre o conjunto Pima. Material didático; "
                                    "não é ferramenta de diagnóstico.")
    for a in D.ATRIBUTOS:
        usados = [v for v in disc.dominio(a, True) if any(x == a and y == v for r in modelo.regras for x, y in r.condicoes)]
        kb.variaveis[a] = Variavel(a, valores=[disc.etiqueta(a, v) for v in usados],
                                   pergunta=f"{a} ({D.DESCRICAO[a]}): em que faixa está o valor? (ou «ausente» se não foi medido)",
                                   descricao=D.DESCRICAO[a])
    kb.variaveis["Resultado"] = Variavel("Resultado", valores=[ROT[0], ROT[1]], perguntavel=False)
    for r in modelo.regras:
        kb.regras.append(Regra(r.id, [Condicao(a, "=", disc.etiqueta(a, v)) for a, v in r.condicoes],
                               [Conclusao("Resultado", r.classe)], int(round(1000 * r.laplace)),
                               f"PRISM: cobre {r.n} exemplos de treino, {r.acertos} da classe {r.classe} "
                               f"(precisão {100 * r.precisao:.0f}%)."))
    return kb


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", default=None)
    ap.add_argument("--saida", default=str(AQUI / "resultados"))
    ap.add_argument("--relatorio", default=str(AQUI / "RELATORIO.md"))
    ap.add_argument("--q3", default=str(Path(__file__).parent.parent / "q3" / "resultados" / "metricas.json"),
                    help="metricas.json da Questão 3 (para a comparação)")
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    RES = Path(a.saida)
    RES.mkdir(parents=True, exist_ok=True)
    df = D.carregar(a.dados)
    tr, te = D.dividir(df)

    # ---------------- 1) PRISM clássico (pureza total) como no algoritmo original
    K_CLASSICO = 3
    mod_cl, disc_cl, base_cl = ajustar_prism(tr, K_CLASSICO, rastrear=True)
    contar_regras_teste(mod_cl, te, disc_cl)
    m_cl_tr, _, _ = avaliar(mod_cl, tr, disc_cl)
    m_cl_te, _, _ = avaliar(mod_cl, te, disc_cl)

    # ---------------- 2) seleção de variante regularizada por validação cruzada no treino
    grade = GRADE if not a.rapido else {"k": [3], "precisao_min": [1.0, 0.8], "cobertura_min": [1, 10], "max_condicoes": [None]}
    cv_split = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=D.SEMENTE)
    ncv = cv_split.get_n_splits()
    linhas = []
    for k, pm, cm, mc in itertools.product(grade["k"], grade["precisao_min"], grade["cobertura_min"], grade["max_condicoes"]):
        cfg = {"k": k, "precisao_min": pm, "cobertura_min": cm, "max_condicoes": mc}
        f1, sd, nr = validar_config(tr, cfg, cv_split)
        linhas.append({**cfg, "f1_cv": f1, "f1_dp": sd, "regras_medias": nr})
    tab = pd.DataFrame(linhas)
    tab.sort_values("f1_cv", ascending=False).to_csv(RES / "grade_prism.csv", index=False)
    i_melhor = int(tab["f1_cv"].idxmax())
    limite = tab.loc[i_melhor, "f1_cv"] - tab.loc[i_melhor, "f1_dp"] / math.sqrt(ncv)
    cand = tab[tab["f1_cv"] >= limite].sort_values(["regras_medias", "f1_cv"], ascending=[True, False])
    esc = cand.iloc[0]
    cfg_esc = {"k": int(esc["k"]), "precisao_min": float(esc["precisao_min"]), "cobertura_min": int(esc["cobertura_min"]),
               "max_condicoes": None if pd.isna(esc["max_condicoes"]) else int(esc["max_condicoes"])}
    mod, disc, base_tr = ajustar_prism(tr, cfg_esc["k"], precisao_min=cfg_esc["precisao_min"],
                                       cobertura_min=cfg_esc["cobertura_min"], max_condicoes=cfg_esc["max_condicoes"])
    contar_regras_teste(mod, te, disc)
    m_tr, _, _ = avaliar(mod, tr, disc)
    m_te, prev_te, esc_te = avaliar(mod, te, disc)
    ic_f1 = bootstrap_ic(te["Diabetes"].to_numpy(), prev_te, lambda y, p: M.metricas(y, p, 1)["f1"])

    # ---------------- 3) comparação com a árvore da Questão 3
    q3 = None
    if Path(a.q3).exists():
        q3 = json.loads(Path(a.q3).read_text(encoding="utf-8"))
    maioria = int(tr["Diabetes"].mode()[0])
    m_base = M.metricas(te["Diabetes"].to_numpy(), np.full(len(te), maioria), 1)

    # ---------------- arquivos
    def linhas_regras(modelo, d):
        out = []
        for r in modelo.regras:
            out.append(f"{r.id}: {texto_regra(r, d)}   [treino: {r.acertos}/{r.n}; teste: {r.acertos_teste}/{r.n_teste}]")
        return out
    (RES / "regras_prism_classico.txt").write_text("\n".join(linhas_regras(mod_cl, disc_cl)) + "\n", encoding="utf-8")
    (RES / "regras_prism.txt").write_text("\n".join(linhas_regras(mod, disc)) + "\n", encoding="utf-8")
    (RES / "regras_prism.json").write_text(json.dumps({
        "config": cfg_esc, "classe_padrao": mod.classe_padrao,
        "cortes": disc.cortes,
        "regras": [{"id": r.id, "condicoes": [[x, v, disc.condicao_texto(x, v)] for x, v in r.condicoes], "classe": r.classe,
                    "n": r.n, "acertos": r.acertos, "n_teste": r.n_teste, "acertos_teste": r.acertos_teste} for r in mod.regras]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    from sbc.parser import escrever_kb
    (RES / "diabetes_prism.kb").write_text(escrever_kb(kb_do_modelo(mod, disc, "Diabetes (regras PRISM, Questão 4)")),
                                           encoding="utf-8")
    saida = {"config": cfg_esc, "teste": m_te, "treino": m_tr, "classico_teste": m_cl_te, "classico_treino": m_cl_tr,
             "n_regras": len(mod.regras), "n_regras_classico": len(mod_cl.regras), "ic95_f1": ic_f1}
    (RES / "metricas.json").write_text(json.dumps(saida, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    # figuras
    fig, ax = plt.subplots(figsize=(6, 4))
    sc = ax.scatter(tab["regras_medias"], tab["f1_cv"], c=tab["cobertura_min"], cmap="viridis", s=40)
    ax.scatter([esc["regras_medias"]], [esc["f1_cv"]], s=160, facecolors="none", edgecolors="red", label="escolhida")
    ax.set_xlabel("nº médio de regras")
    ax.set_ylabel("F1 (validação cruzada, treino)")
    ax.set_title("PRISM: complexidade × desempenho")
    fig.colorbar(sc, label="cobertura mínima")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RES / "prism_complexidade.png", dpi=130)
    plt.close(fig)

    rel = montar_relatorio(df, tr, te, mod_cl, disc_cl, m_cl_tr, m_cl_te, K_CLASSICO, mod, disc, cfg_esc, tab, esc, limite,
                           m_tr, m_te, ic_f1, q3, m_base, maioria, ncv, base_cl)
    Path(a.relatorio).write_text(rel, encoding="utf-8")
    print(f"Q4 concluída em {time.time() - t0:.0f}s: PRISM clássico F1 teste = {m_cl_te['f1']:.3f} "
          f"({len(mod_cl.regras)} regras); escolhido F1 teste = {m_te['f1']:.3f} ({len(mod.regras)} regras)")
    return saida


# ====================================================================== relatório
def passo_a_passo(mod_cl, disc, base_cl, idx_regra=0, max_cand=6):
    """Mostra a construção de uma regra: tabela de candidatos p/t a cada passo."""
    h = mod_cl.historico[idx_regra]
    r = next(x for x in mod_cl.regras if x.id == h["regra"])
    L = [f"Construção da regra **{r.id}** (classe-alvo: **{r.classe}**):\n"]
    for i, p in enumerate(h["passos"], 1):
        tab = sorted(p["tabela"], key=lambda t: (-(t[2] / t[3]), -t[2]))[:max_cand]
        a, v = p["escolhida"]
        L.append(f"*Passo {i}* — exemplos cobertos até agora: {p['antes'][1]} ({p['antes'][0]} da classe-alvo). "
                 f"Melhores candidatos (p/t = positivos/cobertos):\n")
        L.append(tabela_md(["Condição candidata", "p", "t", "p/t"],
                           [[("**" if (x, y) == (a, v) else "") + disc.condicao_texto(x, y) + ("**" if (x, y) == (a, v) else ""),
                             pp, tt, pct(pp / tt)] for x, y, pp, tt in tab]))
        L.append(f"\n→ escolhida: **{disc.condicao_texto(a, v)}**\n")
    L.append(f"Regra final: `{texto_regra(r, disc)}` — cobre {r.n} exemplos de treino, {r.acertos} da classe "
             f"{r.classe} (precisão {pct(r.precisao, 0)}).\n")
    return "\n".join(L)


def montar_relatorio(df, tr, te, mod_cl, disc_cl, m_cl_tr, m_cl_te, k_cl, mod, disc, cfg, tab, esc, limite, m_tr, m_te,
                     ic_f1, q3, m_base, maioria, ncv, base_cl):
    L = []
    w = L.append
    w("# Questão 4 — Geração direta de regras com PRISM (conjunto *Pima Indians Diabetes*)\n")
    w("> Relatório gerado por `python -m q4.executar`. Usa a **mesma divisão treino/teste** da Questão 3 "
      f"({len(tr)} treino / {len(te)} teste).\n")
    w("## 1. O algoritmo PRISM\n")
    w("PRISM (Cendrowska, 1987) é um algoritmo de **cobertura sequencial** (*separar e conquistar*): em vez de construir "
      "uma árvore e depois extrair regras (Questões 1–3), ele aprende as regras **diretamente**, uma classe por vez:\n")
    w("```text\nPara cada classe c:\n  E ← todos os exemplos de treino\n  Enquanto E contiver exemplos de c:\n"
      "    R ← regra sem condições;  C ← E\n    Enquanto C contiver exemplos que não são de c (e ainda houver atributos):\n"
      "      para cada par (atributo = valor) não usado, calcule p/t sobre C  (p = exemplos de c, t = cobertos)\n"
      "      acrescente a R o par de maior p/t (empate: maior p);  C ← exemplos de C que o satisfazem\n"
      "    emita R;  E ← E − exemplos cobertos por R\n```\n")
    w("Diferenças em relação às árvores: PRISM maximiza a **precisão da regra** (p/t) em vez de ganho de informação, "
      "gera regras que **não** precisam formar uma partição (podem se sobrepor) e exige atributos **categóricos**. "
      "Implementação própria em `ia/prism.py` (sem biblioteca), testada em `tests/test_prism.py`.\n")
    w("## 2. Preparação dos dados\n")
    w("* Os 8 atributos são numéricos; PRISM exige categóricos, então foram **discretizados por frequência igual** (quantis), "
      "com cortes aprendidos **somente no treino** (e, na validação cruzada, somente nas dobras de treino).")
    w("* Valores ausentes (zeros impossíveis, ver Q3) viram uma categoria própria **“ausente”** (“não medido”) — "
      "em vez de imputar —, o que deixa o algoritmo usar a própria ausência como informação (p.ex. insulina não medida).")
    w(f"* Escolhas por validação cruzada: número de faixas k ∈ {{3,4,5}}.\n")
    w("## 3. PRISM clássico (puro) — passo a passo\n")
    w(f"Configuração do algoritmo original: k = {k_cl} faixas, regras só terminam quando 100% puras, sem cobertura mínima.\n")
    w(passo_a_passo(mod_cl, disc_cl, base_cl, 0))
    w("")
    n_cl = len(mod_cl.regras)
    ex_ruido = sum(1 for r in mod_cl.regras if r.n <= 2)
    w(f"O PRISM clássico produziu **{n_cl} regras** ({br(sum(len(r.condicoes) for r in mod_cl.regras) / n_cl, 1)} condições em "
      f"média); {ex_ruido} delas cobrem 2 exemplos ou menos. Como o conjunto é ruidoso (as classes se sobrepõem), exigir "
      f"pureza total força regras muito específicas que decoram o treino:\n")
    w(tabela_md(["Conjunto", "Acurácia", "Precisão", "Recall", "F1", "AUC", "Cobertura das regras"],
                [["Treino", pct(m_cl_tr["acuracia"]), pct(m_cl_tr["precisao"]), pct(m_cl_tr["recall"]), pct(m_cl_tr["f1"]),
                  br(m_cl_tr["auc"], 3), pct(m_cl_tr["cobertura_regras"])],
                 ["**Teste**", pct(m_cl_te["acuracia"]), pct(m_cl_te["precisao"]), pct(m_cl_te["recall"]), pct(m_cl_te["f1"]),
                  br(m_cl_te["auc"], 3), pct(m_cl_te["cobertura_regras"])]]))
    w("")
    w(f"A diferença treino × teste ({pct(m_cl_tr['acuracia'])} → {pct(m_cl_te['acuracia'])} de acurácia) é o "
      f"*sobreajuste* típico de PRISM puro em dados ruidosos. (Lista completa: `resultados/regras_prism_classico.txt`.)\n")
    w("## 4. PRISM regularizado (escolhido por validação cruzada)\n")
    w("Duas extensões padrão, que continuam sendo PRISM, mas toleram ruído:\n")
    w("* **precisão mínima** — a regra pode parar antes da pureza total quando p/t ≥ limiar;")
    w("* **cobertura mínima** — regras que cobrem poucos exemplos da classe são descartadas;")
    w("* **máximo de condições** — regras curtas.\n")
    w(f"Grade: k ∈ {{3,4,5}} × precisão mínima ∈ {{1; 0,9; 0,8; 0,7}} × cobertura mínima ∈ {{1,5,10,20}} × máx. condições ∈ "
      f"{{sem limite, 2, 3}} = {len(tab)} configurações, avaliadas por validação cruzada estratificada repetida no treino "
      f"(5×2 = {ncv} ajustes), pontuando F1 da classe Diabetes. **Escolha** pela regra do 1 desvio-padrão (como na Q3): "
      f"entre as de F1 médio ≥ {br(limite, 3)}, a de menos regras.\n")
    w(f"Escolhida: k = **{cfg['k']}** faixas, precisão mínima = **{br(cfg['precisao_min'], 2)}**, cobertura mínima = "
      f"**{cfg['cobertura_min']}**, máx. condições = **{cfg['max_condicoes'] or 'sem limite'}** "
      f"(F1 em validação: {pct(esc['f1_cv'])} ± {pct(esc['f1_dp'])}, {br(esc['regras_medias'], 1)} regras em média por dobra).\n")
    w("![complexidade](resultados/prism_complexidade.png)\n")
    w("### 4.1 Base de regras\n")
    w("Classificação: entre as regras que cobrem o exemplo, vale a de **maior precisão de Laplace** "
      "(acertos+1)/(cobertos+2), desempate pela maior cobertura; se nenhuma cobre, usa-se a classe majoritária do treino "
      f"(**{mod.classe_padrao}**). Condições escritas como intervalos dos atributos originais.\n")
    rows = []
    ordem = sorted(mod.regras, key=lambda r: (r.classe != ROT[1], -r.laplace, -r.n))
    LIMITE = 40
    if len(ordem) > LIMITE:
        w(f"São muitas regras; abaixo, as {LIMITE} de maior precisão de Laplace (as de “{ROT[1]}” primeiro). "
          f"A lista completa está em `resultados/regras_prism.txt`.\n")
        ordem = ordem[:LIMITE]
    for r in ordem:
        rows.append([r.id, texto_regra(r, disc), f"{r.acertos}/{r.n}", pct(r.precisao, 0),
                     f"{r.acertos_teste}/{r.n_teste}", pct(r.acertos_teste / r.n_teste, 0) if r.n_teste else "—"])
    w(tabela_md(["Id", "Regra", "Treino (acertos/cobertos)", "Prec. treino", "Teste (acertos/cobertos)", "Prec. teste"], rows))
    w("")
    w(f"Total: **{len(mod.regras)} regras**; média de {br(sum(len(r.condicoes) for r in mod.regras) / len(mod.regras), 1)} "
      f"condições por regra. A base também foi exportada como base de conhecimento do shell da Questão 5 "
      f"(`q4/resultados/diabetes_prism.kb`: `python -m sbc q4/resultados/diabetes_prism.kb`).\n")
    w("## 5. Desempenho (conjunto de teste)\n")
    cab = ["Modelo", "Regras", "Acurácia", "Precisão", "Recall", "F1", "AUC"]

    def lin(nome, nreg, m):
        return [nome, nreg, pct(m["acuracia"]), pct(m["precisao"]), pct(m["recall"]), pct(m["f1"]),
                br(m["auc"], 3) if m.get("auc") is not None else "—"]
    tabela = [lin("**PRISM regularizado**", len(mod.regras), m_te), lin("PRISM clássico (puro)", len(mod_cl.regras), m_cl_te)]
    if q3:
        tabela.append(lin("Árvore de decisão (Questão 3)", q3["folhas"], q3["teste"]))
    tabela.append(lin(f"Baseline: sempre {ROT[maioria]}", 1, {**m_base, "auc": 0.5}))
    w(tabela_md(cab, tabela))
    w("")
    w(f"IC 95% (bootstrap) do F1 do PRISM regularizado: [{pct(ic_f1[0])}; {pct(ic_f1[1])}].\n")
    cm = [["**Real: " + ROT[0] + "**", m_te["VN"], m_te["FP"]], ["**Real: " + ROT[1] + "**", m_te["FN"], m_te["VP"]]]
    w("Matriz de confusão do PRISM regularizado (teste):\n")
    w(tabela_md(["", "Previsto: " + ROT[0], "Previsto: " + ROT[1]], cm))
    w("")
    w(f"As regras cobrem {pct(m_te['cobertura_regras'])} dos exemplos de teste; os demais recebem a classe padrão.\n")
    w("## 6. Discussão\n")
    if q3:
        d_f1 = m_te["f1"] - q3["teste"]["f1"]
        w(f"* **PRISM × árvore (Q3):** F1 de teste {pct(m_te['f1'])} contra {pct(q3['teste']['f1'])} "
          f"({'+' if d_f1 >= 0 else ''}{br(100 * d_f1, 1)} p.p.), com {len(mod.regras)} regras contra {q3['folhas']} regras (folhas) "
          f"da árvore. Com o teste tão pequeno, essa diferença deve ser lida junto dos intervalos de confiança — "
          f"diferenças de poucos pontos não são conclusivas.")
    w(f"* **Pureza × generalização:** o PRISM puro chegou a {pct(m_cl_tr['acuracia'])} de acurácia no treino e "
      f"{pct(m_cl_te['acuracia'])} no teste; a versão regularizada caiu para {pct(m_tr['acuracia'])} no treino e "
      f"{'subiu' if m_te['acuracia'] > m_cl_te['acuracia'] else 'ficou em'} {pct(m_te['acuracia'])} no teste, com "
      f"{len(mod_cl.regras) - len(mod.regras)} regras a menos: aceitar regras “impuras” é o que torna a base útil.")
    w("* **Regras sobrepostas:** diferentemente da árvore (partição do espaço), regras do PRISM podem cobrir o mesmo exemplo; "
      "por isso é preciso uma política de resolução de conflitos (aqui, a precisão de Laplace).")
    w("* **Discretização importa:** os cortes por quantis não coincidem com os limiares ótimos que a árvore encontra; "
      "a árvore escolhe limiares por ganho de informação, enquanto aqui as faixas são fixadas antes de aprender as regras.")
    w("* **Interpretação:** regras como as acima são auditáveis, mas descrevem associações estatísticas nesta amostra, "
      "não causas; não há uso diagnóstico.\n")
    w("## 7. Reprodutibilidade\n")
    w("```bash\npython -m q3.executar   # gera q3/resultados/divisao.json e metricas.json (para a comparação)\n"
      "python -m q4.executar\n```")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
