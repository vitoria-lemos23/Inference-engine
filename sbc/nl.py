"""Interpretação de frases em português para o diálogo com o usuário.

Não usa nenhum modelo de linguagem externo: é um analisador por padrões (expressões regulares, palavras-chave
e correspondência aproximada), suficiente para comandos, respostas a perguntas e declaração de fatos.
Tudo é comparado sem acentos e sem distinguir maiúsculas de minúsculas.
"""
from __future__ import annotations

import difflib
import re

from .modelo import como_numero, norm, valores_iguais

# ====================================================================== respostas a perguntas
SIM = {"s", "sim", "yes", "y", "claro", "isso", "correto", "verdade", "verdadeiro", "positivo", "ok", "afirmativo"}
NAO = {"n", "nao", "no", "falso", "negativo", "jamais", "nunca"}
DESCONHECE = {"nao sei", "desconheco", "sei la", "nao tenho certeza", "talvez", "?", "ignoro", "nao conheco",
              "nao lembro", "sem informacao", "nao tenho essa informacao", "desconhecido", "indiferente"}
CANCELA = {"cancelar", "cancela", "sair", "parar", "abortar", "desistir", "chega", "voltar"}


def _numero(texto):
    """Primeiro número do texto (aceita 1.500, 1500, 1,5, R$ 2.000,50)."""
    m = re.search(r"-?\d+(?:[.,]\d+)*", texto)
    if not m:
        return None
    s = m.group(0)
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        n = float(s)
    except ValueError:
        return None
    return int(n) if n == int(n) else n


def melhor_opcao(texto, opcoes, limiar=0.78):
    """Escolhe, entre `opcoes`, a que o texto designa: número da lista, igualdade, contido ou parecido."""
    t = norm(texto)
    if not t:
        return None
    if re.fullmatch(r"\d+", t) and 1 <= int(t) <= len(opcoes):
        return opcoes[int(t) - 1]
    for o in opcoes:
        if norm(o) == t:
            return o
    # a opção aparece inteira dentro da frase ("acho que é acima de $35k") -> a mais longa
    cont = [o for o in opcoes if norm(o) and re.search(r"(?<!\w)" + re.escape(norm(o)) + r"(?!\w)", t)]
    if cont:
        return max(cont, key=lambda o: len(norm(o)))
    # a frase está dentro da opção ("desconhecida" ~ "desconhec")
    cont = [o for o in opcoes if len(t) >= 3 and t in norm(o)]
    if len(cont) == 1:
        return cont[0]
    # parecido (erro de digitação)
    cand = difflib.get_close_matches(t, [norm(o) for o in opcoes], n=1, cutoff=limiar)
    if cand:
        for o in opcoes:
            if norm(o) == cand[0]:
                return o
    return None


def interpretar_resposta(texto, opcoes=None, tipo="texto"):
    """Interpreta a resposta do usuário a uma pergunta.
    Retorna ('valor', v) | ('desconhecido',) | ('por_que',) | ('como',) | ('cancelar',) | ('invalido', mensagem)."""
    t = norm(texto)
    if not t:
        return ("invalido", "Resposta vazia.")
    if opcoes:                                       # uma opção escrita por extenso tem precedência (ex.: «indiferente»)
        for o in opcoes:
            if norm(o) == t:
                return ("valor", o)
    if re.match(r"^(por ?que|porque|pq|por quê)\b", t) and not re.match(r"^por que nao", t):
        return ("por_que",)
    if t in ("como", "como?", "explique", "explicar"):
        return ("como",)
    if t in DESCONHECE or any(t.startswith(p) for p in ("nao sei", "nao tenho certeza", "desconheco")):
        return ("desconhecido",)
    if t in CANCELA:
        return ("cancelar",)
    if tipo == "numero":
        n = _numero(texto)
        if n is None:
            return ("invalido", "Preciso de um número (por exemplo: 3500).")
        return ("valor", n)
    if opcoes:
        bool_op = {norm(o) for o in opcoes} <= {"sim", "nao"} and len(opcoes) == 2
        if bool_op:
            palavras = set(t.split())
            if t in SIM or (palavras & SIM and not palavras & NAO):
                return ("valor", next(o for o in opcoes if norm(o) == "sim"))
            if t in NAO or (palavras & NAO):
                return ("valor", next(o for o in opcoes if norm(o) == "nao"))
        o = melhor_opcao(texto, opcoes)
        if o is not None:
            return ("valor", o)
        listado = ", ".join(str(x) for x in opcoes)
        return ("invalido", f"Não reconheci essa resposta. Opções: {listado}.")
    n = _numero(texto) if tipo == "numero" else None
    return ("valor", n if n is not None else texto.strip())


# ====================================================================== fatos em linguagem natural
_LIGACAO = r"(?:e|eh|esta|estao|sao|foi|era|seria|fica|=|:|igual a|igual|como|tem|possui|com)"


def _variavel_no_texto(t, base):
    """Variável citada em `t` (já normalizado): retorna (variavel, trecho_restante) ou (None, t)."""
    melhor = None
    for v in base.variaveis.values():
        for nome in {norm(v.rotulo), norm(v.nome), norm(v.nome.replace("_", " "))}:
            if not nome:
                continue
            m = re.search(r"(?<!\w)" + re.escape(nome) + r"(?!\w)", t)
            if m and (melhor is None or len(nome) > melhor[0]):
                melhor = (len(nome), v, m)
    if melhor is None:
        return None, t
    _, v, m = melhor
    return v, (t[:m.start()] + " " + t[m.end():]).strip()


def _mencoes(t, base):
    """Todas as menções a variáveis em `t` (já normalizado): [(inicio, fim, variavel)], sem sobreposição."""
    cand = []
    for v in base.variaveis.values():
        for nome in {norm(v.rotulo), norm(v.nome), norm(v.nome.replace("_", " "))}:
            if nome:
                for m in re.finditer(r"(?<!\w)" + re.escape(nome) + r"(?!\w)", t):
                    cand.append((m.start(), m.end(), v))
    cand.sort(key=lambda c: -(c[1] - c[0]))            # nomes mais longos primeiro
    escolhidas = []
    for i, f, v in cand:
        if all(f <= i2 or i >= f2 for i2, f2, _ in escolhidas):
            escolhidas.append((i, f, v))
    return sorted(escolhidas, key=lambda c: c[0])


_CONECTORES_INI = re.compile(r"^(?:(?:o|a|os|as|de|da|do|que|sendo|seja|fica|ficou)\s+)*"
                             r"(?:" + _LIGACAO + r"\s+)?(?:(?:o|a|um|uma|de|do|da)\s+)*")
_CONECTORES_FIM = re.compile(r"(?:\s*[,;.]|(?:^|\s+)(?:e|ou|mas|que|porque|entao))+\s*$")


_NEG_ANTES = re.compile(r"(?:^|\s)(?:nao|nem|sem|nunca)\s+(?:(?:o|a|os|as|e|tem|possui|ter)\s+)*$")
_NEG_FIM = re.compile(r"(?:^|\s)(?:nao|nem|sem|nunca)(?:\s+(?:o|a|os|as|e|tem|possui|ter))*\s*$")


def _booleana(v):
    return len(v.valores) == 2 and {norm(x) for x in v.valores} == {"sim", "nao"}


def extrair_fatos(texto, base):
    """Extrai fatos 'variável = valor' de uma frase. Retorna lista de (nome_da_variável, valor).
    Cada menção a uma variável é seguida do seu valor, até a próxima menção; variáveis sim/não aceitam
    negação antes da menção («não voa»). Valores citados sozinhos ("android") também são reconhecidos."""
    t = norm(texto)
    ms = _mencoes(t, base)
    negados = [bool(_NEG_ANTES.search(t[:i])) for i, _, _ in ms]
    fatos, vistos = [], set()
    for k, (i, f, v) in enumerate(ms):
        fim = ms[k + 1][0] if k + 1 < len(ms) else len(t)
        segmento = t[f:fim]
        if k + 1 < len(ms) and negados[k + 1]:
            segmento = _NEG_FIM.sub("", segmento)          # a negação pertence à próxima menção
        resto = _CONECTORES_FIM.sub("", segmento.strip()).strip()
        resto = _CONECTORES_INI.sub("", resto).strip()
        resto = _CONECTORES_FIM.sub("", resto).strip()
        valor = None
        if _booleana(v):
            op = {norm(x): x for x in v.valores}
            palavras = set(resto.split())
            if resto and (resto in SIM or (palavras & SIM and not palavras & NAO)):
                valor = op["sim"]
            elif resto and (resto in NAO or palavras & NAO):
                valor = op["nao"]
            elif not resto:
                valor = op["nao"] if negados[k] else op["sim"]
        elif resto:
            if v.tipo == "numero":
                valor = _numero(resto)
            elif v.valores:
                valor = melhor_opcao(resto, [str(x) for x in v.valores], limiar=0.8)
            else:
                valor = resto
        if valor is not None and v.nome not in vistos:
            fatos.append((v.nome, valor))
            vistos.add(v.nome)
    # valores citados sem o nome da variável, se pertencerem a uma única variável
    for v in base.variaveis.values():
        if v.nome in vistos or v.tipo == "numero" or _booleana(v):
            continue
        for val in v.valores:
            nv = norm(val)
            if len(nv) < 3 or not re.search(r"(?<!\w)" + re.escape(nv) + r"(?!\w)", t):
                continue
            donos = [w for w in base.variaveis.values()
                     if any(norm(x) == nv for x in w.valores)]
            if len(donos) == 1:
                fatos.append((v.nome, val))
                vistos.add(v.nome)
                break
    return fatos


def escolher_variavel(texto, base):
    """Variável (meta) citada no texto, ou None."""
    v, _ = _variavel_no_texto(norm(texto), base)
    return v


# ====================================================================== comandos
def reconhecer_comando(texto, base):
    """Classifica uma linha do usuário. Retorna (intenção, argumentos: dict)."""
    bruto = texto.strip()
    t = norm(bruto)
    if not t:
        return "vazio", {}
    if re.match(r"^(sair|quit|exit|fim|tchau|encerrar|adeus)\b", t):
        return "sair", {}
    if re.match(r"^(ajuda|help|comandos|\?+$|o que (voce )?(faz|sabe fazer|pode fazer))", t):
        return "ajuda", {}
    # edição ---------------------------------------------------------------------------------------
    m = re.match(r"^(?:adicionar|adicione|criar|crie|nova|inserir|insira|incluir|inclua)\s+(?:uma\s+)?regra\s*(?:(r\w+(?:\.\d+)?)\s*)?[:\-]?\s*(.*)$", bruto, re.I | re.S)
    if m and re.match(r"^\s*se\b", m.group(2), re.I):
        return "add_regra", {"id": m.group(1), "texto": m.group(2).strip()}
    if re.match(r"^\s*se\b.*\b(?:entao|então)\b", bruto, re.I | re.S):
        return "add_regra", {"id": None, "texto": bruto}
    m = re.match(r"^(?:remover|remova|excluir|exclua|apagar|apague|deletar)\s+(?:a\s+)?regra\s+(\S+)", bruto.strip(), re.I)
    if m:
        return "rem_regra", {"id": m.group(1)}
    m = re.match(r"^(?:editar|edite|alterar|altere|trocar|substituir)\s+(?:a\s+)?regra\s+(\S+)\s*[:\-]?\s*(se\b.*)$", bruto, re.I | re.S)
    if m:
        return "edit_regra", {"id": m.group(1), "texto": m.group(2)}
    m = re.match(r"^(?:adicionar|adicione|criar|crie|inserir|incluir)\s+(?:um\s+)?fato\s*[:\-]?\s*(.+)$", bruto, re.I)
    if m:
        return "add_fato", {"texto": m.group(1).strip()}
    m = re.match(r"^(?:remover|remova|excluir|apagar)\s+(?:o\s+)?fato\s*[:\-]?\s*(.+)$", bruto, re.I)
    if m:
        return "rem_fato", {"nome": m.group(1).strip()}
    if re.match(r"^(modo editor|editor|editar (a )?base|editar$)", t):
        return "editor", {}
    if re.match(r"^(validar|valide|verificar (a )?base|checar|conferir (a )?base)", t):
        return "validar", {}
    m = re.match(r"^(?:salvar|salve|gravar|grave)(?:\s+(?:a\s+)?base)?(?:\s+(?:em|como|no arquivo)?\s*(.+))?$", bruto, re.I)
    if m:
        return "salvar", {"arquivo": (m.group(1) or "").strip() or None}
    if re.match(r"^(listar|liste|mostrar|mostre|quais sao as|ver)\s+(as\s+)?(bases|exemplos)|^(bases|exemplos)$", t):
        return "bases", {}
    m = re.match(r"^(?:carregar|carregue|abrir|abra|usar|use|trocar para|mudar para)\s+(?:a\s+)?(?:base\s+)?(?:de\s+)?(.+)$", bruto, re.I)
    if m and not re.match(r"^(encadeamento|modo)", norm(m.group(1))):
        return "carregar", {"nome": m.group(1).strip()}
    # explicações --------------------------------------------------------------------------------------
    m = re.match(r"^por ?que nao\s+(.+)$", t)
    if m:
        return "por_que_nao", {"texto": m.group(1)}
    if re.match(r"^(por ?que|porque|pq)\b", t):
        return "por_que", {}
    m = re.match(r"^como\s+(?:voce\s+)?(?:chegou|concluiu|descobriu|sabe|soube|deduziu|obteve|determinou|provou|inferiu)\s*(?:a\s+|na\s+|em\s+|que\s+|ao\s+)?(?:conclusao\s+)?(?:de\s+|que\s+|a\s+)?(.*)$", t)
    if m:
        return "como", {"texto": m.group(1).strip()}
    if re.match(r"^como\b", t):
        return "como", {"texto": re.sub(r"^como\s*", "", t).strip()}
    if re.match(r"^(trilha|historico|log|passo a passo|rastro|trace)", t):
        return "trilha", {}
    # estado e informação --------------------------------------------------------------------------------
    if re.match(r"^(o que (voce )?sabe|fatos|memoria|mostrar fatos|mostre os fatos|estado|situacao)", t):
        return "fatos", {}
    m = re.match(r"^(?:mostrar|mostre|ver|exibir|explique|qual e)\s+(?:a\s+)?regra\s+(\S+)", bruto.strip(), re.I)
    if m:
        return "regra", {"id": m.group(1)}
    m = re.match(r"^(r\d+(?:\.\d+)?)$", t)
    if m:
        return "regra", {"id": m.group(1)}
    m = re.match(r"^regra\s+(\S+)$", t)
    if m:
        return "regra", {"id": m.group(1)}
    if re.match(r"^(regras|listar regras|liste (as )?regras|mostrar regras|mostre (as )?regras|quais (sao )?as regras|ver regras|base de regras)", t):
        return "regras", {}
    if re.match(r"^(variaveis|atributos|listar variaveis|quais variaveis)", t):
        return "variaveis", {}
    if re.match(r"^(sobre|info|informacoes|descreva|descricao|quem (e )?voce|o que e isso)", t):
        return "sobre", {}
    if re.match(r"^(limpar|limpe|reiniciar|reinicie|recomecar|nova consulta|esquecer tudo|zerar|resetar)", t):
        return "limpar", {}
    m = re.search(r"\b(?:modo|encadeamento|usar|use|chaining)\b.*\b(frente|forward|tras|backward|misto|hibrido|mixed)\b", t)
    if m and not re.search(r"\b(consultar|avaliar)\b", t):
        return "modo", {"modo": _modo(m.group(1))}
    if re.match(r"^(frente|forward|tras|backward|misto|hibrido|mixed)$", t):
        return "modo", {"modo": _modo(t)}
    # consulta ---------------------------------------------------------------------------------------------
    gatilho = (r"^(?:consultar|consulte|iniciar|inicie|comecar|comece|avaliar|avalie|descobrir|descubra|determinar|determine|"
               r"diagnosticar|diagnostique|classificar|classifique|recomendar|recomende|analisar|analise|"
               r"quero (?:saber|descobrir|avaliar|ver|diagnosticar|classificar)|gostaria de (?:saber|avaliar)|"
               r"preciso (?:saber|avaliar|descobrir)|vamos|qual (?:e|seria|sera|eh)|quais (?:sao|seriam)|me diga|diga)\b")
    if re.match(gatilho, t):
        v = escolher_variavel(bruto, base)
        modo = None
        mm = re.search(r"\b(frente|forward|tras|backward|misto|hibrido|mixed)\b", t)
        if mm:
            modo = _modo(mm.group(1))
        return "consultar", {"meta": v.nome if v else None, "modo": modo}
    # fato informado -----------------------------------------------------------------------------------------
    fatos = extrair_fatos(bruto, base)
    if fatos:
        return "informar", {"fatos": fatos}
    v = escolher_variavel(bruto, base)
    if v is not None and v.nome in base.metas:
        return "consultar", {"meta": v.nome, "modo": None}
    return "desconhecido", {}


def _modo(p):
    p = norm(p)
    if p in ("frente", "forward"):
        return "frente"
    if p in ("tras", "backward"):
        return "tras"
    return "misto"


AJUDA = """Comandos (escreva em linguagem natural; os exemplos abaixo são só uma amostra):

  CONSULTAR
    consultar [meta]  ·  avaliar o risco  ·  qual é o diagnóstico?  ·  descubra o animal
    modo para frente | modo para trás | modo misto     (escolhe o tipo de encadeamento)

  INFORMAR DADOS
    a renda é acima de $35k  ·  histórico de crédito = Boa  ·  idade é 25
    o que você sabe?   (mostra os fatos)       limpar   (nova consulta)

  EXPLICAÇÕES
    por quê?        (durante uma pergunta: por que o sistema pergunta isso; repita para subir um nível)
    como?  ·  como você concluiu o risco?      (como uma conclusão foi obtida)
    por que não risco = baixo?                 (por que algo NÃO foi concluído)
    trilha          (histórico passo a passo da inferência)

  BASE DE CONHECIMENTO
    regras  ·  regra R3  ·  variáveis  ·  sobre  ·  bases (lista exemplos)  ·  carregar animais
    adicionar regra: SE a = x E b > 3 ENTÃO c = y       remover regra R3       editar regra R3: SE ... ENTÃO ...
    adicionar fato: a = b        remover fato a         validar        salvar [arquivo]       editor (modo guiado)

  sair

Ao responder a uma pergunta você pode digitar o número da opção, o valor, 'não sei', 'por quê?' ou 'cancelar'."""
