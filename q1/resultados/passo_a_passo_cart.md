# Q1 — CART — CART

Convenções: contagens por classe escritas como **B**=Baixo, **M**=Moderado, **A**=Alto; log₂ é o logaritmo na base 2 e 0·log₂0 = 0. Empates são resolvidos pela ordem das colunas da base (e, para a classe de uma folha, pela classe mais grave).

## Nó 1  —  (raiz)

Exemplos (30): E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12, E13, E14, E15, E16, E17, E18, E19, E20, E21, E22, E23, E24, E25, E26, E27, E28, E29, E30  
Distribuição: B=11, M=8, A=11  
Gini(S) = 1 − (11/30)² − (8/30)² − (11/30)² = 0,6600

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} | 12 vs. 18 | 0,5694 (B=7, M=3, A=2) | 0,6235 (B=4, M=5, A=9) | 0,6019 | 0,0581 |
| {Boa, Desconhecida} vs. {Ruim} ✔ | 22 vs. 8 | 0,6240 (B=11, M=5, A=6) | 0,4688 (B=0, M=3, A=5) | 0,5826 | 0,0774 |
| {Boa, Ruim} vs. {Desconhecida} | 20 vs. 10 | 0,6650 (B=7, M=6, A=7) | 0,6400 (B=4, M=2, A=4) | 0,6567 | 0,0033 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 16 vs. 14 | 0,6484 (B=7, M=4, A=5) | 0,6531 (B=4, M=4, A=6) | 0,6506 | 0,0094 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 18 vs. 12 | 0,6420 (B=6, M=4, A=8) | 0,6528 (B=5, M=4, A=3) | 0,6463 | 0,0137 |

**Renda** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {$0 a $15k} vs. {$15 a $35k, Acima de $35k} | 8 vs. 22 | 0,2188 (B=0, M=1, A=7) | 0,6157 (B=11, M=7, A=4) | 0,5098 | 0,1502 |
| {$0 a $15k, $15 a $35k} vs. {Acima de $35k} ✔ | 19 vs. 11 | 0,5540 (B=2, M=6, A=11) | 0,2975 (B=9, M=2, A=0) | 0,4600 | 0,2000 |
| {$0 a $15k, Acima de $35k} vs. {$15 a $35k} | 19 vs. 11 | 0,6150 (B=9, M=3, A=7) | 0,6281 (B=2, M=5, A=4) | 0,6198 | 0,0402 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio, Longo} ✔ | 11 vs. 19 | 0,5124 (B=1, M=3, A=7) | 0,6094 (B=10, M=5, A=4) | 0,5738 | 0,0862 |
| {Curto, Médio} vs. {Longo} | 22 vs. 8 | 0,6446 (B=6, M=6, A=10) | 0,5312 (B=5, M=2, A=1) | 0,6144 | 0,0456 |
| {Curto, Longo} vs. {Médio} | 19 vs. 11 | 0,6537 (B=6, M=5, A=8) | 0,6446 (B=5, M=3, A=3) | 0,6504 | 0,0096 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 16 vs. 14 | 0,5859 (B=4, M=3, A=9) | 0,6020 (B=7, M=5, A=2) | 0,5935 | 0,0665 |

➡ **Divisão escolhida: Renda ∈ {$0 a $15k, $15 a $35k}?**  Gini ponderado = (19/30)·0,5540 + (11/30)·0,2975 = **0,4600** (redução de 0,2000).

## Nó 2  —  Renda ∈ {$0 a $15k, $15 a $35k}

Exemplos (19): E1, E2, E3, E4, E7, E11, E12, E14, E15, E16, E17, E18, E19, E20, E21, E22, E24, E25, E26  
Distribuição: B=2, M=6, A=11  
Gini(S) = 1 − (2/19)² − (6/19)² − (11/19)² = 0,5540

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} ✔ | 7 vs. 12 | 0,6531 (B=2, M=3, A=2) | 0,3750 (B=0, M=3, A=9) | 0,4774 | 0,0766 |
| {Boa, Desconhecida} vs. {Ruim} | 13 vs. 6 | 0,6154 (B=2, M=5, A=6) | 0,2778 (B=0, M=1, A=5) | 0,5088 | 0,0452 |
| {Boa, Ruim} vs. {Desconhecida} | 13 vs. 6 | 0,5917 (B=2, M=4, A=7) | 0,4444 (B=0, M=2, A=4) | 0,5452 | 0,0088 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 10 vs. 9 | 0,6200 (B=2, M=3, A=5) | 0,4444 (B=0, M=3, A=6) | 0,5368 | 0,0172 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 13 vs. 6 | 0,5207 (B=1, M=4, A=8) | 0,6111 (B=1, M=2, A=3) | 0,5493 | 0,0048 |

**Renda** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {$0 a $15k} vs. {$15 a $35k} ✔ | 8 vs. 11 | 0,2188 (B=0, M=1, A=7) | 0,6281 (B=2, M=5, A=4) | 0,4557 | 0,0983 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio, Longo} | 10 vs. 9 | 0,4200 (B=0, M=3, A=7) | 0,6420 (B=2, M=3, A=4) | 0,5251 | 0,0289 |
| {Curto, Médio} vs. {Longo} ✔ | 14 vs. 5 | 0,4082 (B=0, M=4, A=10) | 0,6400 (B=2, M=2, A=1) | 0,4692 | 0,0848 |
| {Curto, Longo} vs. {Médio} | 15 vs. 4 | 0,5867 (B=2, M=5, A=8) | 0,3750 (B=0, M=1, A=3) | 0,5421 | 0,0119 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 12 vs. 7 | 0,3750 (B=0, M=3, A=9) | 0,6531 (B=2, M=3, A=2) | 0,4774 | 0,0766 |

➡ **Divisão escolhida: Renda ∈ {$0 a $15k}?**  Gini ponderado = (8/19)·0,2188 + (11/19)·0,6281 = **0,4557** (redução de 0,0983).

## Nó 3  —  Renda = $0 a $15k

Exemplos (8): E1, E4, E7, E11, E17, E18, E19, E24  
Distribuição: B=0, M=1, A=7  
Gini(S) = 1 − (1/8)² − (7/8)² = 0,2188

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} ✔ | 3 vs. 5 | 0,4444 (B=0, M=1, A=2) | 0,0000 (B=0, M=0, A=5) | 0,1667 | 0,0521 |
| {Boa, Desconhecida} vs. {Ruim} | 5 vs. 3 | 0,3200 (B=0, M=1, A=4) | 0,0000 (B=0, M=0, A=3) | 0,2000 | 0,0188 |
| {Boa, Ruim} vs. {Desconhecida} | 6 vs. 2 | 0,2778 (B=0, M=1, A=5) | 0,0000 (B=0, M=0, A=2) | 0,2083 | 0,0104 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 5 vs. 3 | 0,3200 (B=0, M=1, A=4) | 0,0000 (B=0, M=0, A=3) | 0,2000 | 0,0188 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 5 vs. 3 | 0,0000 (B=0, M=0, A=5) | 0,4444 (B=0, M=1, A=2) | 0,1667 | 0,0521 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio, Longo} | 4 vs. 4 | 0,0000 (B=0, M=0, A=4) | 0,3750 (B=0, M=1, A=3) | 0,1875 | 0,0312 |
| {Curto, Médio} vs. {Longo} ✔ | 6 vs. 2 | 0,0000 (B=0, M=0, A=6) | 0,5000 (B=0, M=1, A=1) | 0,1250 | 0,0938 |
| {Curto, Longo} vs. {Médio} | 6 vs. 2 | 0,2778 (B=0, M=1, A=5) | 0,0000 (B=0, M=0, A=2) | 0,2083 | 0,0104 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 6 vs. 2 | 0,0000 (B=0, M=0, A=6) | 0,5000 (B=0, M=1, A=1) | 0,1250 | 0,0938 |

➡ **Divisão escolhida: Tempo de Emprego ∈ {Curto, Médio}?**  Gini ponderado = (6/8)·0,0000 + (2/8)·0,5000 = **0,1250** (redução de 0,0938).

## Nó 4  —  Renda = $0 a $15k E Tempo de Emprego ∈ {Curto, Médio}

Exemplos (6): E1, E4, E7, E11, E18, E19  
Distribuição: B=0, M=0, A=6  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 5  —  Renda = $0 a $15k E Tempo de Emprego = Longo

Exemplos (2): E17, E24  
Distribuição: B=0, M=1, A=1  
Gini(S) = 1 − (1/2)² − (1/2)² = 0,5000

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 1 vs. 1 | 0,0000 (B=0, M=1, A=0) | 0,0000 (B=0, M=0, A=1) | 0,0000 | 0,5000 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 1 vs. 1 | 0,0000 (B=0, M=0, A=1) | 0,0000 (B=0, M=1, A=0) | 0,0000 | 0,5000 |

➡ **Divisão escolhida: Dívida ∈ {Baixa}?**  Gini ponderado = (1/2)·0,0000 + (1/2)·0,0000 = **0,0000** (redução de 0,5000).

## Nó 6  —  Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Baixa

Exemplos (1): E24  
Distribuição: B=0, M=1, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 7  —  Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Alta

Exemplos (1): E17  
Distribuição: B=0, M=0, A=1  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 8  —  Renda = $15 a $35k

Exemplos (11): E2, E3, E12, E14, E15, E16, E20, E21, E22, E25, E26  
Distribuição: B=2, M=5, A=4  
Gini(S) = 1 − (2/11)² − (5/11)² − (4/11)² = 0,6281

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} ✔ | 4 vs. 7 | 0,5000 (B=2, M=2, A=0) | 0,4898 (B=0, M=3, A=4) | 0,4935 | 0,1346 |
| {Boa, Desconhecida} vs. {Ruim} | 8 vs. 3 | 0,6250 (B=2, M=4, A=2) | 0,4444 (B=0, M=1, A=2) | 0,5758 | 0,0523 |
| {Boa, Ruim} vs. {Desconhecida} | 7 vs. 4 | 0,6531 (B=2, M=3, A=2) | 0,5000 (B=0, M=2, A=2) | 0,5974 | 0,0307 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 5 vs. 6 | 0,6400 (B=2, M=2, A=1) | 0,5000 (B=0, M=3, A=3) | 0,5636 | 0,0645 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 8 vs. 3 | 0,5938 (B=1, M=4, A=3) | 0,6667 (B=1, M=1, A=1) | 0,6136 | 0,0145 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio, Longo} | 6 vs. 5 | 0,5000 (B=0, M=3, A=3) | 0,6400 (B=2, M=2, A=1) | 0,5636 | 0,0645 |
| {Curto, Médio} vs. {Longo} ✔ | 8 vs. 3 | 0,5000 (B=0, M=4, A=4) | 0,4444 (B=2, M=1, A=0) | 0,4848 | 0,1433 |
| {Curto, Longo} vs. {Médio} | 9 vs. 2 | 0,6420 (B=2, M=4, A=3) | 0,5000 (B=0, M=1, A=1) | 0,6162 | 0,0119 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 6 vs. 5 | 0,5000 (B=0, M=3, A=3) | 0,6400 (B=2, M=2, A=1) | 0,5636 | 0,0645 |

➡ **Divisão escolhida: Tempo de Emprego ∈ {Curto, Médio}?**  Gini ponderado = (8/11)·0,5000 + (3/11)·0,4444 = **0,4848** (redução de 0,1433).

## Nó 9  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio}

Exemplos (8): E2, E3, E12, E14, E15, E16, E21, E22  
Distribuição: B=0, M=4, A=4  
Gini(S) = 1 − (4/8)² − (4/8)² = 0,5000

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} ✔ | 2 vs. 6 | 0,0000 (B=0, M=2, A=0) | 0,4444 (B=0, M=2, A=4) | 0,3333 | 0,1667 |
| {Boa, Desconhecida} vs. {Ruim} | 6 vs. 2 | 0,4444 (B=0, M=4, A=2) | 0,0000 (B=0, M=0, A=2) | 0,3333 | 0,1667 |
| {Boa, Ruim} vs. {Desconhecida} | 4 vs. 4 | 0,5000 (B=0, M=2, A=2) | 0,5000 (B=0, M=2, A=2) | 0,5000 | 0,0000 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 3 vs. 5 | 0,4444 (B=0, M=2, A=1) | 0,4800 (B=0, M=2, A=3) | 0,4667 | 0,0333 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 6 vs. 2 | 0,5000 (B=0, M=3, A=3) | 0,5000 (B=0, M=1, A=1) | 0,5000 | 0,0000 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio} ✔ | 6 vs. 2 | 0,5000 (B=0, M=3, A=3) | 0,5000 (B=0, M=1, A=1) | 0,5000 | 0,0000 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 6 vs. 2 | 0,5000 (B=0, M=3, A=3) | 0,5000 (B=0, M=1, A=1) | 0,5000 | 0,0000 |

➡ **Divisão escolhida: História de Crédito ∈ {Boa}?**  Gini ponderado = (2/8)·0,0000 + (6/8)·0,4444 = **0,3333** (redução de 0,1667).

## Nó 10  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Boa

Exemplos (2): E12, E22  
Distribuição: B=0, M=2, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 11  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito ∈ {Desconhecida, Ruim}

Exemplos (6): E2, E3, E14, E15, E16, E21  
Distribuição: B=0, M=2, A=4  
Gini(S) = 1 − (2/6)² − (4/6)² = 0,4444

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Desconhecida} vs. {Ruim} ✔ | 4 vs. 2 | 0,5000 (B=0, M=2, A=2) | 0,0000 (B=0, M=0, A=2) | 0,3333 | 0,1111 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 3 vs. 3 | 0,4444 (B=0, M=2, A=1) | 0,0000 (B=0, M=0, A=3) | 0,2222 | 0,2222 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 4 vs. 2 | 0,3750 (B=0, M=1, A=3) | 0,5000 (B=0, M=1, A=1) | 0,4167 | 0,0278 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio} ✔ | 4 vs. 2 | 0,3750 (B=0, M=1, A=3) | 0,5000 (B=0, M=1, A=1) | 0,4167 | 0,0278 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 4 vs. 2 | 0,3750 (B=0, M=1, A=3) | 0,5000 (B=0, M=1, A=1) | 0,4167 | 0,0278 |

➡ **Divisão escolhida: Dívida ∈ {Baixa}?**  Gini ponderado = (3/6)·0,4444 + (3/6)·0,0000 = **0,2222** (redução de 0,2222).

## Nó 12  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito ∈ {Desconhecida, Ruim} E Dívida = Baixa

Exemplos (3): E3, E15, E21  
Distribuição: B=0, M=2, A=1  
Gini(S) = 1 − (2/3)² − (1/3)² = 0,4444

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Desconhecida} vs. {Ruim} ✔ | 2 vs. 1 | 0,0000 (B=0, M=2, A=0) | 0,0000 (B=0, M=0, A=1) | 0,0000 | 0,4444 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 2 vs. 1 | 0,5000 (B=0, M=1, A=1) | 0,0000 (B=0, M=1, A=0) | 0,3333 | 0,1111 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio} ✔ | 2 vs. 1 | 0,5000 (B=0, M=1, A=1) | 0,0000 (B=0, M=1, A=0) | 0,3333 | 0,1111 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 2 vs. 1 | 0,5000 (B=0, M=1, A=1) | 0,0000 (B=0, M=1, A=0) | 0,3333 | 0,1111 |

➡ **Divisão escolhida: História de Crédito ∈ {Desconhecida}?**  Gini ponderado = (2/3)·0,0000 + (1/3)·0,0000 = **0,0000** (redução de 0,4444).

## Nó 13  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Desconhecida E Dívida = Baixa

Exemplos (2): E3, E21  
Distribuição: B=0, M=2, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 14  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito = Ruim E Dívida = Baixa

Exemplos (1): E15  
Distribuição: B=0, M=0, A=1  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 15  —  Renda = $15 a $35k E Tempo de Emprego ∈ {Curto, Médio} E História de Crédito ∈ {Desconhecida, Ruim} E Dívida = Alta

Exemplos (3): E2, E14, E16  
Distribuição: B=0, M=0, A=3  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 16  —  Renda = $15 a $35k E Tempo de Emprego = Longo

Exemplos (3): E20, E25, E26  
Distribuição: B=2, M=1, A=0  
Gini(S) = 1 − (2/3)² − (1/3)² = 0,4444

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Ruim} ✔ | 2 vs. 1 | 0,0000 (B=2, M=0, A=0) | 0,0000 (B=0, M=1, A=0) | 0,0000 | 0,4444 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 2 vs. 1 | 0,0000 (B=2, M=0, A=0) | 0,0000 (B=0, M=1, A=0) | 0,0000 | 0,4444 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 2 vs. 1 | 0,5000 (B=1, M=1, A=0) | 0,0000 (B=1, M=0, A=0) | 0,3333 | 0,1111 |

➡ **Divisão escolhida: História de Crédito ∈ {Boa}?**  Gini ponderado = (2/3)·0,0000 + (1/3)·0,0000 = **0,0000** (redução de 0,4444).

## Nó 17  —  Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Boa

Exemplos (2): E25, E26  
Distribuição: B=2, M=0, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 18  —  Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Ruim

Exemplos (1): E20  
Distribuição: B=0, M=1, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 19  —  Renda = Acima de $35k

Exemplos (11): E5, E6, E8, E9, E10, E13, E23, E27, E28, E29, E30  
Distribuição: B=9, M=2, A=0  
Gini(S) = 1 − (9/11)² − (2/11)² = 0,2975

**História de Crédito** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Boa} vs. {Desconhecida, Ruim} | 5 vs. 6 | 0,0000 (B=5, M=0, A=0) | 0,4444 (B=4, M=2, A=0) | 0,2424 | 0,0551 |
| {Boa, Desconhecida} vs. {Ruim} ✔ | 9 vs. 2 | 0,0000 (B=9, M=0, A=0) | 0,0000 (B=0, M=2, A=0) | 0,0000 | 0,2975 |
| {Boa, Ruim} vs. {Desconhecida} | 7 vs. 4 | 0,4082 (B=5, M=2, A=0) | 0,0000 (B=4, M=0, A=0) | 0,2597 | 0,0378 |

**Dívida** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Baixa} vs. {Alta} ✔ | 6 vs. 5 | 0,2778 (B=5, M=1, A=0) | 0,3200 (B=4, M=1, A=0) | 0,2970 | 0,0006 |

**Garantia** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Nenhuma} vs. {Adequada} ✔ | 5 vs. 6 | 0,0000 (B=5, M=0, A=0) | 0,4444 (B=4, M=2, A=0) | 0,2424 | 0,0551 |

**Tempo de Emprego** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Curto} vs. {Médio, Longo} | 1 vs. 10 | 0,0000 (B=1, M=0, A=0) | 0,3200 (B=8, M=2, A=0) | 0,2909 | 0,0066 |
| {Curto, Médio} vs. {Longo} | 8 vs. 3 | 0,3750 (B=6, M=2, A=0) | 0,0000 (B=3, M=0, A=0) | 0,2727 | 0,0248 |
| {Curto, Longo} vs. {Médio} ✔ | 4 vs. 7 | 0,0000 (B=4, M=0, A=0) | 0,4082 (B=5, M=2, A=0) | 0,2597 | 0,0378 |

**Residência** — partições binárias testadas:

| Divisão (sim vs. não) | n (sim vs. não) | Gini sim | Gini não | Gini ponderado | Redução |
| --- | --- | --- | --- | --- | --- |
| {Alugada} vs. {Própria} ✔ | 4 vs. 7 | 0,0000 (B=4, M=0, A=0) | 0,4082 (B=5, M=2, A=0) | 0,2597 | 0,0378 |

➡ **Divisão escolhida: História de Crédito ∈ {Boa, Desconhecida}?**  Gini ponderado = (9/11)·0,0000 + (2/11)·0,0000 = **0,0000** (redução de 0,2975).

## Nó 20  —  Renda = Acima de $35k E História de Crédito ∈ {Boa, Desconhecida}

Exemplos (9): E5, E6, E9, E10, E13, E27, E28, E29, E30  
Distribuição: B=9, M=0, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 21  —  Renda = Acima de $35k E História de Crédito = Ruim

Exemplos (2): E8, E23  
Distribuição: B=0, M=2, A=0  
Gini(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.
