"""Оптимізований інтерфейс."""
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data.generator import METRICS
from core.processing import exponential_smoothing, holt_winters_forecast
from core.anomaly import detect_series

def render(df, truth, weights):
    t0=time.perf_counter()
    st.subheader("OPTIMIZED — інформаційно-аналітична панель")
    latest=df.sort_values("Час").groupby("Об'єкт").tail(1).set_index("Об'єкт")
    kpis=[("Середнє навантаження", "Навантаження (%)", 90),("Макс. температура", "Температура (°C)", 55),("Споживання", "Споживання (кВт)", 160),("Помилки", "Помилки (шт/год)", 6)]
    cols=st.columns(4)
    for c,(label,metric,thr) in zip(cols,kpis):
        val=float(df[metric].tail(120).mean()) if metric!="Температура (°C)" else float(df[metric].tail(120).max())
        status="КРИТИЧНО" if val>=thr else ("УВАГА" if val>=thr*.85 else "НОРМА")
        icon={"КРИТИЧНО":"🔴","УВАГА":"🟡","НОРМА":"🟢"}[status]
        c.metric(label,f"{val:.1f}",f"{icon} {status}")
    st.markdown("### Стан об'єктів")
    matrix=[]
    for obj in sorted(df["Об'єкт"].unique()):
        row={"Об'єкт":obj}
        for m in METRICS:
            s=df[df["Об'єкт"]==obj][m]
            z=abs((s.iloc[-1]-s.tail(120).mean())/(s.tail(120).std()+1e-9))
            row[m]=round(float(z),2)
        matrix.append(row)
    heat=pd.DataFrame(matrix).set_index("Об'єкт")
    st.dataframe(heat.style.background_gradient(axis=None),use_container_width=True)
    st.markdown("### Стрічка подій")
    events=[]
    for (obj,metric),g in df.groupby(["Об'єкт","Показник"]):
        flags=detect_series(g.set_index("Час")[metric])["anomaly"]
        for ts in flags[flags].index[-20:]: events.append((ts,obj,metric))
    for ts,obj,metric in sorted(events,reverse=True)[:8]: st.warning(f"⚠️ {ts:%d.%m %H:%M} — {obj}, {metric}")
    objs=sorted(df["Об'єкт"].unique()); obj=st.selectbox("Детальний об'єкт",objs)
    metric=st.selectbox("Детальний показник",list(METRICS))
    g=df[df["Об'єкт"]==obj].set_index("Час")[metric].tail(720)
    smooth=exponential_smoothing(g,.25); fc=holt_winters_forecast(g,60)
    flags=detect_series(g)["anomaly"]
    fig=go.Figure(); fig.add_trace(go.Scatter(x=g.index,y=g,name="Сирі дані",line=dict(width=1,opacity=.25))); fig.add_trace(go.Scatter(x=smooth.index,y=smooth,name="Згладжування")); fig.add_trace(go.Scatter(x=fc["Час"],y=fc["Прогноз"],name="Прогноз")); fig.add_trace(go.Scatter(x=fc["Час"],y=fc["Верхня межа"],line=dict(width=0),showlegend=False)); fig.add_trace(go.Scatter(x=fc["Час"],y=fc["Нижня межа"],fill="tonexty",line=dict(width=0),name="95% інтервал"));
    ax=g[flags]; fig.add_trace(go.Scatter(x=ax.index,y=ax,name="Аномалії",mode="markers",marker=dict(size=9,symbol="x")))
    fig.update_layout(height=500); st.plotly_chart(fig,use_container_width=True)
    st.caption(f"Оновлення інтерфейсу: {(time.perf_counter()-t0)*1000:.1f} мс")
