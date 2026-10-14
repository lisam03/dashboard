"""Математичне оброблення часових рядів."""
from __future__ import annotations
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def moving_average(s: pd.Series, window: int = 15) -> pd.Series:
    """Ковзне середнє: $MA_t = \frac{1}{w}\sum_{i=0}^{w-1}x_{t-i}$."""
    return s.rolling(window, min_periods=1).mean()

def exponential_smoothing(s: pd.Series, alpha: float = 0.25) -> pd.Series:
    """Експоненційне згладжування: $S_t = \alpha X_t + (1-\alpha)S_{t-1}$."""
    return s.ewm(alpha=alpha, adjust=False).mean()

def holt_winters_forecast(s: pd.Series, horizon: int = 60, seasonal_periods: int = 60):
    """Прогноз Holt--Winters.

    Модель: $y_t = \ell_t + b_t + s_t + \varepsilon_t$.
    Довірчий інтервал наближено: $\hat y_t \pm 1.96\,SE(\hat y_t)$.
    """
    x = s.astype(float).dropna()
    if len(x) < 180:
        pred = np.repeat(x.iloc[-1], horizon)
        se = max(float(x.std()), 1e-6)
    else:
        model = ExponentialSmoothing(x, trend="add", seasonal="add", seasonal_periods=seasonal_periods, initialization_method="estimated").fit(optimized=True)
        fc = model.forecast(horizon)
        resid = x - model.fittedvalues
        se = max(float(resid.std()), 1e-6)
        pred = fc.to_numpy()
    future = pd.date_range(x.index[-1] + pd.Timedelta(minutes=1), periods=horizon, freq="min")
    out = pd.DataFrame({"Час": future, "Прогноз": pred, "Нижня межа": pred - 1.96*se, "Верхня межа": pred + 1.96*se})
    return out
