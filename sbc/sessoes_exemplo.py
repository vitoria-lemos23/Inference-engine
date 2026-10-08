"""Gera transcrições de sessões de exemplo em docs/exemplos_sessoes/ (execute: python -m sbc.sessoes_exemplo).

Cada sessão é um roteiro de entradas do usuário; a saída é exatamente a que o shell produz no terminal."""
from __future__ import annotations

from pathlib import Path

from .dialogo import PASTA_BASES, Dialogo
from .parser import carregar

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "exemplos_sessoes"

# (arquivo, base, modo, título, comandos, respostas por variável)
#   comandos : o que o usuário digita fora das perguntas, em ordem;
#   respostas: o que digita quando o shell pergunta sobre a variável (lista = várias tentativas em sequência,
#              p.ex. primeiro «por quê?» e depois a resposta); a última resposta da lista se repete; sem entrada => «não sei».
SESSOES = [
    ("01_credito_encadeamento_para_tras", "credito", "tras", "Encadeamento para trás com «por quê?» e «como?»",
     ["consultar", "como", "por que não risco = alto?", "trilha"],
     {"Renda": ["por quê?", "$15 a $35k"], "História de Crédito": ["por quê?", "por quê?", "Boa"],
      "Dívida": ["Baixa"]}),
    ("02_animais_encadeamento_para_frente", "animais", "frente",
     "Encadeamento para frente: fatos em linguagem natural e coleta dirigida pelos dados",
     ["o animal tem penas e não voa, vive na água", "o que você sabe?", "consultar", "como", "trilha"],
     {"anda_em_duas_patas": ["sim"], "tamanho": ["grande"], "alimentacao": ["variada"], "pescoco_longo": ["não"],
      "listras": ["não"], "manchas": ["não"], "tem_pelos": ["não"], "tem_escamas": ["não"], "pele_umida": ["não"],
      "amamenta": ["não"], "respira_por_guelras": ["não"], "nada_bem": ["não"]}),
    ("03_animais_encadeamento_misto", "animais", "misto",
     "Encadeamento misto: fatos já conhecidos + perguntas só do que falta",
     ["sei que tem pelos, amamenta e tem listras", "qual é o animal?", "como", "por que não animal = tigre?"],
     {"alimentacao": ["por quê?", "plantas"]}),
    ("04_diagnostico_pc_misto", "diagnostico_pc", "misto",
     "Diagnóstico de equipamento (misto), com respostas «não sei» e várias metas",
     ["o computador liga: não", "consultar", "como defeito", "como acao"],
     {"cheiro_queimado": ["não"], "ruido_hd": ["não"], "sistema_inicia": ["não sei"], "antivirus_detecta": ["não"],
      "erro_disco": ["não"], "imagem": ["sim"], "lentidao": ["não"], "tela_azul": ["não"], "temperatura": ["55"],
      "reinicia_sozinho": ["não"]}),
    ("05_suporte_internet_tras", "suporte_internet", "tras", "Suporte técnico (para trás)",
     ["consultar", "como solucao", "por que não causa = problema só no aparelho?"],
     {"roteador_liga": ["sim"], "outros_funcionam": ["sim"], "tipo_conexao": ["wifi"], "wifi_conectado": ["sim"],
      "sinal": ["forte"], "ip_valido": ["sim"], "abre_por_ip": ["sim"], "abre_por_nome": ["não"],
      "velocidade": ["80"]}),
    ("06_celular_edicao_da_base", "celular", "tras", "Seleção de produto, com edição da base durante o uso",
     ["consultar observacao", "como",
      "adicionar regra: SE faixa = intermediário E uso = jogos E bateria_importante = sim "
      "ENTÃO observacao = jogos exigem bateria grande",
      "validar", "limpar", "consultar observacao", "o que você sabe?"],
     {"orcamento": ["2500"], "uso": ["jogos"], "bateria_importante": ["sim"], "mao_pequena": ["não"],
      "resistente_agua": ["sim"], "sistema": ["android"]}),
    ("07_cursos_encadeamento_misto", "cursos", "misto", "Recomendação de cursos (variáveis multivaloradas)",
     ["consultar", "como curso", "fatos"],
     {"gosta_matematica": ["sim"], "gosta_programar": ["sim"], "gosta_experimentos": ["não"],
      "gosta_pessoas": ["não"], "gosta_criar": ["sim"], "gosta_negocios": ["não"], "gosta_escrever": ["não"],
      "gosta_biologia": ["não"], "tempo_disponivel": ["noturno"]}),
]


def gerar(destino=DESTINO):
    destino.mkdir(parents=True, exist_ok=True)
    indice = ["# Sessões de exemplo do shell\n",
              "Transcrições geradas por `python -m sbc.sessoes_exemplo`. A saída é exatamente a do terminal; "
              "as linhas `você>` são as entradas do usuário.\n"]
    for nome, base, modo, titulo, comandos, respostas in SESSOES:
        saida, cmds = [], iter(comandos)
        filas = {k: list(v) for k, v in respostas.items()}
        dialogo = []

        def entrada(_):
            p = dialogo[0].pergunta_em_curso
            if p is not None:
                fila = filas.get(p.atributo)
                return (fila.pop(0) if len(fila) > 1 else fila[0]) if fila else "não sei"
            try:
                return next(cmds)
            except StopIteration:
                raise EOFError from None

        d = Dialogo(carregar(PASTA_BASES / f"{base}.kb"), entrada=entrada, saida=saida.append, modo=modo, eco=True)
        dialogo.append(d)
        d.executar()
        (destino / f"{nome}.txt").write_text("\n".join(saida) + "\n", encoding="utf-8")
        indice.append(f"- [{nome}.txt]({nome}.txt) — **{titulo}** (base `{base}`, modo `{modo}`)")
    (destino / "README.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
    return [x[0] for x in SESSOES]


if __name__ == "__main__":
    for n in gerar():
        print("gerado:", n)
