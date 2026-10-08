"""Converte uma base de regras gerada pelas Questões 1/2/4 (JSON) em uma base de conhecimento ``.kb``.

Exemplo (gera a base de risco de crédito a partir da árvore ID3 da Questão 1):

    python -m sbc.importar --regras q1/resultados/regras_id3.json --csv q1/dados/credito_ampliado.csv \\
        --classe Risco --saida sbc/bases/credito.kb --nome "Risco de crédito (ID3)"

O resultado é um arquivo comum: o shell não "sabe" que ele veio de uma árvore de decisão.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .modelo import BaseConhecimento, Condicao, Conclusao, Regra, Variavel
from .parser import escrever_kb


def importar(regras_json, csv_path, classe, nome, descricao="", id_col="ID", dominios=None, sep=";",
             perguntas=None, ordem_classes=None):
    with open(regras_json, encoding="utf-8") as f:
        dados = json.load(f)
    with open(csv_path, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f, delimiter=sep)
        colunas = [c.strip() for c in leitor.fieldnames]
        linhas = [{k.strip(): (v or "").strip() for k, v in r.items()} for r in leitor]
    atributos = [c for c in colunas if c not in (classe, id_col)]
    base = BaseConhecimento(nome=nome, descricao=descricao, metas=[classe], estrategia="ordem")
    for a in atributos:
        vistos = []
        for l in linhas:
            if l[a] not in vistos:
                vistos.append(l[a])
        ordem = (dominios or {}).get(a, [])
        vals = [v for v in ordem if v in vistos] + [v for v in vistos if v not in ordem]
        base.variaveis[a] = Variavel(a, valores=vals, pergunta=(perguntas or {}).get(a, f"Qual é o valor de {a}?"))
    classes = []
    for l in linhas:
        if l[classe] not in classes:
            classes.append(l[classe])
    if ordem_classes:
        classes = [c for c in ordem_classes if c in classes] + [c for c in classes if c not in ordem_classes]
    base.variaveis[classe] = Variavel(classe, valores=classes, perguntavel=False,
                                      pergunta=f"Qual é o valor de {classe}?")
    for r in dados["regras"]:
        conds = []
        for a, vals in r["condicoes"]:
            conds.append(Condicao(a, "=", vals[0]) if len(vals) == 1 else Condicao(a, "em", tuple(vals)))
        expl = f"Regra extraída da árvore ({dados.get('meta', {}).get('algoritmo', '?')}): cobre {r.get('n', 0)} " \
               f"exemplo(s) do treinamento, {r.get('acertos', 0)} classificado(s) corretamente."
        base.regras.append(Regra(r["id"], conds, [Conclusao(classe, r["classe"])], 0, expl))
    return base


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--regras", required=True)
    p.add_argument("--csv", required=True)
    p.add_argument("--classe", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--nome", default="Base importada")
    p.add_argument("--descricao", default="")
    p.add_argument("--id-col", default="ID")
    p.add_argument("--sep", default=";")
    a = p.parse_args(argv)
    b = importar(a.regras, a.csv, a.classe, a.nome, a.descricao, a.id_col, sep=a.sep)
    Path(a.saida).write_text(escrever_kb(b), encoding="utf-8")
    print(f"{a.saida}: {len(b.regras)} regras, {len(b.variaveis)} variáveis")


if __name__ == "__main__":
    main()
