# Q1 — ID3 — ID3

Convenções: contagens por classe escritas como **B**=Baixo, **M**=Moderado, **A**=Alto; log₂ é o logaritmo na base 2 e 0·log₂0 = 0. Empates são resolvidos pela ordem das colunas da base (e, para a classe de uma folha, pela classe mais grave).

## Nó 1  —  (raiz)

Exemplos (30): E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12, E13, E14, E15, E16, E17, E18, E19, E20, E21, E22, E23, E24, E25, E26, E27, E28, E29, E30  
Distribuição: B=11, M=8, A=11  
H(S) = − (11/30)·log₂(11/30) − (8/30)·log₂(8/30) − (11/30)·log₂(11/30) = 1,5700

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| História de Crédito | Boa → B=7, M=3, A=2 ; H=1,384<br>Desconhecida → B=4, M=2, A=4 ; H=1,522<br>Ruim → B=0, M=3, A=5 ; H=0,954 | 1,3156 | 0,2544 |
| Dívida | Baixa → B=7, M=4, A=5 ; H=1,546<br>Alta → B=4, M=4, A=6 ; H=1,557 | 1,5511 | 0,0189 |
| Garantia | Nenhuma → B=6, M=4, A=8 ; H=1,530<br>Adequada → B=5, M=4, A=3 ; H=1,555 | 1,5401 | 0,0298 |
| Renda | $0 a $15k → B=0, M=1, A=7 ; H=0,544<br>$15 a $35k → B=2, M=5, A=4 ; H=1,495<br>Acima de $35k → B=9, M=2, A=0 ; H=0,684 | 0,9439 | 0,6261 |
| Tempo de Emprego | Curto → B=1, M=3, A=7 ; H=1,241<br>Médio → B=5, M=3, A=3 ; H=1,539<br>Longo → B=5, M=2, A=1 ; H=1,299 | 1,3657 | 0,2042 |
| Residência | Alugada → B=4, M=3, A=9 ; H=1,420<br>Própria → B=7, M=5, A=2 ; H=1,432 | 1,4253 | 0,1447 |

Cálculos detalhados (todos os atributos, nó raiz):

- Ganho(História de Crédito) = 1,5700 − [(12/30)·1,3844 + (10/30)·1,5219 + (8/30)·0,9544] = 1,5700 − 1,3156 = **0,2544**
- Ganho(Dívida) = 1,5700 − [(16/30)·1,5462 + (14/30)·1,5567] = 1,5700 − 1,5511 = **0,0189**
- Ganho(Garantia) = 1,5700 − [(18/30)·1,5305 + (12/30)·1,5546] = 1,5700 − 1,5401 = **0,0298**
- Ganho(Renda) = 1,5700 − [(8/30)·0,5436 + (11/30)·1,4949 + (11/30)·0,6840] = 1,5700 − 0,9439 = **0,6261**
- Ganho(Tempo de Emprego) = 1,5700 − [(11/30)·1,2407 + (11/30)·1,5395 + (8/30)·1,2988] = 1,5700 − 1,3657 = **0,2042**
- Ganho(Residência) = 1,5700 − [(16/30)·1,4197 + (14/30)·1,4316] = 1,5700 − 1,4253 = **0,1447**

➡ **Atributo escolhido: Renda** (maior ganho de informação).

## Nó 2  —  Renda = $0 a $15k

Exemplos (8): E1, E4, E7, E11, E17, E18, E19, E24  
Distribuição: B=0, M=1, A=7  
H(S) = − (1/8)·log₂(1/8) − (7/8)·log₂(7/8) = 0,5436

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| História de Crédito | Boa → B=0, M=1, A=2 ; H=0,918<br>Desconhecida → B=0, M=0, A=2 ; H=0,000<br>Ruim → B=0, M=0, A=3 ; H=0,000 | 0,3444 | 0,1992 |
| Dívida | Baixa → B=0, M=1, A=4 ; H=0,722<br>Alta → B=0, M=0, A=3 ; H=0,000 | 0,4512 | 0,0924 |
| Garantia | Nenhuma → B=0, M=0, A=5 ; H=0,000<br>Adequada → B=0, M=1, A=2 ; H=0,918 | 0,3444 | 0,1992 |
| Tempo de Emprego | Curto → B=0, M=0, A=4 ; H=0,000<br>Médio → B=0, M=0, A=2 ; H=0,000<br>Longo → B=0, M=1, A=1 ; H=1,000 | 0,2500 | 0,2936 |
| Residência | Alugada → B=0, M=0, A=6 ; H=0,000<br>Própria → B=0, M=1, A=1 ; H=1,000 | 0,2500 | 0,2936 |

Cálculos detalhados do atributo escolhido (Tempo de Emprego):

- Ganho(Tempo de Emprego) = 0,5436 − [(4/8)·0,0000 + (2/8)·0,0000 + (2/8)·1,0000] = 0,5436 − 0,2500 = **0,2936**

➡ **Atributo escolhido: Tempo de Emprego** (maior ganho de informação) (empate com Residência; desempate pela ordem das colunas).

## Nó 3  —  Renda = $0 a $15k E Tempo de Emprego = Curto

Exemplos (4): E1, E7, E11, E18  
Distribuição: B=0, M=0, A=4  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 4  —  Renda = $0 a $15k E Tempo de Emprego = Médio

Exemplos (2): E4, E19  
Distribuição: B=0, M=0, A=2  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 5  —  Renda = $0 a $15k E Tempo de Emprego = Longo

Exemplos (2): E17, E24  
Distribuição: B=0, M=1, A=1  
H(S) = − (1/2)·log₂(1/2) − (1/2)·log₂(1/2) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| Dívida | Baixa → B=0, M=1, A=0 ; H=0,000<br>Alta → B=0, M=0, A=1 ; H=0,000 | 0,0000 | 1,0000 |
| Garantia | Nenhuma → B=0, M=0, A=1 ; H=0,000<br>Adequada → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 1,0000 |

Cálculos detalhados do atributo escolhido (Dívida):

- Ganho(Dívida) = 1,0000 − [(1/2)·0,0000 + (1/2)·0,0000] = 1,0000 − 0,0000 = **1,0000**

➡ **Atributo escolhido: Dívida** (maior ganho de informação) (empate com Garantia; desempate pela ordem das colunas).

## Nó 6  —  Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Baixa

Exemplos (1): E24  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 7  —  Renda = $0 a $15k E Tempo de Emprego = Longo E Dívida = Alta

Exemplos (1): E17  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 8  —  Renda = $15 a $35k

Exemplos (11): E2, E3, E12, E14, E15, E16, E20, E21, E22, E25, E26  
Distribuição: B=2, M=5, A=4  
H(S) = − (2/11)·log₂(2/11) − (5/11)·log₂(5/11) − (4/11)·log₂(4/11) = 1,4949

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| História de Crédito | Boa → B=2, M=2, A=0 ; H=1,000<br>Desconhecida → B=0, M=2, A=2 ; H=1,000<br>Ruim → B=0, M=1, A=2 ; H=0,918 | 0,9777 | 0,5172 |
| Dívida | Baixa → B=2, M=2, A=1 ; H=1,522<br>Alta → B=0, M=3, A=3 ; H=1,000 | 1,2372 | 0,2577 |
| Garantia | Nenhuma → B=1, M=4, A=3 ; H=1,406<br>Adequada → B=1, M=1, A=1 ; H=1,585 | 1,4545 | 0,0404 |
| Tempo de Emprego | Curto → B=0, M=3, A=3 ; H=1,000<br>Médio → B=0, M=1, A=1 ; H=1,000<br>Longo → B=2, M=1, A=0 ; H=0,918 | 0,9777 | 0,5172 |
| Residência | Alugada → B=0, M=3, A=3 ; H=1,000<br>Própria → B=2, M=2, A=1 ; H=1,522 | 1,2372 | 0,2577 |

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 1,4949 − [(4/11)·1,0000 + (4/11)·1,0000 + (3/11)·0,9183] = 1,4949 − 0,9777 = **0,5172**

➡ **Atributo escolhido: História de Crédito** (maior ganho de informação) (empate com Tempo de Emprego; desempate pela ordem das colunas).

## Nó 9  —  Renda = $15 a $35k E História de Crédito = Boa

Exemplos (4): E12, E22, E25, E26  
Distribuição: B=2, M=2, A=0  
H(S) = − (2/4)·log₂(2/4) − (2/4)·log₂(2/4) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| Dívida | Baixa → B=2, M=0, A=0 ; H=0,000<br>Alta → B=0, M=2, A=0 ; H=0,000 | 0,0000 | 1,0000 |
| Garantia | Nenhuma → B=1, M=2, A=0 ; H=0,918<br>Adequada → B=1, M=0, A=0 ; H=0,000 | 0,6887 | 0,3113 |
| Tempo de Emprego | Curto → B=0, M=2, A=0 ; H=0,000<br>Longo → B=2, M=0, A=0 ; H=0,000 | 0,0000 | 1,0000 |
| Residência | Alugada → B=0, M=2, A=0 ; H=0,000<br>Própria → B=2, M=0, A=0 ; H=0,000 | 0,0000 | 1,0000 |

Cálculos detalhados do atributo escolhido (Dívida):

- Ganho(Dívida) = 1,0000 − [(2/4)·0,0000 + (2/4)·0,0000] = 1,0000 − 0,0000 = **1,0000**

➡ **Atributo escolhido: Dívida** (maior ganho de informação) (empate com Tempo de Emprego, Residência; desempate pela ordem das colunas).

## Nó 10  —  Renda = $15 a $35k E História de Crédito = Boa E Dívida = Baixa

Exemplos (2): E25, E26  
Distribuição: B=2, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 11  —  Renda = $15 a $35k E História de Crédito = Boa E Dívida = Alta

Exemplos (2): E12, E22  
Distribuição: B=0, M=2, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 12  —  Renda = $15 a $35k E História de Crédito = Desconhecida

Exemplos (4): E2, E3, E16, E21  
Distribuição: B=0, M=2, A=2  
H(S) = − (2/4)·log₂(2/4) − (2/4)·log₂(2/4) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| Dívida | Baixa → B=0, M=2, A=0 ; H=0,000<br>Alta → B=0, M=0, A=2 ; H=0,000 | 0,0000 | 1,0000 |
| Garantia | Nenhuma → B=0, M=1, A=1 ; H=1,000<br>Adequada → B=0, M=1, A=1 ; H=1,000 | 1,0000 | 0,0000 |
| Tempo de Emprego | Curto → B=0, M=1, A=2 ; H=0,918<br>Médio → B=0, M=1, A=0 ; H=0,000 | 0,6887 | 0,3113 |
| Residência | Alugada → B=0, M=1, A=1 ; H=1,000<br>Própria → B=0, M=1, A=1 ; H=1,000 | 1,0000 | 0,0000 |

Cálculos detalhados do atributo escolhido (Dívida):

- Ganho(Dívida) = 1,0000 − [(2/4)·0,0000 + (2/4)·0,0000] = 1,0000 − 0,0000 = **1,0000**

➡ **Atributo escolhido: Dívida** (maior ganho de informação).

## Nó 13  —  Renda = $15 a $35k E História de Crédito = Desconhecida E Dívida = Baixa

Exemplos (2): E3, E21  
Distribuição: B=0, M=2, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 14  —  Renda = $15 a $35k E História de Crédito = Desconhecida E Dívida = Alta

Exemplos (2): E2, E16  
Distribuição: B=0, M=0, A=2  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 15  —  Renda = $15 a $35k E História de Crédito = Ruim

Exemplos (3): E14, E15, E20  
Distribuição: B=0, M=1, A=2  
H(S) = − (1/3)·log₂(1/3) − (2/3)·log₂(2/3) = 0,9183

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| Dívida | Baixa → B=0, M=0, A=1 ; H=0,000<br>Alta → B=0, M=1, A=1 ; H=1,000 | 0,6667 | 0,2516 |
| Tempo de Emprego | Curto → B=0, M=0, A=1 ; H=0,000<br>Médio → B=0, M=0, A=1 ; H=0,000<br>Longo → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 0,9183 |
| Residência | Alugada → B=0, M=0, A=2 ; H=0,000<br>Própria → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 0,9183 |

Cálculos detalhados do atributo escolhido (Tempo de Emprego):

- Ganho(Tempo de Emprego) = 0,9183 − [(1/3)·0,0000 + (1/3)·0,0000 + (1/3)·0,0000] = 0,9183 − 0,0000 = **0,9183**

➡ **Atributo escolhido: Tempo de Emprego** (maior ganho de informação) (empate com Residência; desempate pela ordem das colunas).

## Nó 16  —  Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Curto

Exemplos (1): E15  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 17  —  Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Médio

Exemplos (1): E14  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 18  —  Renda = $15 a $35k E História de Crédito = Ruim E Tempo de Emprego = Longo

Exemplos (1): E20  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 19  —  Renda = Acima de $35k

Exemplos (11): E5, E6, E8, E9, E10, E13, E23, E27, E28, E29, E30  
Distribuição: B=9, M=2, A=0  
H(S) = − (9/11)·log₂(9/11) − (2/11)·log₂(2/11) = 0,6840

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho |
| --- | --- | --- | --- |
| História de Crédito | Boa → B=5, M=0, A=0 ; H=0,000<br>Desconhecida → B=4, M=0, A=0 ; H=0,000<br>Ruim → B=0, M=2, A=0 ; H=0,000 | 0,0000 | 0,6840 |
| Dívida | Baixa → B=5, M=1, A=0 ; H=0,650<br>Alta → B=4, M=1, A=0 ; H=0,722 | 0,6827 | 0,0013 |
| Garantia | Nenhuma → B=5, M=0, A=0 ; H=0,000<br>Adequada → B=4, M=2, A=0 ; H=0,918 | 0,5009 | 0,1831 |
| Tempo de Emprego | Curto → B=1, M=0, A=0 ; H=0,000<br>Médio → B=5, M=2, A=0 ; H=0,863<br>Longo → B=3, M=0, A=0 ; H=0,000 | 0,5493 | 0,1348 |
| Residência | Alugada → B=4, M=0, A=0 ; H=0,000<br>Própria → B=5, M=2, A=0 ; H=0,863 | 0,5493 | 0,1348 |

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 0,6840 − [(5/11)·0,0000 + (4/11)·0,0000 + (2/11)·0,0000] = 0,6840 − 0,0000 = **0,6840**

➡ **Atributo escolhido: História de Crédito** (maior ganho de informação).

## Nó 20  —  Renda = Acima de $35k E História de Crédito = Boa

Exemplos (5): E9, E10, E13, E28, E30  
Distribuição: B=5, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 21  —  Renda = Acima de $35k E História de Crédito = Desconhecida

Exemplos (4): E5, E6, E27, E29  
Distribuição: B=4, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 22  —  Renda = Acima de $35k E História de Crédito = Ruim

Exemplos (2): E8, E23  
Distribuição: B=0, M=2, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.
