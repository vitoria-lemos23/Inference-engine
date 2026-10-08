# Q1 — C4.5 — C4.5

Convenções: contagens por classe escritas como **B**=Baixo, **M**=Moderado, **A**=Alto; log₂ é o logaritmo na base 2 e 0·log₂0 = 0. Empates são resolvidos pela ordem das colunas da base (e, para a classe de uma folha, pela classe mais grave).

## Nó 1  —  (raiz)

Exemplos (30): E1, E2, E3, E4, E5, E6, E7, E8, E9, E10, E11, E12, E13, E14, E15, E16, E17, E18, E19, E20, E21, E22, E23, E24, E25, E26, E27, E28, E29, E30  
Distribuição: B=11, M=8, A=11  
H(S) = − (11/30)·log₂(11/30) − (8/30)·log₂(8/30) − (11/30)·log₂(11/30) = 1,5700

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=7, M=3, A=2 ; H=1,384<br>Desconhecida → B=4, M=2, A=4 ; H=1,522<br>Ruim → B=0, M=3, A=5 ; H=0,954 | 1,3156 | 0,2544 | 1,5656 | 0,1625 | sim |
| Dívida | Baixa → B=7, M=4, A=5 ; H=1,546<br>Alta → B=4, M=4, A=6 ; H=1,557 | 1,5511 | 0,0189 | 0,9968 | 0,0190 | não |
| Garantia | Nenhuma → B=6, M=4, A=8 ; H=1,530<br>Adequada → B=5, M=4, A=3 ; H=1,555 | 1,5401 | 0,0298 | 0,9710 | 0,0307 | não |
| Renda | $0 a $15k → B=0, M=1, A=7 ; H=0,544<br>$15 a $35k → B=2, M=5, A=4 ; H=1,495<br>Acima de $35k → B=9, M=2, A=0 ; H=0,684 | 0,9439 | 0,6261 | 1,5700 | 0,3988 | sim |
| Tempo de Emprego | Curto → B=1, M=3, A=7 ; H=1,241<br>Médio → B=5, M=3, A=3 ; H=1,539<br>Longo → B=5, M=2, A=1 ; H=1,299 | 1,3657 | 0,2042 | 1,5700 | 0,1301 | não |
| Residência | Alugada → B=4, M=3, A=9 ; H=1,420<br>Própria → B=7, M=5, A=2 ; H=1,432 | 1,4253 | 0,1447 | 0,9968 | 0,1452 | não |

Ganho médio dos candidatos = 0,2130. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados (todos os atributos, nó raiz):

- Ganho(História de Crédito) = 1,5700 − [(12/30)·1,3844 + (10/30)·1,5219 + (8/30)·0,9544] = 1,5700 − 1,3156 = **0,2544**
  - InfoDivisão(História de Crédito) = − (12/30)·log₂(12/30) − (10/30)·log₂(10/30) − (8/30)·log₂(8/30) = 1,5656; RazãoGanho = 0,2544 / 1,5656 = **0,1625**
- Ganho(Dívida) = 1,5700 − [(16/30)·1,5462 + (14/30)·1,5567] = 1,5700 − 1,5511 = **0,0189**
  - InfoDivisão(Dívida) = − (16/30)·log₂(16/30) − (14/30)·log₂(14/30) = 0,9968; RazãoGanho = 0,0189 / 0,9968 = **0,0190**
- Ganho(Garantia) = 1,5700 − [(18/30)·1,5305 + (12/30)·1,5546] = 1,5700 − 1,5401 = **0,0298**
  - InfoDivisão(Garantia) = − (18/30)·log₂(18/30) − (12/30)·log₂(12/30) = 0,9710; RazãoGanho = 0,0298 / 0,9710 = **0,0307**
- Ganho(Renda) = 1,5700 − [(8/30)·0,5436 + (11/30)·1,4949 + (11/30)·0,6840] = 1,5700 − 0,9439 = **0,6261**
  - InfoDivisão(Renda) = − (8/30)·log₂(8/30) − (11/30)·log₂(11/30) − (11/30)·log₂(11/30) = 1,5700; RazãoGanho = 0,6261 / 1,5700 = **0,3988**
- Ganho(Tempo de Emprego) = 1,5700 − [(11/30)·1,2407 + (11/30)·1,5395 + (8/30)·1,2988] = 1,5700 − 1,3657 = **0,2042**
  - InfoDivisão(Tempo de Emprego) = − (11/30)·log₂(11/30) − (11/30)·log₂(11/30) − (8/30)·log₂(8/30) = 1,5700; RazãoGanho = 0,2042 / 1,5700 = **0,1301**
- Ganho(Residência) = 1,5700 − [(16/30)·1,4197 + (14/30)·1,4316] = 1,5700 − 1,4253 = **0,1447**
  - InfoDivisão(Residência) = − (16/30)·log₂(16/30) − (14/30)·log₂(14/30) = 0,9968; RazãoGanho = 0,1447 / 0,9968 = **0,1452**

➡ **Atributo escolhido: Renda** (maior razão de ganho).

## Nó 2  —  Renda = $0 a $15k

Exemplos (8): E1, E4, E7, E11, E17, E18, E19, E24  
Distribuição: B=0, M=1, A=7  
H(S) = − (1/8)·log₂(1/8) − (7/8)·log₂(7/8) = 0,5436

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=0, M=1, A=2 ; H=0,918<br>Desconhecida → B=0, M=0, A=2 ; H=0,000<br>Ruim → B=0, M=0, A=3 ; H=0,000 | 0,3444 | 0,1992 | 1,5613 | 0,1276 | não |
| Dívida | Baixa → B=0, M=1, A=4 ; H=0,722<br>Alta → B=0, M=0, A=3 ; H=0,000 | 0,4512 | 0,0924 | 0,9544 | 0,0968 | não |
| Garantia | Nenhuma → B=0, M=0, A=5 ; H=0,000<br>Adequada → B=0, M=1, A=2 ; H=0,918 | 0,3444 | 0,1992 | 0,9544 | 0,2087 | não |
| Tempo de Emprego | Curto → B=0, M=0, A=4 ; H=0,000<br>Médio → B=0, M=0, A=2 ; H=0,000<br>Longo → B=0, M=1, A=1 ; H=1,000 | 0,2500 | 0,2936 | 1,5000 | 0,1957 | sim |
| Residência | Alugada → B=0, M=0, A=6 ; H=0,000<br>Própria → B=0, M=1, A=1 ; H=1,000 | 0,2500 | 0,2936 | 0,8113 | 0,3619 | sim |

Ganho médio dos candidatos = 0,2156. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (Residência):

- Ganho(Residência) = 0,5436 − [(6/8)·0,0000 + (2/8)·1,0000] = 0,5436 − 0,2500 = **0,2936**
  - InfoDivisão(Residência) = − (6/8)·log₂(6/8) − (2/8)·log₂(2/8) = 0,8113; RazãoGanho = 0,2936 / 0,8113 = **0,3619**

➡ **Atributo escolhido: Residência** (maior razão de ganho).

## Nó 3  —  Renda = $0 a $15k E Residência = Alugada

Exemplos (6): E1, E4, E7, E11, E18, E19  
Distribuição: B=0, M=0, A=6  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 4  —  Renda = $0 a $15k E Residência = Própria

Exemplos (2): E17, E24  
Distribuição: B=0, M=1, A=1  
H(S) = − (1/2)·log₂(1/2) − (1/2)·log₂(1/2) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| Dívida | Baixa → B=0, M=1, A=0 ; H=0,000<br>Alta → B=0, M=0, A=1 ; H=0,000 | 0,0000 | 1,0000 | 1,0000 | 1,0000 | sim |
| Garantia | Nenhuma → B=0, M=0, A=1 ; H=0,000<br>Adequada → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 1,0000 | 1,0000 | 1,0000 | sim |

Ganho médio dos candidatos = 1,0000. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (Dívida):

- Ganho(Dívida) = 1,0000 − [(1/2)·0,0000 + (1/2)·0,0000] = 1,0000 − 0,0000 = **1,0000**
  - InfoDivisão(Dívida) = − (1/2)·log₂(1/2) − (1/2)·log₂(1/2) = 1,0000; RazãoGanho = 1,0000 / 1,0000 = **1,0000**

➡ **Atributo escolhido: Dívida** (maior razão de ganho) (empate com Garantia; desempate pela ordem das colunas).

## Nó 5  —  Renda = $0 a $15k E Residência = Própria E Dívida = Baixa

Exemplos (1): E24  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 6  —  Renda = $0 a $15k E Residência = Própria E Dívida = Alta

Exemplos (1): E17  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 7  —  Renda = $15 a $35k

Exemplos (11): E2, E3, E12, E14, E15, E16, E20, E21, E22, E25, E26  
Distribuição: B=2, M=5, A=4  
H(S) = − (2/11)·log₂(2/11) − (5/11)·log₂(5/11) − (4/11)·log₂(4/11) = 1,4949

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=2, M=2, A=0 ; H=1,000<br>Desconhecida → B=0, M=2, A=2 ; H=1,000<br>Ruim → B=0, M=1, A=2 ; H=0,918 | 0,9777 | 0,5172 | 1,5726 | 0,3289 | sim |
| Dívida | Baixa → B=2, M=2, A=1 ; H=1,522<br>Alta → B=0, M=3, A=3 ; H=1,000 | 1,2372 | 0,2577 | 0,9940 | 0,2592 | não |
| Garantia | Nenhuma → B=1, M=4, A=3 ; H=1,406<br>Adequada → B=1, M=1, A=1 ; H=1,585 | 1,4545 | 0,0404 | 0,8454 | 0,0478 | não |
| Tempo de Emprego | Curto → B=0, M=3, A=3 ; H=1,000<br>Médio → B=0, M=1, A=1 ; H=1,000<br>Longo → B=2, M=1, A=0 ; H=0,918 | 0,9777 | 0,5172 | 1,4354 | 0,3603 | sim |
| Residência | Alugada → B=0, M=3, A=3 ; H=1,000<br>Própria → B=2, M=2, A=1 ; H=1,522 | 1,2372 | 0,2577 | 0,9940 | 0,2592 | não |

Ganho médio dos candidatos = 0,3180. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (Tempo de Emprego):

- Ganho(Tempo de Emprego) = 1,4949 − [(6/11)·1,0000 + (2/11)·1,0000 + (3/11)·0,9183] = 1,4949 − 0,9777 = **0,5172**
  - InfoDivisão(Tempo de Emprego) = − (6/11)·log₂(6/11) − (2/11)·log₂(2/11) − (3/11)·log₂(3/11) = 1,4354; RazãoGanho = 0,5172 / 1,4354 = **0,3603**

➡ **Atributo escolhido: Tempo de Emprego** (maior razão de ganho).

## Nó 8  —  Renda = $15 a $35k E Tempo de Emprego = Curto

Exemplos (6): E2, E12, E15, E16, E21, E22  
Distribuição: B=0, M=3, A=3  
H(S) = − (3/6)·log₂(3/6) − (3/6)·log₂(3/6) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=0, M=2, A=0 ; H=0,000<br>Desconhecida → B=0, M=1, A=2 ; H=0,918<br>Ruim → B=0, M=0, A=1 ; H=0,000 | 0,4591 | 0,5409 | 1,4591 | 0,3707 | sim |
| Dívida | Baixa → B=0, M=1, A=1 ; H=1,000<br>Alta → B=0, M=2, A=2 ; H=1,000 | 1,0000 | 0,0000 | 0,9183 | 0,0000 | não |
| Garantia | Nenhuma → B=0, M=2, A=2 ; H=1,000<br>Adequada → B=0, M=1, A=1 ; H=1,000 | 1,0000 | 0,0000 | 0,9183 | 0,0000 | não |
| Residência | Alugada → B=0, M=3, A=2 ; H=0,971<br>Própria → B=0, M=0, A=1 ; H=0,000 | 0,8091 | 0,1909 | 0,6500 | 0,2936 | sim |

Ganho médio dos candidatos = 0,1829. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 1,0000 − [(2/6)·0,0000 + (3/6)·0,9183 + (1/6)·0,0000] = 1,0000 − 0,4591 = **0,5409**
  - InfoDivisão(História de Crédito) = − (2/6)·log₂(2/6) − (3/6)·log₂(3/6) − (1/6)·log₂(1/6) = 1,4591; RazãoGanho = 0,5409 / 1,4591 = **0,3707**

➡ **Atributo escolhido: História de Crédito** (maior razão de ganho).

## Nó 9  —  Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Boa

Exemplos (2): E12, E22  
Distribuição: B=0, M=2, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 10  —  Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida

Exemplos (3): E2, E16, E21  
Distribuição: B=0, M=1, A=2  
H(S) = − (1/3)·log₂(1/3) − (2/3)·log₂(2/3) = 0,9183

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| Dívida | Baixa → B=0, M=1, A=0 ; H=0,000<br>Alta → B=0, M=0, A=2 ; H=0,000 | 0,0000 | 0,9183 | 0,9183 | 1,0000 | sim |
| Garantia | Nenhuma → B=0, M=0, A=1 ; H=0,000<br>Adequada → B=0, M=1, A=1 ; H=1,000 | 0,6667 | 0,2516 | 0,9183 | 0,2740 | não |
| Residência | Alugada → B=0, M=1, A=1 ; H=1,000<br>Própria → B=0, M=0, A=1 ; H=0,000 | 0,6667 | 0,2516 | 0,9183 | 0,2740 | não |

Ganho médio dos candidatos = 0,4739. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (Dívida):

- Ganho(Dívida) = 0,9183 − [(1/3)·0,0000 + (2/3)·0,0000] = 0,9183 − 0,0000 = **0,9183**
  - InfoDivisão(Dívida) = − (1/3)·log₂(1/3) − (2/3)·log₂(2/3) = 0,9183; RazãoGanho = 0,9183 / 0,9183 = **1,0000**

➡ **Atributo escolhido: Dívida** (maior razão de ganho).

## Nó 11  —  Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Baixa

Exemplos (1): E21  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 12  —  Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Desconhecida E Dívida = Alta

Exemplos (2): E2, E16  
Distribuição: B=0, M=0, A=2  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 13  —  Renda = $15 a $35k E Tempo de Emprego = Curto E História de Crédito = Ruim

Exemplos (1): E15  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 14  —  Renda = $15 a $35k E Tempo de Emprego = Médio

Exemplos (2): E3, E14  
Distribuição: B=0, M=1, A=1  
H(S) = − (1/2)·log₂(1/2) − (1/2)·log₂(1/2) = 1,0000

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Desconhecida → B=0, M=1, A=0 ; H=0,000<br>Ruim → B=0, M=0, A=1 ; H=0,000 | 0,0000 | 1,0000 | 1,0000 | 1,0000 | sim |
| Dívida | Baixa → B=0, M=1, A=0 ; H=0,000<br>Alta → B=0, M=0, A=1 ; H=0,000 | 0,0000 | 1,0000 | 1,0000 | 1,0000 | sim |
| Residência | Alugada → B=0, M=0, A=1 ; H=0,000<br>Própria → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 1,0000 | 1,0000 | 1,0000 | sim |

Ganho médio dos candidatos = 1,0000. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 1,0000 − [(1/2)·0,0000 + (1/2)·0,0000] = 1,0000 − 0,0000 = **1,0000**
  - InfoDivisão(História de Crédito) = − (1/2)·log₂(1/2) − (1/2)·log₂(1/2) = 1,0000; RazãoGanho = 1,0000 / 1,0000 = **1,0000**

➡ **Atributo escolhido: História de Crédito** (maior razão de ganho) (empate com Dívida, Residência; desempate pela ordem das colunas).

## Nó 15  —  Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Desconhecida

Exemplos (1): E3  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 16  —  Renda = $15 a $35k E Tempo de Emprego = Médio E História de Crédito = Ruim

Exemplos (1): E14  
Distribuição: B=0, M=0, A=1  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Alto**.

## Nó 17  —  Renda = $15 a $35k E Tempo de Emprego = Longo

Exemplos (3): E20, E25, E26  
Distribuição: B=2, M=1, A=0  
H(S) = − (2/3)·log₂(2/3) − (1/3)·log₂(1/3) = 0,9183

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=2, M=0, A=0 ; H=0,000<br>Ruim → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 0,9183 | 0,9183 | 1,0000 | sim |
| Dívida | Baixa → B=2, M=0, A=0 ; H=0,000<br>Alta → B=0, M=1, A=0 ; H=0,000 | 0,0000 | 0,9183 | 0,9183 | 1,0000 | sim |
| Garantia | Nenhuma → B=1, M=1, A=0 ; H=1,000<br>Adequada → B=1, M=0, A=0 ; H=0,000 | 0,6667 | 0,2516 | 0,9183 | 0,2740 | não |

Ganho médio dos candidatos = 0,6961. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 0,9183 − [(2/3)·0,0000 + (1/3)·0,0000] = 0,9183 − 0,0000 = **0,9183**
  - InfoDivisão(História de Crédito) = − (2/3)·log₂(2/3) − (1/3)·log₂(1/3) = 0,9183; RazãoGanho = 0,9183 / 0,9183 = **1,0000**

➡ **Atributo escolhido: História de Crédito** (maior razão de ganho) (empate com Dívida; desempate pela ordem das colunas).

## Nó 18  —  Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Boa

Exemplos (2): E25, E26  
Distribuição: B=2, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 19  —  Renda = $15 a $35k E Tempo de Emprego = Longo E História de Crédito = Ruim

Exemplos (1): E20  
Distribuição: B=0, M=1, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.

## Nó 20  —  Renda = Acima de $35k

Exemplos (11): E5, E6, E8, E9, E10, E13, E23, E27, E28, E29, E30  
Distribuição: B=9, M=2, A=0  
H(S) = − (9/11)·log₂(9/11) − (2/11)·log₂(2/11) = 0,6840

| Atributo | Divisão (valor → B, M, A ; H) | H(S∣A) | Ganho | InfoDivisão | Razão de ganho | Ganho ≥ média? |
| --- | --- | --- | --- | --- | --- | --- |
| História de Crédito | Boa → B=5, M=0, A=0 ; H=0,000<br>Desconhecida → B=4, M=0, A=0 ; H=0,000<br>Ruim → B=0, M=2, A=0 ; H=0,000 | 0,0000 | 0,6840 | 1,4949 | 0,4576 | sim |
| Dívida | Baixa → B=5, M=1, A=0 ; H=0,650<br>Alta → B=4, M=1, A=0 ; H=0,722 | 0,6827 | 0,0013 | 0,9940 | 0,0013 | não |
| Garantia | Nenhuma → B=5, M=0, A=0 ; H=0,000<br>Adequada → B=4, M=2, A=0 ; H=0,918 | 0,5009 | 0,1831 | 0,9940 | 0,1842 | não |
| Tempo de Emprego | Curto → B=1, M=0, A=0 ; H=0,000<br>Médio → B=5, M=2, A=0 ; H=0,863<br>Longo → B=3, M=0, A=0 ; H=0,000 | 0,5493 | 0,1348 | 1,2407 | 0,1086 | não |
| Residência | Alugada → B=4, M=0, A=0 ; H=0,000<br>Própria → B=5, M=2, A=0 ; H=0,863 | 0,5493 | 0,1348 | 0,9457 | 0,1425 | não |

Ganho médio dos candidatos = 0,2276. Só concorrem os atributos com ganho ≥ média; entre eles vence a maior **razão de ganho**.

Cálculos detalhados do atributo escolhido (História de Crédito):

- Ganho(História de Crédito) = 0,6840 − [(5/11)·0,0000 + (4/11)·0,0000 + (2/11)·0,0000] = 0,6840 − 0,0000 = **0,6840**
  - InfoDivisão(História de Crédito) = − (5/11)·log₂(5/11) − (4/11)·log₂(4/11) − (2/11)·log₂(2/11) = 1,4949; RazãoGanho = 0,6840 / 1,4949 = **0,4576**

➡ **Atributo escolhido: História de Crédito** (maior razão de ganho).

## Nó 21  —  Renda = Acima de $35k E História de Crédito = Boa

Exemplos (5): E9, E10, E13, E28, E30  
Distribuição: B=5, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 22  —  Renda = Acima de $35k E História de Crédito = Desconhecida

Exemplos (4): E5, E6, E27, E29  
Distribuição: B=4, M=0, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Baixo**.

## Nó 23  —  Renda = Acima de $35k E História de Crédito = Ruim

Exemplos (2): E8, E23  
Distribuição: B=0, M=2, A=0  
H(S) = 0 (nó puro)

➡ **Folha** (nó puro): classe = **Moderado**.
