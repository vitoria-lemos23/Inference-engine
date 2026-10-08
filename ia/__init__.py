"""Pacote de apoio da Lista 1 de IA (2026.2).

Módulos:
    base        -- leitura/representação de bases de exemplos categóricas
    arvores     -- ID3, C4.5 (razão de ganho + poda pessimista) e CART (Gini, divisão binária)
    regras      -- extração de regras SE...ENTÃO a partir das árvores
    relatorio   -- passo a passo (cálculos), árvore em texto/DOT/PNG, tabelas em Markdown
    prism       -- algoritmo PRISM (regras diretas, "separar e conquistar")
    metricas    -- acurácia, precisão, revocação, F1, matriz de confusão (sem depender de sklearn)
"""
