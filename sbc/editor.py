"""Editor da base de conhecimento: criar, editar e excluir regras, fatos e variáveis; validar a base."""
from __future__ import annotations

from dataclasses import dataclass

from .modelo import BaseConhecimento, Variavel, fmt_valor, norm, valores_iguais
from .parser import ErroSintaxe, parse_fato, parse_regra


@dataclass
class Problema:
    nivel: str            # 'erro' | 'aviso'
    mensagem: str
    regra: str | None = None

    def __str__(self):
        return f"[{self.nivel.upper()}] {self.mensagem}"


class Editor:
    def __init__(self, base: BaseConhecimento):
        self.base = base

    # ================================================================== regras
    def adicionar_regra(self, texto, rid=None, prioridade=0, explicacao=""):
        """Aceita 'SE ... ENTÃO ...' (com OU gera várias regras). Retorna a lista de regras criadas."""
        rid = rid or self.base.proximo_id_regra()
        if self.base.regra(rid):
            raise ValueError(f"já existe uma regra com o identificador {rid}")
        novas = parse_regra(texto, rid, prioridade, explicacao)       # pode levantar ErroSintaxe
        for r in novas:
            if self.base.regra(r.id):
                raise ValueError(f"já existe uma regra com o identificador {r.id}")
        for r in novas:
            for c in r.condicoes:
                self._declarar(c.atributo, c.valor if c.operador in ("=", "!=", "em") else None)
            for c in r.conclusoes:
                self._declarar(c.atributo, c.valor)
            self.base.regras.append(r)
        return novas

    def _declarar(self, atributo, valor):
        existia = atributo in self.base.variaveis
        self.base.garantir_variavel(atributo, valor)
        return not existia

    def substituir_regra(self, rid, texto):
        r = self.base.regra(rid)
        if r is None:
            raise KeyError(f"regra inexistente: {rid}")
        pos = self.base.regras.index(r)
        novas = parse_regra(texto, r.id, r.prioridade, r.explicacao)
        for x in novas[1:]:
            if self.base.regra(x.id):
                raise ValueError(f"já existe uma regra com o identificador {x.id}")
        self.base.regras[pos:pos + 1] = novas
        for x in novas:
            for c in x.condicoes + x.conclusoes:
                self._declarar(c.atributo, getattr(c, "valor", None))
        return novas

    def remover_regra(self, rid):
        r = self.base.regra(rid)
        if r is None:
            raise KeyError(f"regra inexistente: {rid}")
        self.base.regras.remove(r)
        return r

    def mover_regra(self, rid, posicao):
        r = self.remover_regra(rid)
        self.base.regras.insert(max(0, min(posicao - 1, len(self.base.regras))), r)

    # ================================================================== fatos
    def adicionar_fato(self, texto_ou_par):
        a, v = parse_fato(texto_ou_par) if isinstance(texto_ou_par, str) else texto_ou_par
        v0 = self.base.variavel(a)
        a = v0.nome if v0 else a
        if v0 and v0.valores and v0.tipo != "numero":                 # usa a grafia do domínio
            v = next((x for x in v0.valores if valores_iguais(x, v)), v)
        self._declarar(a, v)
        if any(x == a and valores_iguais(y, v) for x, y in self.base.fatos):
            return a, v
        self.base.fatos.append((a, v))
        return a, v

    def remover_fato(self, atributo):
        v0 = self.base.variavel(atributo)
        a = v0.nome if v0 else atributo
        antes = len(self.base.fatos)
        self.base.fatos = [(x, y) for x, y in self.base.fatos if x != a]
        if len(self.base.fatos) == antes:
            raise KeyError(f"não há fato inicial para {atributo}")

    # ================================================================== variáveis e metas
    def definir_variavel(self, nome, **campos):
        v = self.base.variavel(nome)
        if v is None:
            v = self.base.variaveis[nome] = Variavel(nome)
        for k, val in campos.items():
            if not hasattr(v, k):
                raise ValueError(f"campo desconhecido: {k}")
            if val is not None:
                setattr(v, k, val)
        if "rotulo" in campos and not campos["rotulo"]:
            v.rotulo = v.nome
        return v

    def remover_variavel(self, nome):
        v = self.base.variavel(nome)
        if v is None:
            raise KeyError(f"variável inexistente: {nome}")
        usada = [r.id for r in self.base.regras if any(c.atributo == v.nome for c in r.condicoes + r.conclusoes)]
        if usada:
            raise ValueError(f"a variável «{v.rotulo}» é usada pelas regras {', '.join(usada)}; remova-as antes")
        del self.base.variaveis[v.nome]
        self.base.fatos = [(a, x) for a, x in self.base.fatos if a != v.nome]
        self.base.metas = [m for m in self.base.metas if m != v.nome]

    def definir_metas(self, nomes):
        metas = []
        for n in nomes:
            v = self.base.variavel(n)
            if v is None:
                raise KeyError(f"variável inexistente: {n}")
            metas.append(v.nome)
        self.base.metas = metas

    # ================================================================== validação
    def validar(self):
        b, P = self.base, []
        ids = {}
        for r in b.regras:
            if norm(r.id) in ids:
                P.append(Problema("erro", f"identificador de regra repetido: {r.id}", r.id))
            ids[norm(r.id)] = r
            if not r.conclusoes:
                P.append(Problema("erro", f"a regra {r.id} não tem conclusão", r.id))
        concluidos = {c.atributo for r in b.regras for c in r.conclusoes}
        com_fato = {a for a, _ in b.fatos}
        # domínios
        for r in b.regras:
            for c in r.condicoes:
                v = b.variaveis.get(c.atributo)
                if v and v.valores and v.tipo != "numero" and c.operador in ("=", "!=", "em"):
                    vals = c.valor if c.operador == "em" else (c.valor,)
                    for x in vals:
                        if not any(valores_iguais(x, y) for y in v.valores):
                            P.append(Problema("aviso", f"regra {r.id}: o valor «{fmt_valor(x)}» não está entre os "
                                                       f"valores declarados de «{v.rotulo}»", r.id))
            for c in r.conclusoes:
                v = b.variaveis.get(c.atributo)
                if v and v.valores and v.tipo != "numero" and not any(valores_iguais(c.valor, y) for y in v.valores):
                    P.append(Problema("aviso", f"regra {r.id}: o valor «{fmt_valor(c.valor)}» não está entre os "
                                               f"valores declarados de «{v.rotulo}»", r.id))
        # regras que nunca disparam
        for r in b.regras:
            for c in r.condicoes:
                if c.atributo not in concluidos and c.atributo not in com_fato and not b.perguntavel(c.atributo):
                    P.append(Problema("aviso", f"regra {r.id}: «{b.rotulo(c.atributo)}» não é perguntável, nem "
                                               f"concluído por regra, nem fato; a regra nunca dispara", r.id))
        # regras duplicadas / contraditórias
        for i, r in enumerate(b.regras):
            for s in b.regras[i + 1:]:
                if {self._chave(c) for c in r.condicoes} == {self._chave(c) for c in s.condicoes}:
                    mesmas = {(c.atributo, norm(c.valor)) for c in r.conclusoes} == {(c.atributo, norm(c.valor)) for c in s.conclusoes}
                    if mesmas:
                        P.append(Problema("aviso", f"as regras {r.id} e {s.id} são idênticas", s.id))
                    else:
                        for c in r.conclusoes:
                            for d in s.conclusoes:
                                var = b.variaveis.get(c.atributo)
                                if c.atributo == d.atributo and not valores_iguais(c.valor, d.valor) \
                                        and not (var and var.multivalorada):
                                    P.append(Problema("aviso", f"as regras {r.id} e {s.id} têm as mesmas condições e "
                                                               f"concluem valores diferentes para «{b.rotulo(c.atributo)}»", s.id))
        # ciclos entre variáveis derivadas
        dep = {}
        for r in b.regras:
            for c in r.conclusoes:
                dep.setdefault(c.atributo, set()).update(x.atributo for x in r.condicoes)
        ciclo = self._ciclo(dep)
        if ciclo:
            P.append(Problema("aviso", "dependência circular entre variáveis: " + " → ".join(b.rotulo(a) for a in ciclo)))
        # metas
        for m in b.metas:
            if m not in b.variaveis:
                P.append(Problema("erro", f"a meta «{m}» não é uma variável declarada"))
            elif m not in concluidos and not b.perguntavel(m):
                P.append(Problema("aviso", f"a meta «{b.rotulo(m)}» não é concluída por nenhuma regra"))
        # variáveis sem uso
        usadas = {c.atributo for r in b.regras for c in r.condicoes + r.conclusoes} | com_fato | set(b.metas)
        for n, v in b.variaveis.items():
            if n not in usadas:
                P.append(Problema("aviso", f"a variável «{v.rotulo}» é declarada mas não é usada"))
        return P

    @staticmethod
    def _chave(c):
        return (c.atributo, c.operador, tuple(norm(x) for x in c.valor) if c.operador == "em" else norm(c.valor), c.negada)

    @staticmethod
    def _ciclo(dep):
        estado, pilha = {}, []

        def dfs(a):
            estado[a] = 1
            pilha.append(a)
            for b in dep.get(a, ()):
                if estado.get(b) == 1:
                    return pilha[pilha.index(b):] + [b]
                if b not in estado:
                    r = dfs(b)
                    if r:
                        return r
            pilha.pop()
            estado[a] = 2
            return None

        for a in list(dep):
            if a not in estado:
                r = dfs(a)
                if r:
                    return r
        return None
