# Base de regras — C4.5 podada

| Regra | SE ... ENTÃO ... | Cobertura | Confiança |
| --- | --- | --- | --- |
| R1 | SE Renda = $0 a $15k ENTÃO Risco = Alto | 8 | 7/8 |
| R2 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Boa ENTÃO Risco = Moderado | 2 | 2/2 |
| R3 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Baixa ENTÃO Risco = Moderado | 1 | 1/1 |
| R4 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Alta ENTÃO Risco = Alto | 2 | 2/2 |
| R5 | SE Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Ruim ENTÃO Risco = Alto | 1 | 1/1 |
| R6 | SE Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Desconhecida ENTÃO Risco = Moderado | 1 | 1/1 |
| R7 | SE Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Ruim ENTÃO Risco = Alto | 1 | 1/1 |
| R8 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Boa ENTÃO Risco = Baixo | 2 | 2/2 |
| R9 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Ruim ENTÃO Risco = Moderado | 1 | 1/1 |
| R10 | SE Renda = Acima de $35k E História de Crédito = Boa ENTÃO Risco = Baixo | 5 | 5/5 |
| R11 | SE Renda = Acima de $35k E História de Crédito = Desconhecida ENTÃO Risco = Baixo | 4 | 4/4 |
| R12 | SE Renda = Acima de $35k E História de Crédito = Ruim ENTÃO Risco = Moderado | 2 | 2/2 |
