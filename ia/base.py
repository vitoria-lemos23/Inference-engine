"""Representação simples de uma base de exemplos categórica (atributo=valor -> classe)."""
from __future__ import annotations

import csv
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class Base:
    """Conjunto de exemplos com atributos categóricos e uma coluna de classe.

    linhas   : lista de dicts {'ID': 'E1', <atributo>: valor, ..., <classe>: valor}
    dominios : ordem "natural" dos valores de cada atributo (usada para exibir tabelas)
    classes  : ordem natural das classes (da menos para a mais "grave"); o desempate de
               maioria escolhe a classe mais à direita (a mais grave -> postura conservadora).
    """

    atributos: list
    classe: str
    classes: list
    linhas: list
    dominios: dict = field(default_factory=dict)
    id_col: str = "ID"

    # ------------------------------------------------------------------ criação
    @classmethod
    def de_csv(cls, caminho, classe, id_col="ID", dominios=None, ordem_classes=None, sep=";"):
        with open(caminho, newline="", encoding="utf-8") as f:
            leitor = csv.DictReader(f, delimiter=sep)
            colunas = [c.strip() for c in leitor.fieldnames]
            linhas = [{k.strip(): (v or "").strip() for k, v in row.items()} for row in leitor]
        atributos = [c for c in colunas if c not in (classe, id_col)]
        doms = OrderedDict()
        for a in atributos:
            vistos = []
            for l in linhas:
                if l[a] not in vistos:
                    vistos.append(l[a])
            ordem = (dominios or {}).get(a)
            doms[a] = [v for v in ordem if v in vistos] + [v for v in vistos if v not in ordem] if ordem else vistos
        vistas = []
        for l in linhas:
            if l[classe] not in vistas:
                vistas.append(l[classe])
        classes = [c for c in ordem_classes if c in vistas] + [c for c in vistas if c not in (ordem_classes or [])] if ordem_classes else vistas
        return cls(atributos, classe, classes, linhas, dict(doms), id_col)

    # ------------------------------------------------------------------ utilidades
    def contar(self, linhas=None):
        """Contagem por classe (todas as classes presentes na ordem natural, mesmo com zero)."""
        linhas = self.linhas if linhas is None else linhas
        c = OrderedDict((k, 0) for k in self.classes)
        for l in linhas:
            c[l[self.classe]] += 1
        return c

    def valores(self, atributo, linhas=None):
        """Valores observados de um atributo (na ordem natural do domínio)."""
        linhas = self.linhas if linhas is None else linhas
        obs = {l[atributo] for l in linhas}
        ordem = self.dominios.get(atributo, [])
        return [v for v in ordem if v in obs] + sorted(v for v in obs if v not in ordem)

    def maioria(self, contagem):
        """Classe majoritária; empate -> a classe mais grave (última na ordem natural)."""
        melhor = None
        for i, k in enumerate(self.classes):
            if melhor is None or (contagem.get(k, 0), i) >= (contagem.get(melhor[0], 0), melhor[1]):
                melhor = (k, i)
        return melhor[0]

    def sem_linha(self, indice):
        """Base sem o exemplo de índice dado (para validação leave-one-out)."""
        return Base(self.atributos, self.classe, self.classes,
                    [l for i, l in enumerate(self.linhas) if i != indice], self.dominios, self.id_col)

    def com_linhas(self, linhas):
        return Base(self.atributos, self.classe, self.classes, list(linhas), self.dominios, self.id_col)

    def conflitos(self):
        """Exemplos com todos os atributos iguais, mas classes diferentes (base inconsistente)."""
        vistos, achados = {}, []
        for l in self.linhas:
            chave = tuple(l[a] for a in self.atributos)
            if chave in vistos and vistos[chave][self.classe] != l[self.classe]:
                achados.append((vistos[chave][self.id_col], l[self.id_col]))
            vistos.setdefault(chave, l)
        return achados

    def __len__(self):
        return len(self.linhas)
