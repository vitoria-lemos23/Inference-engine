# Regras — sklearn · CART (Gini)

| Regra | SE ... ENTÃO ... | Cobertura | Confiança |
| --- | --- | --- | --- |
| R1 | SE Renda = $0 a $15k E Residência = Alugada ENTÃO Risco = Alto | 6 | 6/6 |
| R2 | SE Renda = $0 a $15k E Residência = Própria E Garantia = Nenhuma ENTÃO Risco = Alto | 1 | 1/1 |
| R3 | SE Renda = $0 a $15k E Residência = Própria E Garantia = Adequada ENTÃO Risco = Moderado | 1 | 1/1 |
| R4 | SE Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Boa E Dívida = Alta ENTÃO Risco = Moderado | 2 | 2/2 |
| R5 | SE Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Desconhecida E Dívida = Alta ENTÃO Risco = Alto | 2 | 2/2 |
| R6 | SE Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito ∈ {Boa, Desconhecida} E Dívida = Baixa ENTÃO Risco = Moderado | 2 | 2/2 |
| R7 | SE Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Ruim ENTÃO Risco = Alto | 2 | 2/2 |
| R8 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E Dívida = Baixa ENTÃO Risco = Baixo | 2 | 2/2 |
| R9 | SE Renda = $15 a $35k E Tempo de Emprego = Longo E Dívida = Alta ENTÃO Risco = Moderado | 1 | 1/1 |
| R10 | SE Renda = Acima de $35k E História de Crédito ∈ {Boa, Desconhecida} ENTÃO Risco = Baixo | 9 | 9/9 |
| R11 | SE Renda = Acima de $35k E História de Crédito = Ruim ENTÃO Risco = Moderado | 2 | 2/2 |
