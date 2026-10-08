PY ?= python

.PHONY: tudo q1 q2 q3 q4 q5 testes sessoes

tudo: q1 q2 q3 q4 sessoes testes

q1:
	$(PY) -m q1.executar
q2:
	$(PY) -m q2.executar
q3:            # precisa de data/diabetes.csv
	$(PY) -m q3.executar
q4: q3         # usa a divisão e as métricas da Q3
	$(PY) -m q4.executar
q5:
	$(PY) -m sbc
sessoes:
	$(PY) -m sbc.sessoes_exemplo
testes:
	$(PY) -W ignore -m unittest discover -s tests -t .
