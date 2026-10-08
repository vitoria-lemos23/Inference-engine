# Questão 5 — Shell genérico de Sistema Baseado em Conhecimento (SBC)

Um *shell* é um SBC **sem conhecimento de domínio**: o motor de inferência, o módulo de explicação, o editor e a
interface são independentes do assunto; o conhecimento (regras, fatos, variáveis) vem de **arquivos de base de
conhecimento** carregados em tempo de execução. Aqui o shell é escrito em Python puro (sem dependências), roda
no terminal e conversa em português.

```
python -m sbc                      # abre o shell sem base; digite «bases» e «carregar animais»
python -m sbc animais              # já carrega uma base de exemplo (ou um caminho para .kb / .json)
python -m sbc credito --modo tras  # modo inicial: frente | tras | misto
python -m sbc --listar-bases
python -m sbc celular --script minha_sessao.txt   # executa um roteiro (uma entrada por linha) com eco
python -m sbc.sessoes_exemplo      # regera as transcrições em docs/exemplos_sessoes/
```

## O que atende ao enunciado

| Exigência | Onde está |
|---|---|
| **Editor da base** (regras e fatos) | `sbc/editor.py` (API) + comandos em linguagem natural e **editor guiado** (`editor`) em `sbc/dialogo.py`; validação com avisos (`validar`) |
| **Encadeamento para frente** | `Motor.encadear_para_frente` / modo `frente` (`sbc/motor.py`) |
| **Encadeamento para trás** | `Motor._obter` / modo `tras` |
| **Encadeamento misto** | modo `misto`: propaga para frente tudo o que já se sabe e, para o que falta, raciocina para trás, propagando para frente a cada resposta do usuário |
| **Explicação "Por quê?"** | durante uma pergunta: `por quê?` (repetível: sobe a cadeia de objetivos até a meta) — `explicacao.por_que` |
| **Explicação "Como?"** | `como` / `como chegou ao animal?` — árvore de justificativa até os dados do usuário — `explicacao.como` |
| extra: **"Por que não?"** e **trilha** | `por que não risco = baixo?` mostra, regra a regra, qual condição falhou; `trilha` lista a sequência de eventos |
| **Interface** (idealmente diálogo em linguagem natural) | `sbc/nl.py` + `sbc/dialogo.py`: comandos, respostas e fatos escritos em português livre (sem LLM externo; veja “Linguagem natural”) |
| **Sem conhecimento de domínio embutido** | nenhum módulo do shell (motor, parser, editor, explicação, diálogo) contém conhecimento de um domínio — só exemplos no texto de ajuda; os domínios estão em `sbc/bases/*.kb` |
| **Várias bases/domínios** | `animais`, `diagnostico_pc` (diagnóstico de equipamento), `suporte_internet` (suporte técnico), `celular` (seleção de produto), `cursos` (recomendação de curso) e `credito` (importada da Questão 1) |

## Arquitetura

```
 ┌───────────────┐  texto livre  ┌──────────┐  intenção+args  ┌────────────────────────────────┐
 │   usuário     │ ────────────► │  nl.py   │ ──────────────► │         dialogo.py             │
 │  (terminal)   │ ◄──────────── │ (PT-BR)  │                 │  laço de comandos, perguntas,  │
 └───────────────┘   respostas   └──────────┘                 │  editor guiado, carregar/salvar│
                                                              └──────┬──────────┬──────────┬───┘
                                                                     │          │          │
                                               ┌─────────────────────▼─┐  ┌─────▼──────┐ ┌─▼────────────┐
                                               │ motor.py              │  │ editor.py  │ │ explicacao.py│
                                               │ memória de trabalho   │  │ CRUD +     │ │ Como? Por    │
                                               │ frente / trás / misto │  │ validação  │ │ quê? Por que │
                                               └───────────┬───────────┘  └─────┬──────┘ │ não? trilha  │
                                                           │                    │        └──────┬───────┘
                                                      ┌────▼────────────────────▼───────────────▼────┐
                                                      │ modelo.py  (Condicao, Regra, Variavel, Base) │
                                                      └────────────────────▲─────────────────────────┘
                                                                           │ lê/escreve
                                                      ┌────────────────────┴─────────────────────────┐
                                                      │ parser.py  (.kb texto  ⇄  .json)  · importar │
                                                      └────────────────────▲─────────────────────────┘
                                                                           │
                                                              sbc/bases/*.kb   (conhecimento do domínio)
```

### Representação do conhecimento (`modelo.py`)

* **Fato**: `atributo = valor` (modelo atributo-valor). Variáveis podem ser de **valor único** ou **multivaloradas**
  (várias conclusões simultâneas, p.ex. uma lista de cursos).
* **Regra**: `SE c1 E c2 … ENTÃO a1 E a2 …`, com operadores `=`, `≠`, `<`, `≤`, `>`, `≥`, `∈` (EM) e negação (`NÃO`).
  Um `OU` é expandido em regras separadas (R5, R5.2…), o que mantém a base simples para o motor e para as explicações.
* **Lógica de três valores** nas condições: *verdadeira*, *falsa* ou *desconhecida* (o atributo ainda não tem valor).
  “Desconhecido” **não** é “diferente”: `a ≠ x` só é verdadeira quando `a` é conhecida e não é `x`.
* **Variável**: nome, rótulo (texto mostrado ao usuário), pergunta, valores possíveis, tipo (texto/número/booleano),
  se é **perguntável** (por padrão: quando nenhuma regra a conclui) e se é multivalorada.
* Comparações ignoram acento e caixa (`Médio` = `medio`); números são comparados como números.

### Motor de inferência (`motor.py`)

**Para frente (dirigido por dados).** Repete: *casar* (regras ainda não disparadas cujas condições são todas
verdadeiras) → *resolver conflito* → *disparar* (acrescentar conclusões à memória de trabalho), até o ponto fixo.
Cada regra dispara no máximo uma vez (**refração**). Estratégias de resolução de conflito, escolhidas na base
(`ESTRATÉGIA:`): `ordem` (ordem do arquivo), `especificidade` (mais condições primeiro) e `prioridade`
(`[prioridade n]` da regra). No modo `frente` o shell antes **coleta** todas as variáveis perguntáveis — é o
comportamento típico de um sistema dirigido por dados.

**Para trás (dirigido por meta).** `_obter(atributo, valor_desejado)`:
1. se a meta já vale, termina;
2. senão, percorre as regras que *concluem* o atributo (filtrando pelo valor desejado) e testa as condições de cada
   uma da esquerda para a direita; cada condição sem valor vira **submeta** (recursão);
3. se nenhuma regra resolve e a variável é perguntável, **pergunta ao usuário** (uma única vez por variável);
4. “não sei” marca a variável como desconhecida e a consulta segue por outros caminhos.

Há **detecção de ciclos** (submeta já em andamento é cortada) e **memória de regras que falharam**
definitivamente. Uma **pilha de objetivos** (`Frame`: meta, regra, índice da condição) acompanha o raciocínio; é ela
que alimenta o *Por quê?*. Para metas multivaloradas o motor continua procurando até esgotar as regras.

**Misto.** `encadear_para_frente()` com o que já se sabe; se a meta ainda não foi estabelecida, raciocínio para
trás, e **após cada resposta do usuário** nova propagação para frente (as respostas podem completar outras regras e
até concluir a meta antes de todas as perguntas serem feitas).

> Conflitos: se duas regras concluem valores diferentes de uma variável de valor único, vale a primeira disparada
> (segundo a estratégia) e o motor registra um evento `conflito` na trilha; `validar` detecta os casos mais
> óbvios antes da execução.

### Explicações (`explicacao.py`)

* **Como?** — cada fato guarda sua origem (*usuário*, *fato inicial* ou *regra* + as premissas usadas). A
  explicação é a árvore de justificativa desde a conclusão até as respostas do usuário.
* **Por quê?** — a pergunta em curso guarda a pilha de objetivos. O 1º “por quê?” cita a regra e a condição que
  motivam a pergunta; cada novo “por quê?” sobe um nível, até chegar à meta da consulta.
* **Por que não?** — para `x = v` não concluído, lista as regras que o concluiriam e a **primeira condição que falha**
  em cada uma (ou se algum dado é desconhecido).
* **Trilha** — registro cronológico: perguntas, respostas, regras disparadas/descartadas, conflitos.

### Linguagem natural (`nl.py`)

Sem LLM e sem rede: é um interpretador de padrões em português, sem distinguir acentos/maiúsculas.
* **Comandos** → intenção + argumentos por expressões regulares (`"qual é o animal?"` → consultar `animal`).
* **Respostas** a perguntas: número da opção, valor, valor aproximado (`curtto` → `Curto`), frases (`"acho que é
  acima de $35k"`), números (`R$ 2.500`), “sim/não” com sinônimos, `não sei`, `por quê?`, `cancelar`.
* **Fatos em frases**: `"a renda é de $0 a $15k e o tempo de emprego é curto"`, `"tem pelos, amamenta e não voa"`,
  `"prefiro android"` (valores que pertencem a uma única variável dispensam o nome da variável).

Limitação honesta: é reconhecimento de padrões, não compreensão. Frases fora desses padrões geram “Não entendi” e o
shell sugere `ajuda`.

## Formato `.kb`

```text
# comentário
BASE: Nome da base
DESCRIÇÃO: uma linha
META: variavel1, variavel2         # o que «consultar» determina, em sequência
ESTRATÉGIA: ordem | especificidade | prioridade

VARIÁVEL renda
    RÓTULO: renda anual do solicitante
    PERGUNTA: Qual é a faixa de renda anual?
    VALORES: "$0 a $15k", "$15 a $35k", "Acima de $35k"
    TIPO: texto | numero | booleano
    PERGUNTÁVEL: sim | não            # padrão: sim, se nenhuma regra conclui a variável
    MULTIVALORADA: sim | não

FATO: variavel = valor                # conhecido desde o início

REGRA R1 [prioridade 3]: SE renda = "$0 a $15k" E tempo EM [Curto, Médio] OU divida > 10 ENTÃO risco = Alto
    EXPLICAÇÃO: texto livre mostrado no «como?»
```

Notas: variáveis usadas apenas nas regras são declaradas automaticamente; valores com espaços não precisam de
aspas (`classe = ave aquática`); “e”, “ou”, “se” **dentro** de um valor são aceitos quando o que vem depois não
parece uma nova condição (`acao = limpar poeira e ventoinhas`); use aspas para valores com vírgula ou
parênteses. `salvar x.json` grava a mesma base em JSON.

## Criar uma base para um novo domínio

1. Escreva `meu_dominio.kb` (copie uma base de `sbc/bases/` como modelo) — ou comece vazio e use `adicionar regra:`.
2. `python -m sbc meu_dominio.kb` → `validar` aponta valores fora do domínio, regras que nunca disparam, regras
   idênticas/contraditórias e dependências circulares.
3. Opcional: converta regras de uma árvore de decisão (Questões 1, 2 e 4) em base do shell:

```
python -m sbc.importar --regras q1/resultados/regras_id3.json --csv q1/dados/credito_ampliado.csv \
       --classe Risco --saida sbc/bases/credito.kb --nome "Risco de crédito (ID3)"
```

A base `credito.kb` foi gerada assim e há um teste (`tests/test_integracao_credito.py`) provando que, nas 216
combinações possíveis dos atributos, o shell decide **exatamente como a árvore ID3** — em qualquer dos três modos.

## Bases de exemplo

| Arquivo | Domínio | Regras | Destaques |
|---|---|---|---|
| `animais.kb` | classificação de animais | 23 | duas camadas de inferência (classe → espécie), estratégia por especificidade |
| `diagnostico_pc.kb` | diagnóstico de equipamento | 36 | prioridades, variável numérica (temperatura), metas multivaloradas (defeitos, ações, gravidade) |
| `suporte_internet.kb` | suporte técnico | 19 | causa → solução, valores numéricos |
| `celular.kb` | seleção de produto | 24 | faixas numéricas de orçamento, operador `EM`, observações acumuladas |
| `cursos.kb` | recomendação de curso | 22 | perfil vocacional multivalorado, OU nas regras, prioridade |
| `credito.kb` | risco de crédito | 14 | regras extraídas da árvore ID3 (Questão 1) |

Transcrições completas em [`docs/exemplos_sessoes/`](../docs/exemplos_sessoes/README.md).

## Testes

```
python -m unittest discover -s tests -t .
```
`tests/test_sbc_parser.py` (gramática, ida-e-volta .kb/.json), `tests/test_sbc_motor.py` (três modos, refração,
ciclos, multivaloradas, estratégias, concordância entre modos em todas as bases, Como/Por quê/Por que não, editor
e validação), `tests/test_sbc_dialogo.py` (linguagem natural, sessões completas, “usuário automático” em todas as
bases e modos) e `tests/test_integracao_credito.py` (árvore ID3 ≡ shell).

## Limitações

* Modelo atributo-valor (sem variáveis lógicas/unificação como em Prolog/CLIPS); uma regra não compara duas
  variáveis entre si (`a < b`), só variável × constante.
* Sem fatores de certeza/probabilidade: o conhecimento é categórico (a incerteza só aparece como “não sei”).
* Ao editar a base durante uma consulta, o shell recalcula o que foi derivado e mantém o que o usuário informou.
* A interface é só de terminal (como combinado); a classe `Dialogo` aceita entrada/saída injetáveis, então uma
  interface web ou gráfica poderia reaproveitar todo o resto.
