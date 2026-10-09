# Lista 1 de Inteligência Artificial — 2026.2

Alunos: Gabriel Calixto, Vitória Lemos
Resolução da Lista 1 (Prof. Evandro Costa): árvores de decisão (ID3, C4.5, CART), extração e comparação de bases de
regras, aprendizado direto de regras (PRISM) e um *shell* genérico de sistemas baseados em conhecimento.
Enunciado: [`docs/enunciado_lista1.pdf`](docs/enunciado_lista1.pdf).

| Questão | O que é | Relatório | Código | Status |
|---|---|---|---|---|
| **1** (1,5) | Base de crédito ampliada (6 atributos, 30 exemplos); ID3, C4.5 e CART **construídos passo a passo**; bases de regras; comparação e escolha | [`q1/RELATORIO.md`](q1/RELATORIO.md) | `ia/arvores.py`, `ia/regras.py`, `q1/` | ✅ |
| **2** (1,5) | Mesmos modelos com **scikit-learn** (+ ARFF para o Weka/J48) e comparação com as implementações próprias | [`q2/RELATORIO.md`](q2/RELATORIO.md) | `q2/`, `ia/sk_utils.py` | ✅ |
| **3** (1,5) | Árvore de decisão + regras no **Pima Indians Diabetes** (Kaggle); acurácia, precisão, recall, F1 | `q3/RELATORIO.md` (gerado) | `q3/` | ⏳ aguardando `data/diabetes.csv` (veja abaixo) |
| **4** (1,5) | **PRISM** (implementado do zero) no mesmo conjunto; base de regras e métricas; comparação com a Q3 | `q4/RELATORIO.md` (gerado) | `ia/prism.py`, `q4/` | ⏳ idem |
| **5** (4,0) | **Shell de SBC** genérico: editor de base, encadeamento para frente/trás/misto, *Por quê?*/*Como?*, diálogo em português | [`sbc/README.md`](sbc/README.md), [`docs/exemplos_sessoes/`](docs/exemplos_sessoes/README.md) | `sbc/` | ✅ |

## Como executar

```bash
pip install -r requirements.txt          # numpy, pandas, scikit-learn, matplotlib (Graphviz `dot` é opcional)

python -m q1.executar                    # gera q1/resultados/* e q1/RELATORIO.md
python -m q2.executar                    # gera q2/resultados/* e q2/RELATORIO.md
# Questões 3 e 4: salve o diabetes.csv do Kaggle em data/diabetes.csv (veja data/README.md)
python -m q3.executar                    # ~2 min (busca em grade com validação cruzada)
python -m q4.executar
python -m sbc animais                    # shell interativo (ou: python -m sbc, e digite «bases»)
python -m unittest discover -s tests -t .    # 99 testes
```
(`make tudo` faz o conjunto; `make testes` só os testes.)

## Resultados principais

**Questão 1 — 30 exemplos, 6 atributos** (acurácia no treino = 100% nas árvores completas; as demais colunas medem
generalização, em que o conjunto pequeno exige cautela):

| Árvore | Regras | Cond. médias | Leave-one-out | CV 5-fold×20 | Cobertura do espaço de 216 entradas |
|---|---|---|---|---|---|
| **ID3** (escolhida) | 14 | 2,6 | 80,0% | 77,0% | 100% |
| C4.5 | 14 | 2,9 | 70,0% | 71,7% | 92,6% |
| C4.5 podada | 12 | 2,8 | 63,3% | 65,3% | 92,6% |
| CART | 11 | 3,0 | 73,3% | 69,7% | 96,3% |

A justificativa completa da escolha (e a discussão honesta de que, com 30 exemplos, as diferenças são pequenas) está no
relatório. Todos os cálculos de entropia, ganho, razão de ganho e Gini aparecem passo a passo em
`q1/resultados/passo_a_passo_*.md`.

**Questão 5 —** seis bases de conhecimento (animais, diagnóstico de PC, suporte de internet, escolha de celular,
cursos e risco de crédito) rodam no mesmo motor; a base de crédito é gerada das regras ID3 da Questão 1 e um teste
automático verifica que o shell decide **exatamente como a árvore** nas 216 combinações possíveis.

## Estrutura

```
ia/        biblioteca própria: base.py (dados), arvores.py (ID3/C4.5/CART), regras.py, prism.py, metricas.py,
           regras_num.py (regras de árvores numéricas), relatorio.py (Markdown/Graphviz), sk_utils.py
q1/ q2/    scripts, dados, resultados e relatório de cada questão
q3/ q4/    idem (dados do Kaggle em data/)
sbc/       shell de SBC: modelo, parser, motor, explicacao, editor, nl, dialogo, bases/*.kb
tests/     99 testes (unittest)
docs/      enunciado e transcrições de sessões do shell
```

## Observações e limitações

* **Weka / R:** não estavam disponíveis no ambiente de desenvolvimento; a Questão 2 usa scikit-learn e inclui o arquivo
  `q2/dados/credito_ampliado.arff`, que **não foi testado no Weka** (o formato segue a especificação do ARFF; J48 usa
  C4.5, então os resultados devem ser comparáveis aos do C4.5 próprio).
* O scikit-learn só implementa CART (Gini ou entropia); não há ID3/C4.5 "de biblioteca" nele — por isso a comparação com
  as implementações próprias.
* Árvores com 30 exemplos são instáveis: pequenas mudanças no conjunto alteram a estrutura. O relatório da Q1 inclui
  uma análise de sensibilidade (remoção de um exemplo por vez).
* Q3/Q4: o conjunto Pima é pequeno e ruidoso; os relatórios trazem intervalos de confiança (*bootstrap*) e deixam claro
  quando diferenças não são conclusivas. Não é uma ferramenta de diagnóstico.
* O shell (Q5) interpreta português por padrões (sem LLM): ver "Limitações" em [`sbc/README.md`](sbc/README.md).
