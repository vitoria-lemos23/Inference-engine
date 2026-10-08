"""Tabela clássica de risco de crédito (Luger, 14 exemplos), usada como caso de verificação."""
from collections import OrderedDict

from ia.base import Base

ATRIBUTOS = ["História de Crédito", "Dívida", "Garantia", "Renda"]
LINHAS = """Alto,Ruim,Alta,Nenhuma,$0 a $15k
Alto,Desconhecida,Alta,Nenhuma,$15 a $35k
Moderado,Desconhecida,Baixa,Nenhuma,$15 a $35k
Alto,Desconhecida,Baixa,Nenhuma,$0 a $15k
Baixo,Desconhecida,Baixa,Nenhuma,Acima de $35k
Baixo,Desconhecida,Baixa,Adequada,Acima de $35k
Alto,Ruim,Baixa,Nenhuma,$0 a $15k
Moderado,Ruim,Baixa,Adequada,Acima de $35k
Baixo,Boa,Baixa,Nenhuma,Acima de $35k
Baixo,Boa,Alta,Adequada,Acima de $35k
Alto,Boa,Alta,Nenhuma,$0 a $15k
Moderado,Boa,Alta,Nenhuma,$15 a $35k
Baixo,Boa,Alta,Nenhuma,Acima de $35k
Alto,Ruim,Alta,Nenhuma,$15 a $35k""".splitlines()


def base_luger():
    linhas = []
    for i, r in enumerate(LINHAS, 1):
        c = r.split(",")
        d = {"ID": f"E{i}", "Risco": c[0]}
        d.update(zip(ATRIBUTOS, c[1:]))
        linhas.append(d)
    doms = OrderedDict((a, sorted({l[a] for l in linhas})) for a in ATRIBUTOS)
    return Base(list(ATRIBUTOS), "Risco", ["Baixo", "Moderado", "Alto"], linhas, dict(doms), "ID")
