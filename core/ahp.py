"""Аналітичний метод ієрархій (AHP)."""
from __future__ import annotations
import numpy as np
import pandas as pd

def ahp_weights(matrix: np.ndarray):
    """Власний вектор: $Aw=\lambda_{max}w$; $CI=(\lambda_{max}-n)/(n-1)$; $CR=CI/RI$."""
    vals, vecs = np.linalg.eig(matrix)
    i=int(np.argmax(vals.real)); lam=float(vals[i].real)
    w=np.abs(vecs[:,i].real); w=w/w.sum()
    n=len(w); ci=(lam-n)/(n-1) if n>1 else 0
    ri={1:0,2:0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45}.get(n,1.49)
    cr=ci/ri if ri else 0
    return w, lam, ci, cr

def default_ahp():
    criteria=["Критичність","Частота використання","Швидкість зміни","Зв'язок з рішенням"]
    A=np.array([[1,3,2,2],[1/3,1,1/2,1/2],[1/2,2,1,1],[1/2,2,1,1]],float)
    w,lam,ci,cr=ahp_weights(A)
    widgets=["KPI","Теплова карта","Стрічка подій","Детальний графік","Прогноз","Фільтри","Стан об'єктів","Тренд"]
    scores=np.array([[9,8,7,9],[9,7,9,9],[10,8,10,10],[8,7,8,10],[7,6,10,9],[4,9,3,4],[8,8,8,8],[6,7,9,7]],float)
    ww=scores@w; ww=ww/ww.sum()
    return criteria,A,w,lam,ci,cr,pd.DataFrame({"Віджет":widgets,"Вага":ww}).sort_values("Вага",ascending=False)
