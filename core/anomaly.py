"""Виявлення аномалій трьома методами та голосуванням 2 з 3."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_series(s: pd.Series, window: int = 120, z_threshold: float = 3.0):
    """Z-оцінка: $z_t = (x_t-\mu_t)/\sigma_t$; IQR: $[Q_1-1.5IQR,Q_3+1.5IQR]$.
    Isolation Forest оцінює ізольованість точок у просторі ознак.
    Фінальне рішення: $A_t=1$, якщо щонайменше два з трьох детекторів дають 1.
    """
    x = s.astype(float)
    med = x.rolling(window, min_periods=max(20, window//4)).median()
    std = x.rolling(window, min_periods=max(20, window//4)).std().replace(0, np.nan)
    z = ((x-med)/std).abs().fillna(0) > z_threshold
    q1 = x.rolling(window, min_periods=max(20, window//4)).quantile(.25)
    q3 = x.rolling(window, min_periods=max(20, window//4)).quantile(.75)
    iqr = q3-q1
    iqr_flag = ((x < q1-1.5*iqr) | (x > q3+1.5*iqr)).fillna(False)
    arr = x.fillna(x.median()).to_numpy().reshape(-1,1)
    iso = IsolationForest(contamination=0.01, random_state=42).fit_predict(arr) == -1
    iso_flag = pd.Series(iso, index=x.index)
    vote = z.astype(int) + iqr_flag.astype(int) + iso_flag.astype(int)
    return pd.DataFrame({"z": z, "iqr": iqr_flag, "isolation": iso_flag, "anomaly": vote >= 2})

def evaluate_detector(df: pd.DataFrame, truth: pd.DataFrame):
    preds=[]
    for obj, g in df.groupby("Об'єкт"):
        g=g.sort_values("Час").set_index("Час")
        for metric in [c for c in df.columns if c not in ["Час","Об'єкт"]]:
            flags = detect_series(g[metric])["anomaly"]
            for ts in flags[flags].index:
                preds.append((obj, metric, ts))
    pred = set(preds)
    # Відомі аномалії розгортаються на 30 хвилин; подія вважається знайденою,
    # якщо хоча б одна точка з 30-хвилинного інтервалу позначена.
    tp=0
    for r in truth.itertuples():
        if any((r[1], r[2], t) in pred for t in pd.date_range(r[3], r[3]+pd.Timedelta(minutes=29), freq="min")): tp += 1
    fn=len(truth)-tp
    fp=max(0, len(pred)-tp)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    return precision, recall
