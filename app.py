"""Точка входу та маршрутизація режимів."""
import time
import streamlit as st
from data.generator import generate_data
from core.ahp import default_ahp
from core.anomaly import evaluate_detector
from core.klm import task_table
from ui.baseline import render as render_baseline
from ui.optimized import render as render_optimized
from ui.experiment import render as render_experiment

st.set_page_config(page_title="Інформаційно-аналітична панель",layout="wide")
mode=st.query_params.get("mode","baseline").lower()
if mode not in ("baseline","optimized"): mode="baseline"
admin=st.query_params.get("admin","0")=="1"
df,truth=generate_data()
# Для алгоритмів передаємо довгий формат з назвою показника.
_,_,_,_,_,cr,weights=default_ahp()
st.title("Інформаційно-аналітична панель")
st.caption(f"Режим: {mode.upper()} · дані: 7 діб · оновлення потоку імітоване")
if "tick" not in st.session_state: st.session_state.tick=0
st.session_state.tick+=1
# Розрахунок затримки обробки поточного кадру.
t0=time.perf_counter()
if mode=="baseline": render_baseline(df)
else: render_optimized(df,truth,weights)
lat=(time.perf_counter()-t0)*1000
st.sidebar.caption(f"Затримка оновлення: {lat:.1f} мс")
st.divider()
render_experiment(df,truth,mode)
if admin:
    st.divider(); st.header("Аналітика — службова вкладка")
    st.dataframe(task_table(),use_container_width=True)
    st.write("### AHP"); st.dataframe(weights,use_container_width=True); st.metric("CR",f"{cr:.4f}")
    precision,recall=evaluate_detector(df,truth); c1,c2=st.columns(2); c1.metric("Precision",f"{precision:.3f}"); c2.metric("Recall",f"{recall:.3f}")
    st.metric("Затримка поточного оновлення, мс",f"{lat:.2f}")
    st.info("CSV-аналіз результатів виконується кнопкою нижче; формат колонок: режим, псевдонім, t1, t2, t3, t4, помилки, а також опційно SUS1..SUS10.")
    import pandas as pd, io, math
    uploaded=st.file_uploader("CSV результатів",type="csv")
    if uploaded:
        r=pd.read_csv(uploaded)
        st.dataframe(r.head(),use_container_width=True)
        numeric=[c for c in ["t1","t2","t3","t4"] if c in r]
        if numeric: r["середній_час"]=r[numeric].mean(axis=1)
        if "помилки" in r: st.metric("Середня кількість помилок",f"{r['помилки'].mean():.2f}")
        if "SUS" not in r and all(f"SUS{i}" in r for i in range(1,11)):
            vals=[]
            for _,row in r.iterrows(): vals.append(sum(row[f"SUS{i}"]-1 if i%2 else 5-row[f"SUS{i}"] for i in range(1,11))*2.5)
            r["SUS"]=vals
        if "SUS" in r: st.metric("Середній SUS",f"{r['SUS'].mean():.1f}")
        if "режим" in r and "середній_час" in r:
            import scipy.stats as stats
            a=r[r["режим"].str.lower()=="baseline"]["середній_час"].dropna(); b=r[r["режим"].str.lower()=="optimized"]["середній_час"].dropna()
            if len(a)>1 and len(b)>1:
                t,p=stats.ttest_ind(a,b,equal_var=False); u,pu=stats.mannwhitneyu(a,b,alternative="two-sided")
                st.write(f"t-тест: t={t:.3f}, p={p:.4f}; Манн–Уїтні: U={u:.1f}, p={pu:.4f}")
                st.bar_chart(r.groupby("режим")["середній_час"].mean())
                import matplotlib.pyplot as plt
                from io import BytesIO
                fig1,ax=plt.subplots(figsize=(8,4)); r.boxplot(column="середній_час",by="режим",ax=ax); ax.set_title("Час виконання завдань за режимами"); ax.set_xlabel("Режим"); ax.set_ylabel("Середній час, с"); plt.suptitle(""); b1=BytesIO(); fig1.savefig(b1,format="png",dpi=300,bbox_inches="tight"); plt.close(fig1); b1.seek(0); st.download_button("Завантажити PNG: час",b1,"time_comparison.png","image/png")
                if "помилки" in r:
                    fig2,ax=plt.subplots(figsize=(8,4)); r.groupby("режим")["помилки"].mean().plot.bar(ax=ax); ax.set_title("Середня кількість помилок"); ax.set_ylabel("Помилки"); b2=BytesIO(); fig2.savefig(b2,format="png",dpi=300,bbox_inches="tight"); plt.close(fig2); b2.seek(0); st.download_button("Завантажити PNG: помилки",b2,"errors_comparison.png","image/png")
                if "SUS" in r:
                    fig3,ax=plt.subplots(figsize=(8,4)); r.groupby("режим")["SUS"].mean().plot.bar(ax=ax); ax.set_title("Середній SUS"); ax.set_ylabel("SUS, балів"); b3=BytesIO(); fig3.savefig(b3,format="png",dpi=300,bbox_inches="tight"); plt.close(fig3); b3.seek(0); st.download_button("Завантажити PNG: SUS",b3,"sus_comparison.png","image/png")
