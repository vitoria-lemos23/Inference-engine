"""Questão 2 -- árvores e regras com implementações de bibliotecas (scikit-learn) e comparação com a Q1.

Uso (na raiz do repositório):  python -m q2.executar
"""
from __future__ import annotations

import itertools
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from ia import arvores as A
from ia import regras as G
from ia import relatorio as R
from ia import sk_utils as SK
from q1.executar import carregar

AQUI = Path(__file__).parent
RES = AQUI / "resultados"
DADOS = AQUI / "dados"
RES.mkdir(exist_ok=True)
DADOS.mkdir(exist_ok=True)


# ====================================================================== modelos
def fabrica_cart(**kw):
    return lambda: DecisionTreeClassifier(criterion="gini", random_state=0, **kw)


def fabrica_entropia(**kw):
    return lambda: DecisionTreeClassifier(criterion="entropy", random_state=0, **kw)


def avaliar_sklearn(fabrica, base, X, y, k=5, repeticoes=20, semente=42):
    """Treino, leave-one-out e CV 5-fold estratificada repetida (mesmas dobras do pacote `ia`)."""
    modelo = fabrica().fit(X, y)
    acc_treino = float((modelo.predict(X) == y).mean())
    certos = 0
    for i in range(len(y)):
        m = fabrica().fit(np.delete(X, i, axis=0), np.delete(y, i))
        certos += m.predict(X[i:i + 1])[0] == y[i]
    loo = certos / len(y)
    accs = []
    for dobras in A.gerar_dobras(base, k, repeticoes, semente):
        c = 0
        for teste in dobras:
            tr = np.setdiff1d(np.arange(len(y)), teste)
            m = fabrica().fit(X[tr], y[tr])
            c += int((m.predict(X[teste]) == y[teste]).sum())
        accs.append(c / len(y))
    return modelo, acc_treino, loo, statistics.mean(accs), statistics.pstdev(accs)


def salvar_arvore_sklearn(modelo, base, destino, titulo):
    nomes = [SK.nome_dummy(a, v) for a, v in SK.nomes_dummies(base)]
    texto = export_text(modelo, feature_names=nomes, show_weights=True)
    (RES / f"{destino}.txt").write_text(texto, encoding="utf-8")
    n_folhas = modelo.get_n_leaves()
    fig, ax = plt.subplots(figsize=(max(14, 1.6 * n_folhas), 4 + 1.0 * modelo.get_depth()))
    nomes_plot = [n.replace("$", r"\$") for n in nomes]   # o matplotlib trata $...$ como fórmula
    plot_tree(modelo, feature_names=nomes_plot, class_names=[str(c) for c in modelo.classes_], filled=True,
              rounded=True, impurity=True, fontsize=7, ax=ax, proportion=False)
    ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(RES / f"{destino}.png", dpi=130)
    plt.close(fig)
    return texto


def gerar_arff(base, caminho):
    """Exporta a base em ARFF para quem quiser repetir a Q2 no Weka (J48 = C4.5)."""
    q = lambda v: "'" + v.replace("'", "\\'") + "'"
    linhas = ["@relation credito_ampliado", ""]
    for a in base.atributos:
        linhas.append(f"@attribute {q(a)} {{{','.join(q(v) for v in base.dominios[a])}}}")
    linhas.append(f"@attribute {q(base.classe)} {{{','.join(q(c) for c in base.classes)}}}")
    linhas += ["", "@data"]
    for l in base.linhas:
        linhas.append(",".join(q(l[a]) for a in base.atributos) + "," + q(l[base.classe]))
    Path(caminho).write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    base = carregar()
    X, y = SK.codificar(base), SK.rotulos(base)
    espaco = [dict(zip(base.atributos, c)) for c in itertools.product(*[base.dominios[a] for a in base.atributos])]
    Xesp = SK.codificar(base, espaco)
    gerar_arff(base, DADOS / "credito_ampliado.arff")

    # ---------------------------------------------------------------- modelos de biblioteca
    modelos = {
        "sklearn · CART (Gini)": ("sk_cart", fabrica_cart()),
        "sklearn · entropia (ganho de informação)": ("sk_entropia", fabrica_entropia()),
    }
    res = {}
    for nome, (slug, fab) in modelos.items():
        modelo, acc_tr, loo, cvm, cvs = avaliar_sklearn(fab, base, X, y)
        salvar_arvore_sklearn(modelo, base, f"arvore_{slug}", nome)
        regras = SK.regras_de_arvore_sklearn(modelo, base)
        (RES / f"regras_{slug}.md").write_text(f"# Regras — {nome}\n\n" + R.regras_md(regras, base.classe) + "\n", encoding="utf-8")
        (RES / f"regras_{slug}.txt").write_text(R.regras_texto(regras, base.classe) + "\n", encoding="utf-8")
        G.salvar_json(regras, RES / f"regras_{slug}.json", {"algoritmo": nome, "classe": base.classe})
        res[nome] = dict(slug=slug, modelo=modelo, regras=regras, acc_treino=acc_tr, loo=loo, cv=cvm, cv_dp=cvs,
                         profundidade=int(modelo.get_depth()), folhas=int(modelo.get_n_leaves()),
                         prev_espaco=list(modelo.predict(Xesp)), texto=(RES / f"arvore_{slug}.txt").read_text(encoding="utf-8"))

    # ---------------------------------------------------------------- implementações próprias (pacote ia)
    proprios = {}
    for rotulo, alg, pod in [("ia · ID3", "ID3", False), ("ia · C4.5", "C4.5", False),
                             ("ia · C4.5 podada", "C4.5", True), ("ia · CART", "CART", False)]:
        r = A.construir(base, alg, podar=pod)[0]
        rg = G.extrair_regras(r)
        loo = A.leave_one_out(base, alg, podar=pod)[0]
        cvm, cvs, _ = A.validacao_cruzada(base, alg, podar=pod)
        proprios[rotulo] = dict(raiz=r, regras=rg, acc_treino=A.acuracia(r, base), loo=loo, cv=cvm, cv_dp=cvs,
                                profundidade=A.profundidade(r), folhas=len(A.folhas(r)),
                                prev_espaco=[A.prever(r, e) for e in espaco])
    # ---------------------------------------------------------------- poda por custo-complexidade (CART do sklearn)
    caminho = DecisionTreeClassifier(criterion="gini", random_state=0).cost_complexity_pruning_path(X, y)
    alfas = sorted(set(float(a) for a in caminho.ccp_alphas))
    poda = []
    for a in alfas:
        modelo, acc_tr, loo, cvm, cvs = avaliar_sklearn(fabrica_cart(ccp_alpha=a), base, X, y)
        poda.append({"alfa": a, "folhas": int(modelo.get_n_leaves()), "acc_treino": acc_tr, "loo": loo, "cv": cvm, "cv_dp": cvs})
    # (!) escolher o alfa pela própria CV seria otimista; a tabela serve para discutir a tendência.

    # ---------------------------------------------------------------- verificação cruzada com as fórmulas do pacote `ia`
    nomes_d = SK.nomes_dummies(base)
    n = len(base)
    linhas_ver = []
    for j, (a, v) in enumerate(nomes_d):
        sim = [l for l in base.linhas if l[a] == v]
        nao = [l for l in base.linhas if l[a] != v]
        cs, cn = base.contar(sim), base.contar(nao)
        g = len(sim) / n * A.gini(cs.values()) + len(nao) / n * A.gini(cn.values())
        h = A.entropia(base.contar().values()) - (len(sim) / n * A.entropia(cs.values()) + len(nao) / n * A.entropia(cn.values()))
        linhas_ver.append((SK.nome_dummy(a, v), g, h, j))
    raiz_cart = int(res["sklearn · CART (Gini)"]["modelo"].tree_.feature[0])
    raiz_ent = int(res["sklearn · entropia (ganho de informação)"]["modelo"].tree_.feature[0])
    min_g = min(x[1] for x in linhas_ver)
    max_h = max(x[2] for x in linhas_ver)
    ver = {
        "gini_raiz_sklearn": linhas_ver[raiz_cart][0], "gini_raiz_otima": abs(linhas_ver[raiz_cart][1] - min_g) < 1e-12,
        "ent_raiz_sklearn": linhas_ver[raiz_ent][0], "ent_raiz_otima": abs(linhas_ver[raiz_ent][2] - max_h) < 1e-12,
        "tabela": sorted(linhas_ver, key=lambda x: x[1])[:6], "tabela_h": sorted(linhas_ver, key=lambda x: -x[2])[:6],
    }
    assert ver["gini_raiz_otima"] and ver["ent_raiz_otima"], "o sklearn deveria escolher a melhor divisão binária"
    # a raiz do CART próprio (subconjuntos) coincide com a do sklearn (um-contra-resto)?
    p1 = proprios["ia · CART"]
    raiz_ia = p1["raiz"]
    ver["cart_ia_raiz"] = f"{raiz_ia.atributo} ∈ {{{', '.join(raiz_ia.ramos[0][1])}}}"
    assert raiz_ia.atributo == "Renda" and set(raiz_ia.ramos[1][1]) == {"Acima de $35k"} and ver["gini_raiz_sklearn"] == "Renda = Acima de $35k"

    # ---------------------------------------------------------------- concordância no espaço de entradas
    todos = {**res, **proprios}
    nomes = list(todos)
    conc = {(a, b): sum(x == y_ for x, y_ in zip(todos[a]["prev_espaco"], todos[b]["prev_espaco"])) / len(espaco)
            for a, b in itertools.combinations(nomes, 2)}

    resumo = {n_: {k: v for k, v in d.items() if k in ("folhas", "profundidade", "acc_treino", "loo", "cv", "cv_dp")}
              for n_, d in todos.items()}
    json.dump({"modelos": resumo, "poda_ccp": poda, "versao_sklearn": sklearn.__version__},
              open(RES / "comparacao_q2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    md = montar_relatorio(base, res, proprios, poda, ver, conc)
    (AQUI / "RELATORIO.md").write_text(md, encoding="utf-8")
    print("Q2 concluída. Veja q2/RELATORIO.md e q2/resultados/.")
    for n_, d in todos.items():
        print(f"  {n_:45s} folhas={d['folhas']:2d} prof={d['profundidade']} treino={d['acc_treino']:.3f} LOO={d['loo']:.3f} CV={d['cv']:.3f}±{d['cv_dp']:.3f}")


def montar_relatorio(base, res, proprios, poda, ver, conc):
    pct = lambda x: f"{100 * x:.1f}%".replace(".", ",")
    br = R.br
    cart, ent = res["sklearn · CART (Gini)"], res["sklearn · entropia (ganho de informação)"]
    idp, c45, c45p, cartp = (proprios[k] for k in ("ia · ID3", "ia · C4.5", "ia · C4.5 podada", "ia · CART"))
    todos = {**res, **proprios}

    # afirmações usadas no texto
    assert cart["profundidade"] > idp["profundidade"] and ent["profundidade"] > idp["profundidade"]
    assert idp["cv"] > cart["cv"] and idp["cv"] > ent["cv"]
    assert all(d["cv"] <= poda[0]["cv"] + 1e-9 for d in poda), "o texto afirma que a poda não melhora a CV"

    cab = ["Modelo", "Origem", "Folhas", "Prof.", "Treino", "LOO", "CV 5-fold ×20"]
    orig = {"sklearn": "biblioteca (scikit-learn)", "ia": "implementação própria (pacote `ia`)"}
    linhas = [[n, orig[n.split(" · ")[0]], d["folhas"], d["profundidade"], pct(d["acc_treino"]), pct(d["loo"]),
               f"{pct(d['cv'])} ± {pct(d['cv_dp'])}"] for n, d in todos.items()]
    t_comp = R.tabela_md(cab, linhas)

    t_conc = R.tabela_md(["Par de modelos", "Concordância (216 combinações)"],
                         [[f"{a} × {b}", pct(v)] for (a, b), v in conc.items()
                          if a.startswith("sklearn") or b.startswith("sklearn")])

    t_ver = R.tabela_md(["Divisão binária (atributo = valor vs. resto)", "Gini ponderado", "Ganho de informação"],
                        [[x[0], br(x[1]), br(x[2])] for x in ver["tabela"]])

    t_poda = R.tabela_md(["ccp_alpha", "Folhas", "Acurácia no treino", "LOO", "CV 5-fold ×20"],
                         [[br(d["alfa"], 5), d["folhas"], pct(d["acc_treino"]), pct(d["loo"]),
                           f"{pct(d['cv'])} ± {pct(d['cv_dp'])}"] for d in poda])

    md = f"""# Questão 2 — Árvores e regras com implementações de bibliotecas (ID3, C4.5 e CART)

> Mesma base ampliada da Questão 1 (30 exemplos, 6 atributos). Todos os números são gerados por
> `python -m q2.executar`; versão do scikit-learn usada: **{sklearn.__version__}**.

## O que foi usado de cada algoritmo (transparência)

| Algoritmo | Como foi obtido nesta questão | Observação |
|---|---|---|
| **CART** | `sklearn.tree.DecisionTreeClassifier(criterion="gini")` | é o CART otimizado do scikit-learn; divide em *binário* sobre atributos codificados em one-hot (um valor contra os demais) |
| **ID3 (aprox.)** | `DecisionTreeClassifier(criterion="entropy")` | usa o **ganho de informação** do ID3, mas, no scikit-learn, as divisões continuam binárias (um valor vs. resto); não é o ID3 multivalorado |
| **ID3 e C4.5 "de verdade"** | pacote `ia` do repositório (`ia.arvores.construir`) | o scikit-learn **não** implementa ID3 nem C4.5 (razão de ganho, divisão multivalorada, poda pessimista). Weka/J48, R/C50 e `chefboost` não estavam disponíveis no ambiente em que o trabalho foi executado (sem acesso à rede para instalar), então usei a implementação própria, a mesma da Q1, chamada pela API |

Para quem quiser repetir com o **Weka (J48 = C4.5)**, a base foi exportada em ARFF:
[`dados/credito_ampliado.arff`](dados/credito_ampliado.arff) *(arquivo gerado por código; não pude executá-lo no Weka neste ambiente)*.

## Preparação dos dados para o scikit-learn

O scikit-learn só aceita atributos numéricos. Cada par *atributo = valor* virou uma coluna 0/1 (**one-hot**: {len(SK.nomes_dummies(base))}
colunas), com domínios fixos para que o treino/teste usem sempre as mesmas colunas. Um teste do tipo
`Renda = Acima de $35k ≤ 0,5` significa "Renda ≠ Acima de $35k". Para apresentar as regras, essas condições são traduzidas de volta
para `atributo = valor` ou `atributo ∈ {{...}}` (os valores restantes após as exclusões). `random_state = 0` fixa o desempate
entre divisões de mesma qualidade (o scikit-learn sorteia a ordem dos atributos).

## Árvore 1 — CART (scikit-learn, Gini)

![CART sklearn](resultados/arvore_sk_cart.png)

```
{cart['texto']}```

### Base de regras (CART / scikit-learn) — {len(cart['regras'])} regras

{R.regras_md(cart['regras'], base.classe)}

## Árvore 2 — critério de entropia / ganho de informação (scikit-learn, "ID3 binário")

![entropia sklearn](resultados/arvore_sk_entropia.png)

```
{ent['texto']}```

### Base de regras (entropia / scikit-learn) — {len(ent['regras'])} regras

{R.regras_md(ent['regras'], base.classe)}

## Árvores 3 e 4 — ID3 e C4.5 (implementação própria, pacote `ia`)

O scikit-learn não tem ID3 nem C4.5; as árvores abaixo vêm de `ia.arvores.construir(base, "ID3")` e `construir(base, "C4.5")`
(o passo a passo completo dos cálculos está na Questão 1: [`passo_a_passo_id3.md`](../q1/resultados/passo_a_passo_id3.md) e
[`passo_a_passo_c45.md`](../q1/resultados/passo_a_passo_c45.md)).

### ID3 — {len(idp['regras'])} regras

![ID3](../q1/resultados/arvore_id3.png)

{R.regras_md(idp['regras'], base.classe)}

### C4.5 (razão de ganho) — {len(c45['regras'])} regras

![C4.5](../q1/resultados/arvore_c45.png)

{R.regras_md(c45['regras'], base.classe)}

Após a poda pessimista, o C4.5 fica com {len(c45p['regras'])} regras ([`regras_c45_podada.md`](../q1/resultados/regras_c45_podada.md)).

## Verificação cruzada: as escolhas do scikit-learn conferem com as fórmulas do pacote `ia`?

Recalculei, com as funções `gini` e `entropia` do pacote `ia`, todas as divisões binárias "atributo = valor vs. resto" da raiz.
As melhores divisões foram:

{t_ver}

* Raiz do CART do scikit-learn: **{ver['gini_raiz_sklearn']}** — {"é" if ver['gini_raiz_otima'] else "NÃO é"} a divisão de menor Gini ponderado.
* Raiz da árvore por entropia: **{ver['ent_raiz_sklearn']}** — {"é" if ver['ent_raiz_otima'] else "NÃO é"} a divisão de maior ganho de informação.
* O CART próprio da Q1 (que testa subconjuntos de valores) escolheu na raiz **{ver['cart_ia_raiz']}** vs. o resto, que é a **mesma partição**
  de "Renda = Acima de $35k vs. resto": as duas implementações concordam na raiz.

## Comparação

{t_comp}

Concordância das previsões com os modelos do scikit-learn, nas 216 combinações possíveis de atributos:

{t_conc}

### Análise

1. **Árvores binárias do scikit-learn são mais profundas.** Com um-valor-contra-resto, atributos de 3 valores exigem vários
   testes encadeados: profundidade {cart['profundidade']} (CART) e {ent['profundidade']} (entropia), contra {idp['profundidade']} no ID3 multivalorado — o que significa
   mais perguntas por consulta em um sistema especialista.
2. **Gini × entropia dão árvores quase iguais** ({cart['folhas']} e {ent['folhas']} folhas; mesma raiz). A diferença está nos desempates
   entre divisões de mesma qualidade, controlados por `random_state`.
3. **Generalização.** Nesta base pequena, o ID3 multivalorado teve a melhor estimativa (CV {pct(idp['cv'])}) contra
   {pct(cart['cv'])} (CART sklearn) e {pct(ent['cv'])} (entropia sklearn); com desvio-padrão em torno de 8 pontos percentuais, as diferenças
   são modestas e devem ser lidas como indicativas (ver Q1, análise de sensibilidade).
4. **CART próprio × scikit-learn.** O CART próprio (subconjuntos de valores) e o do scikit-learn (um-contra-resto) têm o mesmo número de folhas
   ({cartp['folhas']} e {cart['folhas']}) e desempenho semelhante (CV {pct(cartp['cv'])} e {pct(cart['cv'])}); a busca em subconjuntos é mais
   expressiva, mas aqui não mudou o resultado de forma relevante.

## Poda por custo-complexidade (CART do scikit-learn)

O scikit-learn oferece a poda do CART por custo-complexidade (`ccp_alpha`). A tabela mostra o caminho de poda do CART nesta base
(*sem* escolher o melhor alfa pela própria CV, o que seria otimista):

{t_poda}

Aumentar `ccp_alpha` reduz folhas e acurácia de treino; a acurácia de validação **não melhora** em nenhum ponto da trilha, coerente com a Q1:
a base é pequena e sem ruído, e podar descarta casos legítimos.

## Reprodução

```bash
python -m q2.executar
```
"""
    return md


if __name__ == "__main__":
    main()
