# Base de regras — C4.5

| Regra | SE ... ENTÃO ... | Cobertura | Confiança |
| --- | --- | --- | --- |
| R1 | SE Renda = $0 a $15k E Residência = Alugada ENTÃO Risco = Alto | 6 | 6/6 |
| R2 | SE Renda = $0 a $15k E Residência = Própria E Dívida = Baixa ENTÃO Risco = Moderado | 1 | 1/1 |
| R3 | SE Renda = $0 a $15k E Residência = Própria E Dívida = Alta ENTÃO Risco = Alto | 1 | 1/1 |
| R4 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Boa ENTÃO Risco = Moderado | 2 | 2/2 |
| R5 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Baixa ENTÃO Risco = Moderado | 1 | 1/1 |
| R6 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Alta ENTÃO Risco = Alto | 2 | 2/2 |
| R7 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Ruim ENTÃO Risco = Alto | 1 | 1/1 |
| R8 | SE Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Desconhecida ENTÃO Risco = Moderado | 1 | 1/1 |
| R9 | SE Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Ruim ENTÃO Risco = Alto | 1 | 1/1 |
| R10 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Boa ENTÃO Risco = Baixo | 2 | 2/2 |
| R11 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Ruim ENTÃO Risco = Moderado | 1 | 1/1 |
| R12 | SE Renda = Acima de $35k E História de Crédito = Boa ENTÃO Risco = Baixo | 5 | 5/5 |
| R13 | SE Renda = Acima de $35k E História de Crédito = Desconhecida ENTÃO Risco = Baixo | 4 | 4/4 |
| R14 | SE Renda = Acima de $35k E História de Crédito = Ruim ENTÃO Risco = Moderado | 2 | 2/2 |
