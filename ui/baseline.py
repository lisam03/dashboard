"""Інтерфейс BASELINE."""
import streamlit as st
import plotly.express as px
from data.generator import METRICS

def render(df):
    st.subheader("BASELINE — типовий інформаційний dashboard")
    st.caption("Сирі дані без моделей, згладжування, аномалій та зведених KPI.")
    with st.sidebar:
        objects=st.multiselect("Об'єкти", sorted(df["Об'єкт"].unique()), default=sorted(df["Об'єкт"].unique()))
        metrics=st.multiselect("Показники", list(METRICS), default=list(METRICS))
        hours=st.slider("Останні години", 1, 168, 24)
    x=df[df["Об'єкт"].isin(objects) & df["Час"].ge(df["Час"].max()-__import__('pandas').Timedelta(hours=hours))]
    cols=st.columns(3)
    for i,(obj,metric) in enumerate([(o,m) for o in objects for m in metrics]):
        with cols[i%3]:
            g=x[x["Об'єкт"]==obj]
            fig=px.line(g,x="Час",y=metric,title=f"{obj} — {metric}")
            fig.update_layout(height=260,margin=dict(l=10,r=10,t=45,b=10),showlegend=True)
            st.plotly_chart(fig,use_container_width=True,key=f"base_{obj}_{metric}")
