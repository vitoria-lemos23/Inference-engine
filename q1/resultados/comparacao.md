### Métricas comparativas

| Critério | ID3 | C4.5 | C4.5 podada | CART |
| --- | --- | --- | --- | --- |
| Nº de regras (folhas) | 14 | 14 | 12 | 11 |
| Condições por regra (média / máx.) | 2,64 / 3 | 2,86 / 4 | 2,75 / 4 | 3,00 / 4 |
| Profundidade da árvore | 3 | 4 | 4 | 6 |
| Atributos usados | 4 (Renda, Tempo de Emprego, Dívida, História de Crédito) | 5 (Renda, Residência, Dívida, Tempo de Emprego, História de Crédito) | 4 (Renda, Tempo de Emprego, História de Crédito, Dívida) | 4 (Renda, Tempo de Emprego, Dívida, História de Crédito) |
| Acurácia no treino (30 ex.) | 100,0% | 100,0% | 96,7% | 100,0% |
| Acurácia leave-one-out | 80,0% | 70,0% | 63,3% | 73,3% |
| Acurácia CV 5-fold estratificado (20 repetições) | 77,0% ± 8,4% | 71,7% ± 8,3% | 65,3% ± 8,0% | 69,7% ± 9,4% |
| Cobertura do espaço de entradas (216 combinações) | 216 (100,0%) | 200 (92,6%) | 200 (92,6%) | 208 (96,3%) |
| Perguntas ao usuário por consulta (média) | 2,44 | 2,46 | 1,96 | 3,30 |

### Concordância entre as bases

| Par de bases | Concordância nas 216 combinações possíveis |
| --- | --- |
| ID3 × C4.5 | 78,7% |
| ID3 × C4.5 podada | 81,5% |
| ID3 × CART | 90,7% |
| C4.5 × C4.5 podada | 91,7% |
| C4.5 × CART | 86,1% |
| C4.5 podada × CART | 88,9% |
