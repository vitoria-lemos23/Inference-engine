"""Carga, limpeza e divisão do conjunto Pima Indians Diabetes (Kaggle: uciml/pima-indians-diabetes-database)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = RAIZ / "data" / "diabetes.csv"

COLUNAS = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI",
           "DiabetesPedigreeFunction", "Age", "Outcome"]
# nomes usados nas regras e relatórios (com unidade)
NOMES = {
    "Pregnancies": "Gestações",
    "Glucose": "Glicose",
    "BloodPressure": "PressãoDiastólica",
    "SkinThickness": "DobraTríceps",
    "Insulin": "Insulina",
    "BMI": "IMC",
    "DiabetesPedigreeFunction": "HistóricoFamiliar",
    "Age": "Idade",
}
DESCRICAO = {
    "Gestações": "número de gestações",
    "Glicose": "glicose plasmática (2 h no teste oral de tolerância), mg/dL",
    "PressãoDiastólica": "pressão arterial diastólica, mm Hg",
    "DobraTríceps": "espessura da dobra cutânea do tríceps, mm",
    "Insulina": "insulina sérica (2 h), µU/mL",
    "IMC": "índice de massa corporal, kg/m²",
    "HistóricoFamiliar": "função de pedigree de diabetes (risco pelo histórico familiar)",
    "Idade": "idade, anos",
}
# zero fisiologicamente impossível => valor ausente codificado como 0 no arquivo original
ZERO_E_AUSENTE = ["Glicose", "PressãoDiastólica", "DobraTríceps", "Insulina", "IMC"]
ATRIBUTOS = [NOMES[c] for c in COLUNAS[:-1]]
CLASSES = {0: "Sem diabetes", 1: "Diabetes"}
SEMENTE = 42
FRACAO_TESTE = 0.25


def carregar(caminho=None):
    """Lê o CSV, confere o esquema e devolve um DataFrame com colunas em português; zeros impossíveis viram NaN."""
    caminho = Path(caminho or CAMINHO_PADRAO)
    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo {caminho} não encontrado. Baixe o 'diabetes.csv' do Kaggle "
            "(https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database) e salve em data/diabetes.csv, "
            "ou informe outro caminho com --dados.")
    df = pd.read_csv(caminho)
    faltam = [c for c in COLUNAS if c not in df.columns]
    if faltam:
        raise ValueError(f"Colunas ausentes no CSV: {faltam}. Esperado: {COLUNAS}")
    df = df[COLUNAS].rename(columns=NOMES).rename(columns={"Outcome": "Diabetes"})
    if not set(df["Diabetes"].unique()) <= {0, 1}:
        raise ValueError("A coluna Outcome deve conter apenas 0 e 1.")
    df = df.astype(float).assign(Diabetes=df["Diabetes"].astype(int))
    for c in ZERO_E_AUSENTE:
        df[c] = df[c].replace(0, np.nan)
    return df


def dividir(df, semente=SEMENTE, fracao_teste=FRACAO_TESTE):
    """Divisão estratificada treino/teste (a mesma nas Questões 3 e 4). Retorna (treino, teste) como DataFrames."""
    idx_tr, idx_te = train_test_split(df.index, test_size=fracao_teste, stratify=df["Diabetes"], random_state=semente)
    return df.loc[sorted(idx_tr)], df.loc[sorted(idx_te)]


def resumo_ausentes(df):
    return {c: int(df[c].isna().sum()) for c in ZERO_E_AUSENTE}
