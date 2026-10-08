"""Questão 3 -- árvore de decisão e regras para o conjunto Pima Indians Diabetes (Kaggle).

Uso (na raiz do repositório):
    python -m q3.executar                      # lê data/diabetes.csv
    python -m q3.executar --dados caminho.csv --saida pasta_de_saida
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn import metrics as skm
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from ia import metricas as M
from ia.regras_num import regras_de_arvore_numerica
from ia.relatorio import br

from . import dados as D

AQUI = Path(__file__).parent
POS = 1
ROT = D.CLASSES


def pct(x, nd=1):
    return f"{100 * x:.{nd}f}".replace(".", ",") + "%"


def pipeline(**kw):
    return Pipeline([("imputar", SimpleImputer(strategy="median")),
                     ("arvore", DecisionTreeClassifier(random_state=0, **kw))])


GRADE = {
    "arvore__criterion": ["gini", "entropy"],
    "arvore__max_depth": [2, 3, 4, 5, 6, 8, None],
    "arvore__min_samples_leaf": [1, 5, 10, 20],
    "arvore__ccp_alpha": [0.0, 0.002, 0.005, 0.01],
    "arvore__class_weight": [None, "balanced"],
}
PONTUACOES = {"f1": "f1", "acuracia": "accuracy", "precisao": "precision", "recall": "recall", "auc": "roc_auc"}


def escolher_pela_regra_do_1_desvio(cv, Xtr, ytr, k):
    """Entre as configurações com F1 médio >= (melhor - erro-padrão), a de menos folhas (desempate: maior F1)."""
    res = pd.DataFrame(cv.cv_results_)
    i_melhor = int(res["mean_test_f1"].idxmax())
    limite = res.loc[i_melhor, "mean_test_f1"] - res.loc[i_melhor, "std_test_f1"] / math.sqrt(k)
    cand = res[res["mean_test_f1"] >= limite].copy()
    folhas = []
    for p in cand["params"]:
        m = pipeline(**{k_.split("__")[1]: v for k_, v in p.items()}).fit(Xtr, ytr)
        folhas.append(m.named_steps["arvore"].get_n_leaves())
    cand["folhas"] = folhas
    cand = cand.sort_values(["folhas", "mean_test_f1"], ascending=[True, False])
    return int(cand.index[0]), i_melhor, float(limite), res


def bootstrap_ic(y, p, funcao, n=1000, semente=7):
    rng = np.random.default_rng(semente)
    y, p = np.asarray(y), np.asarray(p)
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        vals.append(funcao(y[i], p[i]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def tabela_md(cab, linhas, alinhar=None):
    alinhar = alinhar or ["---"] * len(cab)
    t = ["| " + " | ".join(cab) + " |", "| " + " | ".join(alinhar) + " |"]
    t += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(t)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", default=None, help="caminho do diabetes.csv (padrão: data/diabetes.csv)")
    ap.add_argument("--saida", default=str(AQUI / "resultados"))
    ap.add_argument("--relatorio", default=str(AQUI / "RELATORIO.md"))
    ap.add_argument("--rapido", action="store_true", help="grade reduzida (só para testes)")
    a = ap.parse_args(argv)
    t0 = time.time()
    RES = Path(a.saida)
    RES.mkdir(parents=True, exist_ok=True)

    df = D.carregar(a.dados)
    tr, te = D.dividir(df)
    Xtr, ytr = tr[D.ATRIBUTOS].to_numpy(), tr["Diabetes"].to_numpy()
    Xte, yte = te[D.ATRIBUTOS].to_numpy(), te["Diabetes"].to_numpy()
    (RES / "divisao.json").write_text(json.dumps(
        {"semente": D.SEMENTE, "fracao_teste": D.FRACAO_TESTE, "treino": [int(i) for i in tr.index],
         "teste": [int(i) for i in te.index]}), encoding="utf-8")

    # ---------------------------------------------------------------- busca de hiperparâmetros
    grade = dict(GRADE)
    if a.rapido:
        grade = {"arvore__criterion": ["gini"], "arvore__max_depth": [3, 5], "arvore__min_samples_leaf": [5],
                 "arvore__ccp_alpha": [0.0], "arvore__class_weight": [None]}
    cv_split = RepeatedStratifiedKFold(n_splits=5, n_repeats=4, random_state=D.SEMENTE)
    k_dobras = cv_split.get_n_splits()
    busca = GridSearchCV(pipeline(), grade, scoring=PONTUACOES, refit=False, cv=cv_split, n_jobs=1)
    busca.fit(Xtr, ytr)
    i_esc, i_melhor, limite, res = escolher_pela_regra_do_1_desvio(busca, Xtr, ytr, k_dobras)
    params_esc = {k.split("__")[1]: v for k, v in res.loc[i_esc, "params"].items()}
    params_melhor = {k.split("__")[1]: v for k, v in res.loc[i_melhor, "params"].items()}
    res_ord = res.sort_values("mean_test_f1", ascending=False).head(15)
    res_ord.assign(params=res_ord["params"].astype(str))[
        ["params", "mean_test_f1", "std_test_f1", "mean_test_acuracia", "mean_test_precisao", "mean_test_recall",
         "mean_test_auc"]].to_csv(RES / "grade_top15.csv", index=False)

    # ---------------------------------------------------------------- modelos finais e comparações
    padrao = pipeline().fit(Xtr, ytr)                            # árvore sem controle (ponto de partida)
    final = pipeline(**params_esc).fit(Xtr, ytr)
    melhor_media = pipeline(**params_melhor).fit(Xtr, ytr)
    maioria = int(pd.Series(ytr).mode()[0])

    def avaliar(modelo, X, y):
        prev = modelo.predict(X)
        prob = modelo.predict_proba(X)[:, 1]
        m = M.metricas(y, prev, POS)
        m["auc"] = M.auc_roc(y, prob, POS)
        # conferência cruzada com scikit-learn
        assert abs(m["acuracia"] - skm.accuracy_score(y, prev)) < 1e-12
        assert abs(m["f1"] - skm.f1_score(y, prev, zero_division=0)) < 1e-12
        assert abs(m["precisao"] - skm.precision_score(y, prev, zero_division=0)) < 1e-12
        assert abs(m["recall"] - skm.recall_score(y, prev, zero_division=0)) < 1e-12
        assert abs(m["auc"] - skm.roc_auc_score(y, prob)) < 1e-9
        return m, prev, prob

    m_te, prev_te, prob_te = avaliar(final, Xte, yte)
    m_tr, _, _ = avaliar(final, Xtr, ytr)
    m_pad_te, _, _ = avaliar(padrao, Xte, yte)
    m_mm_te, _, _ = avaliar(melhor_media, Xte, yte)
    base_prev = np.full_like(yte, maioria)
    m_base = M.metricas(yte, base_prev, POS)
    m_base["auc"] = 0.5
    ic_f1 = bootstrap_ic(yte, prev_te, lambda y, p: M.metricas(y, p, POS)["f1"])
    ic_acc = bootstrap_ic(yte, prev_te, lambda y, p: M.metricas(y, p, POS)["acuracia"])
    cvf = cross_validate(pipeline(**params_esc), Xtr, ytr, cv=cv_split, scoring=PONTUACOES)
    cv_final = {k: (float(np.mean(cvf["test_" + k])), float(np.std(cvf["test_" + k]))) for k in PONTUACOES}

    arv = final.named_steps["arvore"]
    imp = final.named_steps["imputar"]
    Xtr_i, Xte_i = imp.transform(Xtr), imp.transform(Xte)
    regras = regras_de_arvore_numerica(arv, D.ATRIBUTOS, Xtr_i, ytr, Xte_i, yte)
    importancias = sorted(zip(D.ATRIBUTOS, arv.feature_importances_), key=lambda t: -t[1])

    # curva de complexidade (profundidade)
    prof = list(range(1, 11))
    cur_cv, cur_tr = [], []
    base_kw = {k: v for k, v in params_esc.items() if k != "max_depth"}
    for d in prof:
        r = cross_validate(pipeline(max_depth=d, **base_kw), Xtr, ytr, cv=cv_split, scoring="f1", return_train_score=True)
        cur_cv.append(float(np.mean(r["test_score"])))
        cur_tr.append(float(np.mean(r["train_score"])))

    # ---------------------------------------------------------------- arquivos
    (RES / "arvore.txt").write_text(export_text(arv, feature_names=D.ATRIBUTOS, class_names=[ROT[c] for c in arv.classes_]),
                                    encoding="utf-8")
    linhas_regras = [f"{r.id}: {r.texto('Resultado', lambda c: ROT[int(c)])}   "
                     f"[treino: {r.acertos}/{r.n}; teste: {r.acertos_teste}/{r.n_teste}]" for r in regras]
    (RES / "regras.txt").write_text("\n".join(linhas_regras) + "\n", encoding="utf-8")
    (RES / "regras.json").write_text(json.dumps({"atributos": D.ATRIBUTOS, "classe_padrao": int(maioria),
                                                 "regras": [r.para_dict() for r in regras]},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
    saida_metricas = {"hiperparametros": {k: (None if v is None else v) for k, v in params_esc.items()},
                      "hiperparametros_melhor_media_cv": params_melhor,
                      "teste": m_te, "treino": m_tr, "teste_arvore_sem_controle": m_pad_te,
                      "teste_melhor_media_cv": m_mm_te, "teste_baseline_maioria": m_base,
                      "cv_treino": cv_final, "ic95_teste": {"f1": ic_f1, "acuracia": ic_acc},
                      "folhas": int(arv.get_n_leaves()), "profundidade": int(arv.get_depth()),
                      "importancias": importancias, "versao_sklearn": sklearn.__version__}
    (RES / "metricas.json").write_text(json.dumps(saida_metricas, ensure_ascii=False, indent=2, default=float),
                                       encoding="utf-8")

    # figuras
    fig, ax = plt.subplots(figsize=(max(10, 2.2 * arv.get_n_leaves()), 6 + arv.get_depth()))
    plot_tree(arv, feature_names=D.ATRIBUTOS, class_names=[ROT[c] for c in arv.classes_], filled=True, rounded=True,
              impurity=False, proportion=False, fontsize=8, ax=ax)
    fig.tight_layout()
    fig.savefig(RES / "arvore.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.4, 4))
    cm = np.array([[m_te["VN"], m_te["FP"]], [m_te["FN"], m_te["VP"]]])
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=16,
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xticks([0, 1], [ROT[0], ROT[1]])
    ax.set_yticks([0, 1], [ROT[0], ROT[1]])
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusão (teste)")
    fig.tight_layout()
    fig.savefig(RES / "matriz_confusao.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.barh([n for n, _ in importancias][::-1], [v for _, v in importancias][::-1], color="#3b6ea5")
    ax.set_xlabel("Importância (redução total de impureza)")
    ax.set_title("Importância dos atributos")
    fig.tight_layout()
    fig.savefig(RES / "importancias.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 3.8))
    ax.plot(prof, cur_tr, "o-", label="treino (F1)")
    ax.plot(prof, cur_cv, "s-", label="validação cruzada (F1)")
    ax.set_xlabel("Profundidade máxima")
    ax.set_ylabel("F1 (classe Diabetes)")
    ax.set_title("Curva de complexidade")
    ax.legend()
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(RES / "curva_complexidade.png", dpi=130)
    plt.close(fig)

    fp = RES / "curva_roc.png"
    fpr, tpr, _ = skm.roc_curve(yte, prob_te)
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.plot(fpr, tpr, label=f"árvore (AUC = {br(m_te['auc'], 3)})")
    ax.plot([0, 1], [0, 1], "k--", lw=.8, label="acaso")
    ax.set_xlabel("Taxa de falsos positivos")
    ax.set_ylabel("Sensibilidade (recall)")
    ax.legend()
    ax.set_title("Curva ROC (teste)")
    fig.tight_layout()
    fig.savefig(fp, dpi=130)
    plt.close(fig)

    relatorio = montar_relatorio(df, tr, te, params_esc, params_melhor, limite, res, i_esc, i_melhor, m_te, m_tr, m_pad_te,
                                 m_mm_te, m_base, ic_f1, ic_acc, cv_final, arv, regras, importancias, cur_cv, prof,
                                 maioria, k_dobras, a)
    Path(a.relatorio).write_text(relatorio, encoding="utf-8")
    print(f"Q3 concluída em {time.time() - t0:.0f}s: F1 teste = {m_te['f1']:.3f}, acurácia = {m_te['acuracia']:.3f}")
    return saida_metricas


# ====================================================================== relatório
def desc_params(p):
    nomes = {"criterion": "critério", "max_depth": "profundidade máxima", "min_samples_leaf": "mín. exemplos por folha",
             "ccp_alpha": "ccp_alpha (poda)", "class_weight": "class_weight"}
    return "; ".join(f"{nomes[k]} = {v}" for k, v in p.items())


def montar_relatorio(df, tr, te, p_esc, p_melhor, limite, res, i_esc, i_melhor, m_te, m_tr, m_pad, m_mm, m_base, ic_f1,
                     ic_acc, cv_final, arv, regras, imp, cur_cv, prof, maioria, k_dobras, args):
    n, npos = len(df), int(df["Diabetes"].sum())
    L = []
    w = L.append
    w("# Questão 3 — Árvore de decisão e regras no conjunto *Pima Indians Diabetes*\n")
    w("> Relatório gerado por `python -m q3.executar` (todos os números abaixo vêm da execução; nada foi digitado à mão).\n")
    w("## 1. Conjunto de dados\n")
    w(f"* **Fonte:** Kaggle — *Pima Indians Diabetes Database* (`uciml/pima-indians-diabetes-database`), originado do "
      f"National Institute of Diabetes and Digestive and Kidney Diseases. Mulheres com pelo menos 21 anos, de ascendência "
      f"Pima.\n* **Tamanho:** {n} exemplos, 8 atributos numéricos e a classe `Outcome` (1 = diagnóstico positivo "
      f"de diabetes; 0 = negativo).\n* **Distribuição da classe:** {n - npos} sem diabetes ({pct((n - npos) / n)}) e {npos} com "
      f"diabetes ({pct(npos / n)}) — conjunto **desbalanceado**; por isso acurácia sozinha engana (um classificador que "
      f"sempre responde “{ROT[maioria]}” já acerta {pct(m_base['acuracia'])} no teste).\n")
    linhas = []
    for c in D.ATRIBUTOS:
        s = df[c]
        linhas.append([c, D.DESCRICAO[c], br(s.min(), 1), br(s.median(), 1), br(s.mean(), 1), br(s.max(), 1),
                       int(s.isna().sum())])
    w(tabela_md(["Atributo", "Descrição", "mín.", "mediana", "média", "máx.", "ausentes"], linhas))
    w("")
    w("## 2. Pré-processamento\n")
    aus = D.resumo_ausentes(df)
    w("* No arquivo original, valores ausentes foram codificados como **0** em atributos onde zero é fisiologicamente "
      "impossível (glicose, pressão, dobra do tríceps, insulina, IMC). Esses zeros foram tratados como **ausentes**: "
      + ", ".join(f"{k}: {v} ({pct(v / n)})" for k, v in aus.items()) + ".")
    w("* Os ausentes são preenchidos com a **mediana do treino** (`SimpleImputer`), dentro do *pipeline*; assim a mediana é "
      "calculada só com dados de treino em cada dobra da validação cruzada (sem vazamento de informação do teste).")
    w(f"* **Divisão treino/teste:** estratificada, {pct(1 - D.FRACAO_TESTE, 0)} / {pct(D.FRACAO_TESTE, 0)} "
      f"(`random_state = {D.SEMENTE}`): {len(tr)} exemplos de treino ({pct(tr['Diabetes'].mean())} positivos) e {len(te)} de teste "
      f"({pct(te['Diabetes'].mean())} positivos). O teste só é usado **uma vez**, no final. As mesmas partições são usadas na "
      f"Questão 4 (índices em `q3/resultados/divisao.json`).\n")
    w("## 3. Método\n")
    w("* Algoritmo: `DecisionTreeClassifier` do scikit-learn " + sklearn.__version__ + " (CART: divisões binárias "
      "`atributo ≤ limiar`, critério Gini ou entropia).")
    w(f"* **Ajuste de hiperparâmetros** só no treino, por busca em grade com validação cruzada estratificada repetida "
      f"(5 dobras × 4 repetições = {k_dobras} ajustes por configuração), pontuando o **F1 da classe Diabetes**. Grade: "
      f"critério {{gini, entropy}} × profundidade {{2,3,4,5,6,8,sem limite}} × mín. exemplos por folha {{1,5,10,20}} × "
      f"`ccp_alpha` {{0; 0,002; 0,005; 0,01}} × `class_weight` {{nenhum, balanced}} = {len(res)} configurações.")
    w(f"* **Escolha:** regra do 1 desvio-padrão — entre as configurações com F1 médio ≥ {br(limite, 3)} "
      f"(melhor média menos um erro-padrão), escolhe-se a de **menos folhas**, privilegiando a interpretabilidade que a "
      f"questão pede (regras curtas).")
    w("* **Métricas** (classe positiva = Diabetes): acurácia = (VP+VN)/n; precisão = VP/(VP+FP); recall = VP/(VP+FN); "
      "F1 = 2·precisão·recall/(precisão+recall); AUC-ROC. Implementadas em `ia/metricas.py` e conferidas, a cada execução, "
      "com `sklearn.metrics`.\n")
    w("## 4. Resultados\n")
    w(f"Configuração escolhida: **{desc_params(p_esc)}**. A de maior F1 médio na validação era: {desc_params(p_melhor)} "
      f"(no teste: F1 = {pct(m_mm['f1'])}; ver `metricas.json`).\n")
    cab = ["Modelo", "Acurácia", "Precisão", "Recall", "F1", "AUC"]

    def lin(nome, m):
        return [nome, pct(m["acuracia"]), pct(m["precisao"]), pct(m["recall"]), pct(m["f1"]),
                br(m["auc"], 3) if m.get("auc") is not None else "—"]
    w("### 4.1 Desempenho no conjunto de **teste**\n")
    w(tabela_md(cab, [lin("**Árvore escolhida**", m_te), lin("Árvore sem controle (padrão do sklearn)", m_pad),
                      lin("Árvore de maior F1 médio na validação", m_mm), lin("Baseline: sempre " + ROT[maioria], m_base)]))
    w("")
    w(f"Intervalos de confiança de 95% (bootstrap, 1000 reamostragens do teste): "
      f"F1 ∈ [{pct(ic_f1[0])}; {pct(ic_f1[1])}], acurácia ∈ [{pct(ic_acc[0])}; {pct(ic_acc[1])}]. "
      f"Com apenas {len(te)} exemplos de teste, diferenças de poucos pontos percentuais entre modelos **não são "
      f"estatisticamente distinguíveis**.\n")
    w("### 4.2 Estimativa por validação cruzada no treino (média ± desvio)\n")
    w(tabela_md(["Acurácia", "Precisão", "Recall", "F1", "AUC"],
                [[f"{pct(cv_final[k][0])} ± {pct(cv_final[k][1])}" if k != "auc" else f"{br(cv_final[k][0], 3)} ± {br(cv_final[k][1], 3)}"
                  for k in ("acuracia", "precisao", "recall", "f1", "auc")]]))
    w("")
    w(f"No treino a árvore escolhida atinge acurácia {pct(m_tr['acuracia'])} e F1 {pct(m_tr['f1'])}; o desempenho em "
      f"validação e teste é menor, como esperado (gap de generalização).\n")
    w("### 4.3 Matriz de confusão (teste)\n")
    w(tabela_md(["", "Previsto: " + ROT[0], "Previsto: " + ROT[1]],
                [["**Real: " + ROT[0] + "**", m_te["VN"], m_te["FP"]], ["**Real: " + ROT[1] + "**", m_te["FN"], m_te["VP"]]]))
    w("")
    w("![matriz de confusão](resultados/matriz_confusao.png) ![curva ROC](resultados/curva_roc.png)\n")
    w(f"Em linguagem de triagem: dos {m_te['VP'] + m_te['FN']} casos de diabetes do teste, {m_te['VP']} foram detectados "
      f"(recall {pct(m_te['recall'])}) e {m_te['FN']} escaparam; dos {m_te['VP'] + m_te['FP']} alertas emitidos, {m_te['VP']} "
      f"estavam corretos (precisão {pct(m_te['precisao'])}). Especificidade: {pct(m_te['especificidade'])}.\n")
    w("## 5. A árvore\n")
    w(f"Profundidade {arv.get_depth()}, {arv.get_n_leaves()} folhas.\n")
    w("![árvore](resultados/arvore.png)\n")
    w("Versão em texto (`resultados/arvore.txt`):\n")
    w("```text\n" + export_text(arv, feature_names=D.ATRIBUTOS, class_names=[ROT[c] for c in arv.classes_]).rstrip() + "\n```\n")
    w("### Importância dos atributos\n")
    w(tabela_md(["Atributo", "Importância"], [[a, pct(v)] for a, v in imp if v > 0]))
    w("")
    w("![importâncias](resultados/importancias.png) ![curva de complexidade](resultados/curva_complexidade.png)\n")
    w("## 6. Base de regras SE … ENTÃO\n")
    w("Uma regra por folha (caminho da raiz até a folha, com condições repetidas sobre o mesmo atributo fundidas em um "
      "intervalo). As regras são **mutuamente exclusivas e exaustivas**: todo exemplo é coberto por exatamente uma.\n")
    linhas = []
    for r in regras:
        linhas.append([r.id, r.texto("Resultado", lambda c: ROT[int(c)]), f"{r.acertos}/{r.n}", pct(r.precisao, 0),
                       f"{r.acertos_teste}/{r.n_teste}",
                       pct(r.precisao_teste, 0) if r.n_teste else "—"])
    w(tabela_md(["Id", "Regra", "Treino (acertos/cobertos)", "Prec. treino", "Teste (acertos/cobertos)", "Prec. teste"], linhas))
    w("")
    pos = [r for r in regras if int(r.classe) == POS]
    neg = [r for r in regras if int(r.classe) != POS]
    w(f"São {len(regras)} regras: {len(pos)} concluem “{ROT[1]}” e {len(neg)} concluem “{ROT[0]}”. "
      f"Média de {br(sum(len(r.intervalos) for r in regras) / len(regras), 1)} condições por regra.\n")
    w("## 7. Discussão\n")
    top = [a for a, v in imp if v > 0][:3]
    w(f"* **Atributos mais usados:** {', '.join(top)} {'concentra' if len(top) == 1 else 'concentram'} "
      f"{pct(sum(v for a, v in imp if a in top))} da importância total. A raiz da árvore divide por **{D.ATRIBUTOS[arv.tree_.feature[0]]} ≤ {br(arv.tree_.threshold[0], 1)}**.")
    ganho = m_te["acuracia"] - m_base["acuracia"]
    if ganho >= 0:
        w(f"* **Ganho sobre o baseline:** acurácia +{br(100 * ganho, 1)} p.p. sobre “sempre {ROT[maioria]}”, e F1 de "
          f"{pct(m_te['f1'])} contra {pct(m_base['f1'])} (o baseline não detecta nenhum caso positivo).")
    else:
        w(f"* **Acurácia × detecção:** a acurácia ({pct(m_te['acuracia'])}) fica {br(-100 * ganho, 1)} p.p. *abaixo* de “sempre "
          f"{ROT[maioria]}” ({pct(m_base['acuracia'])}) — o modelo troca acurácia por detecção: o F1 é {pct(m_te['f1'])} "
          f"contra {pct(m_base['f1'])} do baseline, que nunca encontra um caso positivo. Qual é melhor depende do custo "
          f"relativo de um falso alarme e de um caso perdido.")
    if m_te["recall"] > m_te["precisao"] + 0.03:
        w(f"* **Tipo de erro:** o modelo é mais sensível que preciso (recall {pct(m_te['recall'])} > precisão "
          f"{pct(m_te['precisao'])}): prefere alertar a deixar passar — compatível com triagem, ao custo de falsos alarmes.")
    elif m_te["precisao"] > m_te["recall"] + 0.03:
        w(f"* **Tipo de erro:** o modelo é mais preciso que sensível (precisão {pct(m_te['precisao'])} > recall "
          f"{pct(m_te['recall'])}): quando alerta costuma acertar, mas deixa escapar parte dos casos.")
    else:
        w(f"* **Tipo de erro:** precisão ({pct(m_te['precisao'])}) e recall ({pct(m_te['recall'])}) estão equilibrados.")
    if p_esc.get("class_weight") == "balanced":
        w("* `class_weight = balanced` foi escolhido na validação: dar mais peso à classe minoritária aumenta o recall "
          "e é útil quando perder um caso positivo custa mais que um falso alarme.")
    gap = m_tr["f1"] - m_te["f1"]
    w(f"* **Generalização:** F1 de {pct(m_tr['f1'])} no treino contra {pct(m_te['f1'])} no teste (diferença de "
      f"{br(100 * gap, 1)} p.p.). A árvore sem controle chega a {pct(m_pad['f1'])} de F1 no teste, "
      f"{'pior' if m_pad['f1'] < m_te['f1'] else 'semelhante ou melhor'} que a escolhida, com muito mais folhas — "
      f"mais complexa nem sempre é mais precisa.")
    w("* **Interpretabilidade:** as regras acima podem ser lidas e auditadas por um profissional de saúde; isso é uma "
      "vantagem sobre modelos opacos. Modelos mais complexos (florestas, boosting) podem render desempenho maior; isso "
      "não foi avaliado aqui por estar fora do escopo da questão.\n")
    w("## 8. Limitações e cuidados\n")
    w("* Conjunto pequeno ({} exemplos) e de uma população específica; resultados **não generalizam** para outras "
      "populações e **não servem para diagnóstico** — é um exercício didático.".format(n))
    w("* A imputação pela mediana é simples; atributos com muitos ausentes (insulina, dobra do tríceps) ficam com um "
      "valor artificial concentrado na mediana, e limiares da árvore próximos a essa mediana devem ser lidos com cautela.")
    w("* Um único particionamento treino/teste; a validação cruzada repetida no treino mostra a variabilidade esperada.")
    w("* Limiares de árvores são sensíveis a pequenas mudanças nos dados (instabilidade típica de árvores).\n")
    w("## 9. Reprodutibilidade\n")
    w("```bash\npip install -r requirements.txt\n# coloque o arquivo em data/diabetes.csv\npython -m q3.executar\n```")
    w(f"Versões: scikit-learn {sklearn.__version__}, pandas {pd.__version__}, numpy {np.__version__}. Sementes fixas "
      f"(divisão: {D.SEMENTE}; validação cruzada: {D.SEMENTE}; árvore: 0; bootstrap: 7).")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
