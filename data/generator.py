"""Генератор детермінованих даних моніторингу.

Дані містять добову сезонність, тренд, гаусів шум та рівно 5 відомих аномалій.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

OBJECTS = [f"Об'єкт {i}" for i in range(1, 7)]
METRICS = {"Навантаження (%)": "%", "Температура (°C)": "°C", "Споживання (кВт)": "кВт", "Помилки (шт/год)": "шт/год"}

def generate_data(seed: int = 42, days: int = 7):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-05", periods=days * 24 * 60, freq="min")
    rows = []
    for oi, obj in enumerate(OBJECTS):
        t = np.arange(len(idx)) / 1440.0
        daily = np.sin(2*np.pi*t - 0.7) + 0.35*np.sin(4*np.pi*t + oi)
        trend = t / days
        load = 58 + 10*daily + (oi-2)*1.8 + 2.0*trend + rng.normal(0, 2.0, len(idx))
        temp = 30 + 5*daily + oi*0.6 + 0.8*trend + rng.normal(0, 0.9, len(idx))
        power = 110 + 22*daily + oi*3 + 3*trend + rng.normal(0, 3.0, len(idx))
        errors = np.maximum(0, 1.5 + 0.7*np.maximum(daily, -0.2) + oi*0.08 + rng.normal(0, 0.55, len(idx)))
        for j, ts in enumerate(idx):
            rows.append([ts, obj, load[j], temp[j], power[j], errors[j]])
    df = pd.DataFrame(rows, columns=["Час", "Об'єкт", *METRICS.keys()])
    # Рівно 5 аномалій, кожна має окремий тип.
    anomalies = [
        ("Об'єкт 1", "Навантаження (%)", idx[900], "сплеск"),
        ("Об'єкт 2", "Споживання (кВт)", idx[2500], "провал"),
        ("Об'єкт 3", "Температура (°C)", idx[5600], "дрейф"),
        ("Об'єкт 4", "Помилки (шт/год)", idx[7000], "зростання помилок"),
        ("Об'єкт 5", "Температура (°C)", idx[8200], "перегрів"),
    ]
    for obj, metric, ts, typ in anomalies:
        mask = (df["Об'єкт"] == obj) & (df["Час"] >= ts) & (df["Час"] < ts + pd.Timedelta(minutes=30))
        n = mask.sum()
        if typ == "сплеск": df.loc[mask, metric] += 24
        elif typ == "провал": df.loc[mask, metric] -= 45
        elif typ == "дрейф": df.loc[mask, metric] += np.linspace(0, 12, n)
        elif typ == "зростання помилок": df.loc[mask, metric] += np.linspace(2, 12, n)
        elif typ == "перегрів": df.loc[mask, metric] += 18
    truth = pd.DataFrame(anomalies, columns=["Об'єкт", "Показник", "Час", "Тип"])
    return df, truth
