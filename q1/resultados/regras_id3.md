# Base de regras — ID3

| Regra | SE ... ENTÃO ... | Cobertura | Confiança |
| --- | --- | --- | --- |
| R1 | SE Renda = $0 a $15k E Tempo de Emprego = Curto ENTÃO Risco = Alto | 4 | 4/4 |
| R2 | SE Renda = $0 a $15k E Tempo de Emprego = Médio ENTÃO Risco = Alto | 2 | 2/2 |
| R3 | SE Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Baixa ENTÃO Risco = Moderado | 1 | 1/1 |
| R4 | SE Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Alta ENTÃO Risco = Alto | 1 | 1/1 |
| R5 | SE Renda = $15 a $35k E História de Crédito = Boa E Dívida = Baixa ENTÃO Risco = Baixo | 2 | 2/2 |
| R6 | SE Renda = $15 a $35k E História de Crédito = Boa E Dívida = Alta ENTÃO Risco = Moderado | 2 | 2/2 |
| R7 | SE Renda = $15 a $35k E História de Crédito = Desconhecida E Dívida = Baixa ENTÃO Risco = Moderado | 2 | 2/2 |
| R8 | SE Renda = $15 a $35k E História de Crédito = Desconhecida E Dívida = Alta ENTÃO Risco = Alto | 2 | 2/2 |
| R9 | SE Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Curto ENTÃO Risco = Alto | 1 | 1/1 |
| R10 | SE Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Médio ENTÃO Risco = Alto | 1 | 1/1 |
| R11 | SE Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Longo ENTÃO Risco = Moderado | 1 | 1/1 |
| R12 | SE Renda = Acima de $35k E História de Crédito = Boa ENTÃO Risco = Baixo | 5 | 5/5 |
| R13 | SE Renda = Acima de $35k E História de Crédito = Desconhecida ENTÃO Risco = Baixo | 4 | 4/4 |
| R14 | SE Renda = Acima de $35k E História de Crédito = Ruim ENTÃO Risco = Moderado | 2 | 2/2 |
