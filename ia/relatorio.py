"""Geração de material de relatório: passo a passo dos cálculos, árvores (texto/DOT/PNG), tabelas."""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from .arvores import No, caminho_decisao
from .regras import _mesclar

CORES = {"Baixo": "#a8e6a3", "Moderado": "#ffe08a", "Alto": "#f4a0a0"}
PALETA = ["#a8d4f0", "#f7c59f", "#c9b6e4", "#b5e3b5", "#f4a0a0", "#ffe08a", "#d0d0d0"]


# ====================================================================== formatação
def br(x, nd=4):
    """Número com vírgula decimal (padrão brasileiro)."""
    return f"{x:.{nd}f}".replace(".", ",")


def cont_txt(contagem):
    """'B=2, M=0, A=1' usando as iniciais das classes."""
    return ", ".join(f"{k[0]}={v}" for k, v in contagem.items())


def cond_txt(a, vals):
    return f"{a} = {vals[0]}" if len(vals) == 1 else f"{a} ∈ {{{', '.join(vals)}}}"


def caminho_txt(caminho):
    """Condições do caminho, já fundidas (várias divisões sobre o mesmo atributo viram uma só)."""
    return " E ".join(cond_txt(a, v) for a, v in _mesclar(caminho)) if caminho else "(raiz)"


def tabela_md(cabecalho, linhas, alinhar=None):
    alinhar = alinhar or ["---"] * len(cabecalho)
    out = ["| " + " | ".join(cabecalho) + " |", "| " + " | ".join(alinhar) + " |"]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


def tabela_base_md(base, colunas_extra=None):
    cab = [base.id_col] + list(base.atributos) + [base.classe]
    linhas = [[l[base.id_col]] + [l[a] for a in base.atributos] + [f"**{l[base.classe]}**"] for l in base.linhas]
    return tabela_md(cab, linhas)


# ====================================================================== fórmulas
def _frac(c, n):
    return f"{c}/{n}"


def expr_entropia(contagem, nome="H"):
    """Ex.: H = −(3/5)·log₂(3/5) − (2/5)·log₂(2/5) = 0,9710"""
    n = sum(contagem.values())
    termos = [c for c in contagem.values() if c > 0]
    if len(termos) <= 1:
        return f"{nome} = 0 (nó puro)"
    partes = " ".join(f"− ({_frac(c, n)})·log₂({_frac(c, n)})" for c in termos)
    val = -sum((c / n) * math.log2(c / n) for c in termos)
    return f"{nome} = {partes} = {br(val)}"


def expr_gini(contagem, nome="G"):
    n = sum(contagem.values())
    termos = [c for c in contagem.values() if c > 0]
    if len(termos) <= 1:
        return f"{nome} = 0 (nó puro)"
    s = " − ".join(f"({_frac(c, n)})²" for c in termos)
    val = 1 - sum((c / n) ** 2 for c in termos)
    return f"{nome} = 1 − {s} = {br(val)}"


def expr_ganho(passo, av):
    n = sum(passo.contagem.values())
    partes = " + ".join(f"({r['n']}/{n})·{br(r['entropia'])}" for r in av["ramos"])
    return (f"Ganho({av['atributo']}) = {br(passo.impureza)} − [{partes}] = "
            f"{br(passo.impureza)} − {br(av['entropia_condicional'])} = **{br(av['ganho'])}**")


def expr_razao(av):
    n = sum(r["n"] for r in av["ramos"])
    termos = " ".join(f"− ({r['n']}/{n})·log₂({r['n']}/{n})" for r in av["ramos"])
    return (f"InfoDivisão({av['atributo']}) = {termos} = {br(av['info_divisao'])}; "
            f"RazãoGanho = {br(av['ganho'])} / {br(av['info_divisao'])} = **{br(av['razao_ganho'])}**")


# ====================================================================== passo a passo
def passo_a_passo_md(base, passos, algoritmo, titulo=None):
    """Markdown com TODOS os cálculos de cada nó da construção."""
    alg = algoritmo.upper()
    cart = alg == "CART"
    out = [f"# {titulo or 'Construção passo a passo'} — {alg}", ""]
    out.append("Convenções: contagens por classe escritas como **B**=Baixo, **M**=Moderado, **A**=Alto; "
               "log₂ é o logaritmo na base 2 e 0·log₂0 = 0. Empates são resolvidos pela ordem das colunas "
               "da base (e, para a classe de uma folha, pela classe mais grave).")
    out.append("")
    for p in passos:
        out.append(f"## Nó {p.no_id}  —  {caminho_txt(p.caminho)}")
        out.append("")
        out.append(f"Exemplos ({len(p.ids)}): {', '.join(p.ids)}  ")
        out.append(f"Distribuição: {cont_txt(p.contagem)}  ")
        out.append(expr_gini(p.contagem, "Gini(S)") if cart else expr_entropia(p.contagem, "H(S)"))
        out.append("")
        if p.motivo == "puro":
            out.append(f"➡ **Folha** (nó puro): classe = **{max(p.contagem, key=p.contagem.get)}**.")
            out.append("")
            continue
        if p.motivo == "sem atributos":
            out.append("➡ **Folha**: não há atributo que ainda separe os exemplos; classe = maioria.")
            out.append("")
            continue
        if cart:
            _passo_cart(out, p)
        else:
            _passo_multi(out, p, alg, detalhar_todos=(p.no_id == 1))
        if p.motivo == "sem ganho":
            out.append("➡ **Folha**: nenhuma divisão reduz a impureza; classe = maioria.")
        out.append("")
    return "\n".join(out)


def _passo_multi(out, p, alg, detalhar_todos):
    c45 = alg == "C4.5"
    cab = ["Atributo", "Divisão (valor → B, M, A ; H)", "H(S∣A)", "Ganho"]
    if c45:
        cab += ["InfoDivisão", "Razão de ganho", "Ganho ≥ média?"]
    linhas = []
    for av in p.candidatos:
        div = "<br>".join(f"{r['valor']} → {cont_txt(r['contagem'])} ; H={br(r['entropia'], 3)}" for r in av["ramos"])
        l = [av["atributo"], div, br(av["entropia_condicional"]), br(av["ganho"])]
        if c45:
            l += [br(av["info_divisao"]), br(av["razao_ganho"]), "sim" if av["elegivel"] else "não"]
        linhas.append(l)
    out.append(tabela_md(cab, linhas))
    out.append("")
    if c45:
        out.append(f"Ganho médio dos candidatos = {br(p.detalhe['ganho_medio'])}. Só concorrem os atributos com "
                   f"ganho ≥ média; entre eles vence a maior **razão de ganho**.")
        out.append("")
    alvo = [av for av in p.candidatos] if detalhar_todos else [av for av in p.candidatos if av["atributo"] == p.escolhido]
    if alvo:
        out.append("Cálculos detalhados" + (" (todos os atributos, nó raiz):" if detalhar_todos else f" do atributo escolhido ({p.escolhido}):"))
        out.append("")
        for av in alvo:
            out.append(f"- {expr_ganho(p, av)}")
            if c45:
                out.append(f"  - {expr_razao(av)}")
        out.append("")
    if p.escolhido:
        crit = "razão de ganho" if c45 else "ganho de informação"
        chave = "razao_ganho" if c45 else "ganho"
        esc = next(a for a in p.candidatos if a["atributo"] == p.escolhido)
        empates = [av["atributo"] for av in p.candidatos if av["atributo"] != p.escolhido
                   and abs(av[chave] - esc[chave]) < 1e-9 and (not c45 or av["elegivel"])]
        nota = f" (empate com {', '.join(empates)}; desempate pela ordem das colunas)" if empates else ""
        out.append(f"➡ **Atributo escolhido: {p.escolhido}** (maior {crit}){nota}.")


def _passo_cart(out, p):
    for av in p.candidatos:
        out.append(f"**{av['atributo']}** — partições binárias testadas:")
        out.append("")
        cab = ["Divisão (sim vs. não)", "n (sim vs. não)", "Gini sim", "Gini não", "Gini ponderado", "Redução"]
        linhas = []
        for q in av["particoes"]:
            marca = " ✔" if q is av["melhor"] else ""
            linhas.append([f"{{{', '.join(q['esq'])}}} vs. {{{', '.join(q['dir'])}}}{marca}",
                           f"{q['n_esq']} vs. {q['n_dir']}",
                           f"{br(q['gini_esq'])} ({cont_txt(q['cont_esq'])})",
                           f"{br(q['gini_dir'])} ({cont_txt(q['cont_dir'])})",
                           br(q["gini_ponderado"]), br(q["delta"])])
        out.append(tabela_md(cab, linhas))
        out.append("")
    if p.escolhido:
        q = p.detalhe["particao"]
        n = len(p.ids)
        out.append(f"➡ **Divisão escolhida: {p.escolhido} ∈ {{{', '.join(q['esq'])}}}?**  "
                   f"Gini ponderado = ({q['n_esq']}/{n})·{br(q['gini_esq'])} + ({q['n_dir']}/{n})·{br(q['gini_dir'])} "
                   f"= **{br(q['gini_ponderado'])}** (redução de {br(q['delta'])}).")


# ====================================================================== árvore em texto
def arvore_texto(no, ind=""):
    linhas = []

    def rec(n, pref):
        for i, (rot, vals, f) in enumerate(n.ramos):
            ultimo = i == len(n.ramos) - 1
            ramo, cont = ("└─ " if ultimo else "├─ "), ("   " if ultimo else "│  ")
            op = "=" if len(vals) == 1 else "∈"
            lbl = vals[0] if len(vals) == 1 else "{" + ", ".join(vals) + "}"
            if f.folha:
                linhas.append(f"{pref}{ramo}{n.atributo} {op} {lbl}  ──►  {f.classe}  [{cont_txt(f.contagem)}]")
            else:
                linhas.append(f"{pref}{ramo}{n.atributo} {op} {lbl}")
                rec(f, pref + cont)
    if no.folha:
        return f"──►  {no.classe}  [{cont_txt(no.contagem)}]"
    rec(no, ind)
    return "\n".join(linhas)


# ====================================================================== DOT / PNG
def _cor(classe, classes):
    if classe in CORES:
        return CORES[classe]
    return PALETA[classes.index(classe) % len(PALETA)] if classe in classes else "#dddddd"


def arvore_dot(no, classes, titulo=""):
    linhas = ["digraph G {", '  graph [rankdir=TB, fontname="Helvetica", labelloc=t, fontsize=16, '
              f'label="{titulo}"];',
              '  node [fontname="Helvetica", fontsize=11, style="filled,rounded", shape=box];',
              '  edge [fontname="Helvetica", fontsize=10];']

    def rec(n):
        if n.folha:
            linhas.append(f'  n{n.id} [label="{n.classe}\\n({cont_txt(n.contagem)})", fillcolor="{_cor(n.classe, classes)}", shape=box];')
            return
        linhas.append(f'  n{n.id} [label="{n.atributo}?\\n(n={n.n})", fillcolor="#e8eefc", shape=ellipse, style=filled];')
        for rot, vals, f in n.ramos:
            lbl = vals[0] if len(vals) == 1 else "∈ {" + ", ".join(vals) + "}"
            linhas.append(f'  n{n.id} -> n{f.id} [label="{lbl}"];')
            rec(f)
    rec(no)
    linhas.append("}")
    return "\n".join(linhas)


def salvar_arvore(no, classes, destino_sem_ext, titulo=""):
    """Grava .dot e, se o Graphviz estiver instalado, .png e .svg. Retorna lista de arquivos."""
    destino = Path(destino_sem_ext)
    destino.parent.mkdir(parents=True, exist_ok=True)
    dot = arvore_dot(no, classes, titulo)
    arquivos = [destino.with_suffix(".dot")]
    arquivos[0].write_text(dot, encoding="utf-8")
    exe = shutil.which("dot")
    if exe:
        for fmt in ("png", "svg"):
            saida = destino.with_suffix("." + fmt)
            subprocess.run([exe, f"-T{fmt}", str(arquivos[0]), "-o", str(saida)], check=True)
            arquivos.append(saida)
    return arquivos


# ====================================================================== regras em Markdown
def regras_md(regras, nome_classe):
    cab = ["Regra", "SE ... ENTÃO ...", "Cobertura", "Confiança"]
    linhas = [[r.id, r.texto(nome_classe), f"{r.n}", f"{r.acertos}/{r.n}"] for r in regras]
    return tabela_md(cab, linhas)


def regras_texto(regras, nome_classe):
    return "\n".join(f"{r.id}: {r.texto(nome_classe)}   [cobre {r.n}, acerta {r.acertos}]" for r in regras)


def trilha_exemplo(no, exemplo):
    trilha, folha = caminho_decisao(no, exemplo)
    return caminho_txt(trilha), folha.classe
