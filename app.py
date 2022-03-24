import altair as alt
import pandas as pd
import numpy as np
import streamlit as st

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)    

def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)

st.set_page_config(layout="wide")

local_css("css/style.css")

st.title("Association between COVID-19 Cases with Vaccinations in the U.S.")

col1, col2, col3 = st.columns([5, 5, 2])

df1 = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])

vis1 = alt.Chart(df1).mark_line().encode(
    x=alt.X('a:Q'),
    y=alt.Y('b:Q')
).properties(
    width=480,
    height=580
)

vis2 = alt.Chart(df1).mark_line().encode(
    x=alt.X('a:Q'),
    y=alt.Y('c:Q')
).properties(
    width=480,
    height=180
)

vis3 = alt.Chart(df1).mark_line().encode(
    x=alt.X('b:Q'),
    y=alt.Y('c:Q')
).properties(
    width=480,
    height=380
)

df2 = pd.DataFrame(np.random.randn(20, 3), columns=['a', 'b', 'c'])

vis4 = alt.Chart(df2).mark_line().encode(
    x=alt.X('a:Q'),
    y=alt.Y('b:Q')
).properties(
    width=180,
    height=180
)

vis5 = alt.Chart(df2).mark_line().encode(
    x=alt.X('a:Q'),
    y=alt.Y('c:Q')
).properties(
    width=180,
    height=180
)

vis6 = alt.Chart(df2).mark_line().encode(
    x=alt.X('b:Q'),
    y=alt.Y('c:Q')
).properties(
    width=180,
    height=180
)

with col1:
    vis1

with col2:
    vis2
    vis3

with col3:
    vis4
    vis5
    vis6