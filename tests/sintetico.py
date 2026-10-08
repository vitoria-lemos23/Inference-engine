"""Gera um CSV SINTÉTICO com o esquema do Pima (Kaggle) só para testar o código. NÃO são dados reais."""
import numpy as np
import pandas as pd


def pima_sintetico(n=768, semente=0):
    r = np.random.default_rng(semente)
    idade = r.integers(21, 70, n)
    preg = np.clip(r.poisson(3.8, n), 0, 17)
    imc = np.clip(r.normal(32, 7, n), 18, 60)
    glic = np.clip(r.normal(120, 30, n), 50, 200)
    pa = np.clip(r.normal(70, 12, n), 40, 110)
    dobra = np.clip(r.normal(29, 10, n), 7, 99)
    ins = np.clip(r.gamma(2, 60, n), 14, 846)
    ped = np.clip(r.gamma(2, 0.25, n), 0.08, 2.4)
    z = -9.0 + 0.035 * glic + 0.07 * imc + 0.02 * idade + 0.8 * ped
    y = (r.random(n) < 1 / (1 + np.exp(-z))).astype(int)
    df = pd.DataFrame(dict(Pregnancies=preg, Glucose=glic.round(), BloodPressure=pa.round(), SkinThickness=dobra.round(),
                           Insulin=ins.round(), BMI=imc.round(1), DiabetesPedigreeFunction=ped.round(3), Age=idade,
                           Outcome=y))
    for c, p in [("Glucose", .007), ("BloodPressure", .045), ("SkinThickness", .29), ("Insulin", .49), ("BMI", .014)]:
        df.loc[r.random(n) < p, c] = 0
    return df
