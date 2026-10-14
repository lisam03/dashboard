"""KLM-GOMS та закон Хіка--Хаймана."""
from __future__ import annotations
import math
K,P,H,M,B=.28,1.1,.4,1.35,.1

def klm_time(sequence: str):
    """$T_{KLM}=n_KK+n_PP+n_HH+n_MM+n_BB$."""
    return sum({'K':K,'P':P,'H':H,'M':M,'B':B}.get(c,0) for c in sequence)

def hick_time(n: int, b: float=.35):
    """Закон Хіка--Хаймана: $T=b\log_2(n+1)$."""
    return b*math.log2(n+1)

def task_table():
    tasks=[
        ("Найгірший об'єкт", "MMKPKB", "MMKPKB"),
        ("Аномалії за 24 год", "MPKPKB", "MPKPKB"),
        ("Об'єкт із дрейфом температури", "MMPKKB", "MPKKB"),
        ("Прогноз > 90 %", "MMHMPKPKB", "MMPKKB"),
    ]
    rows=[]
    for name,base,opt in tasks: rows.append({"Завдання":name,"BASELINE":klm_time(base)+hick_time(16),"OPTIMIZED":klm_time(opt)+hick_time(7),"Оператори BASELINE":base,"Оператори OPTIMIZED":opt})
    return pd.DataFrame(rows)
