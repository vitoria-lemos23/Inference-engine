"""Questão 1 -- base de crédito ampliada (6 atributos, 30 exemplos) e árvores ID3, C4.5 e CART.

Uso (na raiz do repositório):  python -m q1.executar

Gera em q1/resultados/ : passo a passo dos cálculos, árvores (.dot/.png/.svg/.txt), bases de regras
(.md/.txt/.json), comparação (.md/.json) e o relatório final q1/RELATORIO.md.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

from ia import arvores as A
from ia import regras as G
from ia import relatorio as R
from ia.base import Base

AQUI = Path(__file__).parent
RES = AQUI / "resultados"
RES.mkdir(exist_ok=True)

DOMINIOS = {
    "Renda": ["$0 a $15k", "$15 a $35k", "Acima de $35k"],
    "História de Crédito": ["Boa", "Desconhecida", "Ruim"],
    "Dívida": ["Baixa", "Alta"],
    "Garantia": ["Nenhuma", "Adequada"],
    "Tempo de Emprego": ["Curto", "Médio", "Longo"],
    "Residência": ["Alugada", "Própria"],
}
CLASSES = ["Baixo", "Moderado", "Alto"]

# (rótulo, algoritmo, poda?, slug de arquivo)
VARIANTES = [
    ("ID3", "ID3", False, "id3"),
    ("C4.5", "C4.5", False, "c45"),
    ("C4.5 podada", "C4.5", True, "c45_podada"),
    ("CART", "CART", False, "cart"),
]


def carregar():
    return Base.de_csv(AQUI / "dados" / "credito_ampliado.csv", "Risco", dominios=DOMINIOS, ordem_classes=CLASSES)


def escrever(nome, texto):
    (RES / nome).write_text(texto, encoding="utf-8")


def tabela_decisoes(passos, alg):
    """Resumo: uma linha por nó interno com o atributo escolhido e o valor do critério."""
    linhas = []
    for p in passos:
        if p.motivo != "dividido":
            continue
        if alg == "CART":
            q = p.detalhe["particao"]
            crit = f"Gini pond. = {R.br(q['gini_ponderado'])} (div.: {{{', '.join(q['esq'])}}} vs. resto)"
            ties = [c["atributo"] for c in p.candidatos if c["atributo"] != p.escolhido
                    and abs(c["melhor"]["gini_ponderado"] - q["gini_ponderado"]) < 1e-9]
        else:
            esc = next(c for c in p.candidatos if c["atributo"] == p.escolhido)
            if alg == "ID3":
                crit = f"ganho = {R.br(esc['ganho'])}"
                ties = [c["atributo"] for c in p.candidatos if c["atributo"] != p.escolhido
                        and abs(c["ganho"] - esc["ganho"]) < 1e-9]
            else:
                crit = f"razão de ganho = {R.br(esc['razao_ganho'])} (ganho = {R.br(esc['ganho'])})"
                ties = [c["atributo"] for c in p.candidatos if c["atributo"] != p.escolhido and c["elegivel"]
                        and abs(c["razao_ganho"] - esc["razao_ganho"]) < 1e-9]
        obs = f"empate com {', '.join(ties)}" if ties else ""
        linhas.append([p.no_id, R.caminho_txt(p.caminho), len(p.ids), R.cont_txt(p.contagem), f"**{p.escolhido}**", crit, obs])
    return R.tabela_md(["Nó", "Caminho", "n", "Distribuição", "Atributo", "Critério", "Obs."], linhas)


def sensibilidade(base):
    """Retira um exemplo por vez (30 sub-bases de 29 exemplos) e mede a acurácia leave-one-out de cada variante.
    Mostra o quão frágil é o ranking dos algoritmos com tão poucos exemplos."""
    nomes = [v[0] for v in VARIANTES]
    soma = {n: 0.0 for n in nomes}
    vitorias = {n: 0.0 for n in nomes}
    for j in range(len(base)):
        sub = base.sem_linha(j)
        accs = {rot: A.leave_one_out(sub, alg, podar=pod)[0] for rot, alg, pod, _ in VARIANTES}
        melhor = max(accs.values())
        top = [n for n in nomes if abs(accs[n] - melhor) < 1e-12]
        for n in nomes:
            soma[n] += accs[n]
        for n in top:
            vitorias[n] += 1 / len(top)
    k = len(base)
    return {n: {"loo_medio": soma[n] / k, "vitorias": vitorias[n]} for n in nomes}


def trecho_raiz(md):
    i = md.index("## Nó 1")
    j = md.index("## Nó 2")
    return md[i:j].replace("## Nó 1  —  (raiz)", "#### Nó raiz (nó 1) — cálculos completos")


def main():
    base = carregar()
    assert len(base) == 30 and len(base.atributos) == 6, "a base deve ter 30 exemplos e 6 atributos"
    assert not base.conflitos(), "base inconsistente"
    cont = base.contar()
    espaco = [dict(zip(base.atributos, c)) for c in itertools.product(*[base.dominios[a] for a in base.atributos])]

    # ------------------------------------------------------------ base ampliada
    escrever("00_base_ampliada.md", "# Base de crédito ampliada (30 exemplos, 6 atributos)\n\n" + R.tabela_base_md(base) + "\n")

    # ------------------------------------------------------------ construção
    saidas = {}
    for rotulo, alg, pod, slug in VARIANTES:
        out = A.construir(base, alg, podar=pod)
        raiz, passos = out[0], out[1]
        log = out[2] if pod else None
        regras = G.extrair_regras(raiz)
        saidas[rotulo] = dict(alg=alg, slug=slug, raiz=raiz, passos=passos, log=log, regras=regras)
        # passo a passo (a variante podada reaproveita o do C4.5 completo)
        if not pod:
            escrever(f"passo_a_passo_{slug}.md", R.passo_a_passo_md(base, passos, alg, f"Q1 — {rotulo}"))
        # árvore
        escrever(f"arvore_{slug}.txt", R.arvore_texto(raiz) + "\n")
        R.salvar_arvore(raiz, base.classes, RES / f"arvore_{slug}", f"{rotulo}")
        # regras
        escrever(f"regras_{slug}.md", f"# Base de regras — {rotulo}\n\n" + R.regras_md(regras, base.classe) + "\n")
        escrever(f"regras_{slug}.txt", R.regras_texto(regras, base.classe) + "\n")
        G.salvar_json(regras, RES / f"regras_{slug}.json", {"algoritmo": rotulo, "classe": base.classe,
                                                              "base": "credito_ampliado.csv"})

    # ------------------------------------------------------------ métricas de comparação
    comp = {}
    for rotulo, alg, pod, slug in VARIANTES:
        s = saidas[rotulo]
        r, rg = s["raiz"], s["regras"]
        st = G.estatisticas(rg)
        loo, _ = A.leave_one_out(base, alg, podar=pod)
        cv_m, cv_s, _ = A.validacao_cruzada(base, alg, k=5, repeticoes=20, semente=42, podar=pod)
        cobertas = sum(any(x.cobre(e) for x in rg) for e in espaco)
        perguntas = sum(len(A.caminho_decisao(r, e)[0]) for e in espaco) / len(espaco)
        comp[rotulo] = {
            "regras": st["regras"], "cond_media": st["condicoes_media"], "cond_max": st["condicoes_max"],
            "profundidade": A.profundidade(r), "atributos": A.atributos_usados(r),
            "acc_treino": A.acuracia(r, base), "acc_loo": loo, "acc_cv_media": cv_m, "acc_cv_dp": cv_s,
            "cobertura_espaco": cobertas / len(espaco), "cobertas": cobertas, "perguntas_medias": perguntas,
            "previsoes_espaco": [A.prever(r, e) for e in espaco],
        }
    concord = {}
    for a, b in itertools.combinations([v[0] for v in VARIANTES], 2):
        pa, pb = comp[a]["previsoes_espaco"], comp[b]["previsoes_espaco"]
        concord[(a, b)] = sum(x == y for x, y in zip(pa, pb)) / len(espaco)

    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "previsoes_espaco"} for k, v in comp.items()},
              open(RES / "comparacao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    sens = sensibilidade(base)

    # exemplo de consulta (coberto pelas três bases) em que as bases discordam
    tres = ("ID3", "C4.5", "CART")
    def cobertas_por_todas(e):
        return all(any(x.cobre(e) for x in saidas[n]["regras"]) for n in tres)
    exemplo = None
    for alvo in (3, 2):
        for i, e in enumerate(espaco):
            if cobertas_por_todas(e) and len({comp[n]["previsoes_espaco"][i] for n in tres}) == alvo:
                exemplo = e
                break
        if exemplo:
            break

    # ------------------------------------------------------------ relatório
    md = montar_relatorio(base, cont, saidas, comp, concord, exemplo, sens)
    (AQUI / "RELATORIO.md").write_text(md, encoding="utf-8")
    escrever("comparacao.md", secao_comparacao(base, saidas, comp, concord, exemplo, so_tabelas=True))
    print("Q1 concluída. Veja q1/RELATORIO.md e q1/resultados/.")
    for k, v in comp.items():
        print(f"  {k:12s} regras={v['regras']:2d} treino={v['acc_treino']:.3f} LOO={v['acc_loo']:.3f} "
              f"CV5x20={v['acc_cv_media']:.3f}±{v['acc_cv_dp']:.3f} perguntas={v['perguntas_medias']:.2f}")


# ====================================================================== texto do relatório
def secao_comparacao(base, saidas, comp, concord, exemplo, so_tabelas=False):
    nomes = [v[0] for v in VARIANTES]
    pct = lambda x: f"{100 * x:.1f}%".replace(".", ",")
    cab = ["Critério"] + nomes
    linhas = [
        ["Nº de regras (folhas)"] + [comp[n]["regras"] for n in nomes],
        ["Condições por regra (média / máx.)"] + [f"{R.br(comp[n]['cond_media'], 2)} / {comp[n]['cond_max']}" for n in nomes],
        ["Profundidade da árvore"] + [comp[n]["profundidade"] for n in nomes],
        ["Atributos usados"] + [f"{len(comp[n]['atributos'])} ({', '.join(comp[n]['atributos'])})" for n in nomes],
        ["Acurácia no treino (30 ex.)"] + [pct(comp[n]["acc_treino"]) for n in nomes],
        ["Acurácia leave-one-out"] + [pct(comp[n]["acc_loo"]) for n in nomes],
        ["Acurácia CV 5-fold estratificado (20 repetições)"] + [f"{pct(comp[n]['acc_cv_media'])} ± {pct(comp[n]['acc_cv_dp'])}" for n in nomes],
        [f"Cobertura do espaço de entradas ({len(comp[nomes[0]]['previsoes_espaco'])} combinações)"] + [f"{comp[n]['cobertas']} ({pct(comp[n]['cobertura_espaco'])})" for n in nomes],
        ["Perguntas ao usuário por consulta (média)"] + [R.br(comp[n]["perguntas_medias"], 2) for n in nomes],
    ]
    t1 = R.tabela_md(cab, linhas)
    pares = list(concord)
    t2 = R.tabela_md(["Par de bases", "Concordância nas 216 combinações possíveis"],
                     [[f"{a} × {b}", pct(concord[(a, b)])] for a, b in pares])
    return f"### Métricas comparativas\n\n{t1}\n\n### Concordância entre as bases\n\n{t2}\n"


def montar_relatorio(base, cont, saidas, comp, concord, exemplo, sens):
    pct = lambda x: f"{100 * x:.1f}%".replace(".", ",")
    br = R.br
    id3, c45, c45p, cart = (saidas[k] for k in ("ID3", "C4.5", "C4.5 podada", "CART"))

    # --- verificações que sustentam o texto abaixo (se a base mudar, o relatório avisa)
    assert id3["passos"][0].escolhido == c45["passos"][0].escolhido == "Renda"
    assert cart["passos"][0].escolhido == "Renda"
    # afirmações do texto de análise/escolha (se a base mudar e alguma deixar de valer, o relatório falha aqui)
    assert max(comp, key=lambda k: comp[k]["acc_cv_media"]) == "ID3"
    assert max(comp, key=lambda k: comp[k]["acc_loo"]) == "ID3"
    assert max(sens, key=lambda k: sens[k]["loo_medio"]) == "ID3"
    assert comp["ID3"]["cobertas"] == 216 and comp["C4.5"]["cobertas"] < 216 and comp["CART"]["cobertas"] < 216
    assert comp["C4.5 podada"]["acc_cv_media"] < comp["C4.5"]["acc_cv_media"]
    assert comp["CART"]["perguntas_medias"] > comp["ID3"]["perguntas_medias"]
    assert comp["ID3"]["profundidade"] <= min(comp[k]["profundidade"] for k in comp)
    assert comp["ID3"]["cond_media"] <= min(comp[k]["cond_media"] for k in ("C4.5", "CART"))
    assert next(p for p in c45["passos"] if p.no_id == 7).escolhido == "Tempo de Emprego"
    assert next(p for p in id3["passos"] if p.no_id == 8).escolhido == "História de Crédito"
    assert len(id3["regras"]) == len(c45["regras"])

    p_id3_n2 = next(p for p in id3["passos"] if p.no_id == 2)
    p_c45_n2 = next(p for p in c45["passos"] if p.no_id == 2)
    ex_txt = ", ".join(f"{a} = {v}" for a, v in exemplo.items())

    # tabela da poda
    log = sorted(c45p["log"], key=lambda d: d["no_id"])
    t_poda = R.tabela_md(
        ["Nó", "Atributo testado", "n", "Erros se virar folha", "Erro estimado (folha)", "Erro estimado (subárvore)", "Decisão"],
        [[d["no_id"], d["atributo"], d["n"], d["erros_folha"], br(d["est_folha"], 3), br(d["est_subarvore"], 3),
          "**podar**" if d["podado"] else "manter"] for d in log])

    def bloco_regras(s, titulo):
        return f"#### {titulo}\n\n" + R.regras_md(s["regras"], base.classe) + "\n"

    dist = ", ".join(f"{k}: {v}" for k, v in cont.items())
    novos = [l for l in base.linhas if int(l["ID"][1:]) >= 15]
    cn = base.contar(novos)

    md = f"""# Questão 1 — Árvores de decisão construídas "à mão" (ID3, C4.5 e CART)

> Todos os números deste relatório são **gerados por código** (`python -m q1.executar`); nada foi digitado à mão.
> O passo a passo completo (todos os nós, todos os atributos, todas as partições) está em
> [`resultados/passo_a_passo_id3.md`](resultados/passo_a_passo_id3.md),
> [`resultados/passo_a_passo_c45.md`](resultados/passo_a_passo_c45.md) e
> [`resultados/passo_a_passo_cart.md`](resultados/passo_a_passo_cart.md).

## (i) Ampliação da base para 6 atributos e 30 exemplos

A base original do "gerente do banco" (baseada em Luger) tem 14 exemplos e 4 atributos (História de Crédito, Dívida,
Garantia, Renda) com a classe **Risco** ∈ {{Baixo, Moderado, Alto}}. (No enunciado, o exemplo E13 aparece como "baixo" em
minúsculas; foi normalizado para **Baixo**.)

**Novos atributos (2):**

| Atributo | Valores | Motivação |
|---|---|---|
| Tempo de Emprego | Curto (< 1 ano), Médio (1 a 5 anos), Longo (> 5 anos) | estabilidade da renda: quem tem emprego longo costuma ter menor risco |
| Residência | Alugada, Própria | patrimônio/estabilidade: imóvel próprio atenua o risco |

**Novos exemplos (16: E15 a E30):** {cn['Alto']} de risco Alto, {cn['Moderado']} Moderado e {cn['Baixo']} Baixo, de modo que a base final
tem {len(base)} exemplos com distribuição **{dist}**. Os valores dos dois novos atributos também foram atribuídos
aos 14 exemplos originais (sem alterar nenhum dos valores originais nem as classes).

Os exemplos adicionados são **fictícios**, criados seguindo uma "política" plausível do gerente, para que as árvores tenham
estrutura interessante e não degenerem: (1) renda baixa leva a risco Alto, salvo exceções com garantia/emprego longo;
(2) renda média depende do histórico e da dívida, e emprego longo com residência própria "rebaixa" o risco em um nível;
(3) renda alta leva a risco Baixo, exceto histórico Ruim (Moderado). Verificou-se que **não há exemplos conflitantes**
(mesmos valores de atributos com classes diferentes).

{R.tabela_base_md(base)}

Arquivo: [`dados/credito_ampliado.csv`](dados/credito_ampliado.csv).

## (ii) Construção das três árvores

### Fórmulas usadas

* Entropia: H(S) = − Σ pᵢ·log₂ pᵢ  ·  Ganho(S, A) = H(S) − Σ (|S_v|/|S|)·H(S_v)
* Informação da divisão: InfoDivisão(A) = − Σ (|S_v|/|S|)·log₂(|S_v|/|S|)  ·  Razão de ganho = Ganho / InfoDivisão
* Gini: G(S) = 1 − Σ pᵢ²  ·  Gini ponderado de uma divisão binária = (n_esq/n)·G_esq + (n_dir/n)·G_dir

| Algoritmo | Critério | Tipo de divisão | Poda |
|---|---|---|---|
| ID3 | maior **ganho de informação** | multivalorada (um ramo por valor) | não |
| C4.5 | maior **razão de ganho**, entre os atributos com ganho ≥ ganho médio | multivalorada | pessimista (CF = 25 %) |
| CART | menor **Gini ponderado** | **sempre binária** (subconjunto de valores vs. resto) | não (ver discussão) |

Empates de critério são desfeitos pela ordem das colunas da base; a classe de uma folha não pura é a maioria (empate →
classe mais grave). Ramos só são criados para valores observados no nó.

### ID3

{trecho_raiz(R.passo_a_passo_md(base, id3['passos'], 'ID3'))}

Decisões em todos os nós:

{tabela_decisoes(id3['passos'], 'ID3')}

![ID3](resultados/arvore_id3.png)

```
{R.arvore_texto(id3['raiz'])}
```

### C4.5

{trecho_raiz(R.passo_a_passo_md(base, c45['passos'], 'C4.5'))}

**Diferença em relação ao ID3 (nó 2, Renda = $0 a $15k).** Os atributos *Tempo de Emprego* e *Residência* empatam em ganho
de informação ({br(next(c for c in p_id3_n2.candidatos if c['atributo'] == 'Tempo de Emprego')['ganho'])}); o ID3 desempata
pela ordem das colunas e escolhe *Tempo de Emprego*. O C4.5 usa a razão de ganho, que penaliza atributos com mais valores
(*Tempo de Emprego* tem 3 valores, razão = {br(next(c for c in p_c45_n2.candidatos if c['atributo'] == 'Tempo de Emprego')['razao_ganho'])};
*Residência* tem 2, razão = {br(next(c for c in p_c45_n2.candidatos if c['atributo'] == 'Residência')['razao_ganho'])}) e escolhe
*Residência*. É exatamente o viés do ID3 por atributos multivalorados que o C4.5 corrige.

Decisões em todos os nós:

{tabela_decisoes(c45['passos'], 'C4.5')}

**Árvore C4.5 antes da poda:**

![C4.5](resultados/arvore_c45.png)

```
{R.arvore_texto(c45['raiz'])}
```

**Poda pessimista (CF = 25 %).** Para cada nó interno, compara-se o erro estimado (limite superior do intervalo de
confiança binomial, "AddErrs" do C4.5) de transformá-lo em folha com a soma dos erros estimados de suas folhas; poda-se
quando folha ≤ subárvore + 0,1. Subárvores são avaliadas de baixo para cima:

{t_poda}

Resultado: {len(G.extrair_regras(c45['raiz'])) - len(c45p['regras'])} folha(s) removida(s) — a árvore passa de {len(c45['regras'])} para {len(c45p['regras'])} folhas.

![C4.5 podada](resultados/arvore_c45_podada.png)

```
{R.arvore_texto(c45p['raiz'])}
```

### CART

{trecho_raiz(R.passo_a_passo_md(base, cart['passos'], 'CART'))}

Decisões em todos os nós:

{tabela_decisoes(cart['passos'], 'CART')}

![CART](resultados/arvore_cart.png)

```
{R.arvore_texto(cart['raiz'])}
```

Como o CART só faz perguntas binárias, atributos com 3 valores (Renda, Tempo de Emprego, História de Crédito) podem ser
reutilizados ao longo de um mesmo caminho (por exemplo, "Renda ∈ {{$0 a $15k, $15 a $35k}}?" seguida de
"Renda = $0 a $15k?"); por isso a árvore é mais profunda (profundidade {comp['CART']['profundidade']}), embora tenha poucas folhas. Na extração de regras, essas
condições repetidas são fundidas em uma só (interseção).

## (iii) Bases de conhecimento (regras SE … ENTÃO …)

Cada folha gera uma regra; as condições do caminho formam a conjunção do SE. "Cobertura" é o número de exemplos de treino
que a regra cobre e "Confiança", a fração deles em que a conclusão é correta.

{bloco_regras(id3, f"Base de regras do ID3 ({len(id3['regras'])} regras)")}
{bloco_regras(c45, f"Base de regras do C4.5, árvore completa ({len(c45['regras'])} regras)")}
{bloco_regras(c45p, f"Base de regras do C4.5 após a poda ({len(c45p['regras'])} regras)")}
{bloco_regras(cart, f"Base de regras do CART ({len(cart['regras'])} regras)")}

Os mesmos conjuntos em texto simples e JSON: `resultados/regras_*.txt` e `resultados/regras_*.json` (o JSON é lido pelo
shell da Questão 5 para montar a base de conhecimento do sistema de crédito).

## (iv) Comparação das bases e escolha

{secao_comparacao(base, saidas, comp, concord, exemplo)}

Como ler as métricas:
* **Acurácia no treino** mede só o ajuste aos 30 exemplos (qualquer árvore sem poda chega a 100 %); **leave-one-out** e
  **CV 5-fold repetido** estimam a capacidade de generalizar.
* **Cobertura** é a fração das 216 combinações possíveis de valores para as quais alguma regra dispara; onde nenhuma
  regra cobre, o sistema não conclui (o shell da Q5 pergunta mais dados ou informa que não há conclusão).
* **Perguntas por consulta** é o comprimento médio do caminho: quantos atributos o usuário precisa informar até a
  conclusão — custo de interação de um sistema especialista.

**Consulta de exemplo em que as bases discordam** ({ex_txt}):

{R.tabela_md(["Base", "Conclusão", "Regra disparada"], [[n, A.prever(saidas[n]['raiz'], exemplo), next(r.id + ': ' + r.texto(base.classe) for r in saidas[n]['regras'] if r.cobre(exemplo))] for n in ('ID3', 'C4.5', 'CART')])}

### Análise

1. **Generalização.** O ID3 obteve a melhor estimativa fora da amostra: {pct(comp['ID3']['acc_loo'])} no leave-one-out e
   {pct(comp['ID3']['acc_cv_media'])} na validação cruzada repetida, contra {pct(comp['C4.5']['acc_cv_media'])} (C4.5),
   {pct(comp['CART']['acc_cv_media'])} (CART) e {pct(comp['C4.5 podada']['acc_cv_media'])} (C4.5 podada). Com apenas 30
   exemplos o desvio-padrão da CV é de cerca de 8 pontos percentuais; logo, a vantagem do ID3 sobre o C4.5 e o CART
   **não é estatisticamente forte** (ver sensibilidade abaixo).
2. **Tamanho e legibilidade.** CART e C4.5 podado têm menos regras ({comp['CART']['regras']} e {comp['C4.5 podada']['regras']}), mas o CART usa
   conjuntos de valores (∈) e, por ser binário, tem profundidade {comp['CART']['profundidade']} e {R.br(comp['CART']['perguntas_medias'], 2)} perguntas por consulta
   (contra {R.br(comp['ID3']['perguntas_medias'], 2)} do ID3). As regras do ID3 e do C4.5 só usam igualdades *atributo = valor*, de leitura
   direta; o ID3 tem as regras mais curtas ({R.br(comp['ID3']['cond_media'], 2)} condições em média) e a menor profundidade ({comp['ID3']['profundidade']}).
3. **Cobertura.** A base do ID3 cobre **{comp['ID3']['cobertas']} das 216** combinações possíveis ({pct(comp['ID3']['cobertura_espaco'])}), pois em todo nó
   interno os valores do atributo escolhido aparecem na amostra. Já C4.5 ({pct(comp['C4.5']['cobertura_espaco'])}) e CART
   ({pct(comp['CART']['cobertura_espaco'])}) deixam combinações sem regra. Para um sistema que precisa sempre concluir, isso importa.
4. **Critérios de seleção de atributos.** A razão de ganho do C4.5 corrige o viés do ID3 por atributos multivalorados (nó 2: empate de
   ganho decidido a favor de *Residência*, de 2 valores). Nesta base, porém, as escolhas do C4.5 no nó 7 (*Tempo de Emprego* no lugar de
   *História de Crédito*) geraram uma árvore do mesmo tamanho (14 regras), com cobertura menor e pior generalização. Não há ganho
   automático do C4.5 sobre o ID3 em bases pequenas e sem atributos "espúrios" de muitos valores.
5. **Poda.** Aqui a poda *piorou* a generalização (CV {pct(comp['C4.5 podada']['acc_cv_media'])}): a base é pequena e **sem ruído** (foi
   construída a partir de uma política consistente), então os casos raros que a poda elimina eram informação legítima. Em dados reais
   ruidosos (Questão 3) a poda tende a ajudar; este resultado é uma característica da base sintética, não uma regra geral.
6. **Sensibilidade do ranking.** Retirando um exemplo por vez (30 sub-bases de 29 exemplos), a acurácia leave-one-out média e o
   número de sub-bases em que cada variante foi a melhor (empates divididos) foram:

{R.tabela_md(["Variante", "LOO médio nas 30 sub-bases", "Nº de sub-bases em que foi a melhor"], [[n, pct(sens[n]['loo_medio']), R.br(sens[n]['vitorias'], 1)] for n in sens])}

   O ID3 é a melhor variante em {R.br(sens['ID3']['vitorias'], 1)} das 30 sub-bases, ou seja, o ranking é estável diante da *remoção* de um exemplo.
   Mesmo assim ele depende dos detalhes da base: em uma versão preliminar (com o E15 idêntico ao E14, isto é, um exemplo
   repetido), o C4.5 ficou à frente do ID3. A conclusão prudente é: *as quatro bases são estatisticamente próximas; a escolha
   deve considerar também critérios de engenharia do conhecimento (cobertura, legibilidade, custo de interação).*

### Escolha: base de regras do **ID3** ({len(id3['regras'])} regras)

Escolho a base do **ID3** como base de conhecimento do sistema de análise de risco de crédito:

* melhor desempenho estimado em dados novos (LOO {pct(comp['ID3']['acc_loo'])}; CV {pct(comp['ID3']['acc_cv_media'])}) e também o maior LOO médio na
  análise de sensibilidade;
* **cobertura total** do espaço de entradas ({comp['ID3']['cobertas']}/216): o sistema sempre consegue concluir sobre qualquer cliente;
* regras curtas e só com igualdades *atributo = valor*, fáceis de ler, validar com o gerente do banco e de usar nas explicações
  "Por quê?" e "Como?" do shell (Questão 5);
* árvore rasa (profundidade {comp['ID3']['profundidade']}): em média {R.br(comp['ID3']['perguntas_medias'], 2)} perguntas ao usuário por consulta, bem menos que o CART
  ({R.br(comp['CART']['perguntas_medias'], 2)});
* 100 % de acerto no treino e coerência com o conhecimento do domínio: a raiz é *Renda*, e *História de Crédito* decide os
  casos de renda média e alta, como na árvore clássica de Luger para o problema de risco de crédito.

**Ressalvas.** (a) Com 30 exemplos, as diferenças entre as bases estão dentro do desvio-padrão da validação (e o ranking mudou ao trocar um único exemplo numa versão preliminar); (b) a base é sintética; (c) o ID3 tem viés por atributos com muitos valores, e em bases com atributos
do tipo "identificador" ele falharia — o C4.5 seria então a escolha mais segura; (d) em um sistema real, convém combinar a
base induzida com a revisão de um especialista.

## Reprodução

```bash
python -m q1.executar        # regenera todos os arquivos desta questão
python -m unittest discover -s tests -t .   # testes automáticos
```
"""
    return md


if __name__ == "__main__":
    main()
