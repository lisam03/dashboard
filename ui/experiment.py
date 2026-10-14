"""Модуль користувацького тестування."""
from __future__ import annotations
import time
import streamlit as st
import pandas as pd
from core.processing import holt_winters_forecast

def _answers(df, truth):
    last=df.sort_values("Час").groupby("Об'єкт").tail(1)
    scores=last[["Навантаження (%)","Температура (°C)","Споживання (кВт)","Помилки (шт/год)"]].rank(pct=True).mean(axis=1)
    worst=last.loc[scores.idxmax(),"Об'єкт"]
    cutoff=df["Час"].max()-pd.Timedelta(hours=24)
    count=sum((truth["Час"]>=cutoff)&(truth["Час"]<=df["Час"].max()))
    drift=truth[truth["Тип"]=="дрейф"]["Об'єкт"].iloc[0]
    load_obj=sorted(df["Об'єкт"].unique())[0]
    g=df[df["Об'єкт"]==load_obj].set_index("Час")["Навантаження (%)"].tail(720)
    fc=holt_winters_forecast(g,60)
    exceed=bool((fc["Прогноз"]>90).any())
    return [worst,str(int(count)),drift,"Так" if exceed else "Ні"],load_obj

def render(df,truth,mode):
    st.subheader("Користувацьке тестування")
    if "exp_started" not in st.session_state:
        st.session_state.exp_started=False
    if not st.session_state.exp_started:
        alias=st.text_input("Псевдонім")
        if st.button("Почати",disabled=not alias): st.session_state.update(exp_started=True,alias=alias,task=0,start=time.perf_counter(),times=[],errors=0,answers=[]); st.rerun()
        return
    correct,nobj=_answers(df,truth); questions=["Який об'єкт зараз у найгіршому стані?","Скільки аномалій було за останні 24 год?","На якому об'єкті зростає температура (дрейф)?",f"Чи перевищить навантаження {nobj} поріг 90 % протягом найближчої години?"]
    i=st.session_state.task
    if i<4:
        st.markdown(f"### Завдання {i+1} з 4"); st.write(questions[i]); opts=sorted(df["Об'єкт"].unique()) if i in (0,2) else (["0","1","2","3","4","5"] if i==1 else ["Так","Ні"])
        ans=st.selectbox("Ваша відповідь",opts,key=f"ans_{i}")
        if st.button("Відповісти"):
            elapsed=time.perf_counter()-st.session_state.start; st.session_state.times.append(elapsed); st.session_state.answers.append(ans); st.session_state.errors += int(str(ans)!=str(correct[i])); st.session_state.task+=1; st.session_state.start=time.perf_counter(); st.rerun()
    else:
        times=st.session_state.times; code=";".join([mode,st.session_state.alias,*[f"{x:.3f}" for x in times],str(st.session_state.errors)])
        st.success("Тест завершено")
        st.code(code); st.write("Скопіюйте один рядок коду результату у Google Form.")
        st.markdown("[Відкрити анкету SUS]("+SUS_FORM_URL+")")
SUS_FORM_URL="https://forms.gle/ВАША_ФОРМА_SUS"
