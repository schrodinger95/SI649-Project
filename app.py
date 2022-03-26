import altair as alt
from altair import datum
from vega_datasets import data
import pandas as pd
import numpy as np
import datetime
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

alt.data_transformers.disable_max_rows()

st.title("Association between COVID-19 Cases with Vaccinations in the U.S.")

col1, col2, col3 = st.columns([4, 6, 2])

d = st.date_input(
     "Filter data up to which date",
     value=datetime.date(2022, 3, 10),
     min_value=datetime.date(2020, 12, 14),
     max_value=datetime.date(2022, 3, 10))
st.write('The dashboard analyzed the data up to this time:', d)

year = d.year
month = d.month
day = d.day

## visulization 1

df1 = pd.read_csv('data/df1.csv')
df1['date'] = pd.to_datetime(df1['date'])

states = alt.topo_feature(data.us_10m.url, feature="states")

vis1_selection = alt.selection_single(fields=["location"])

vis1_colorCondition1 = alt.condition(vis1_selection, 
                                        alt.Color('covid_rate:Q', 
                                                    scale=alt.Scale(scheme='reds'), 
                                                    legend=alt.Legend(title='COVID case rate')), 
                                        alt.value("gray"))
vis1_colorCondition2 = alt.condition(vis1_selection, 
                                        alt.Color('avg_vaccine:Q', 
                                                    scale=alt.Scale(scheme='blues'), 
                                                    legend=alt.Legend(title='Avg vaccine dose')), 
                                        alt.value("gray"))

vis1_base = alt.Chart(states).mark_geoshape().project('albersUsa').encode(
    tooltip=["state:N", "covid_rate:Q", "avg_vaccine:Q"]
).transform_filter(
    datum.year == year & datum.month == month & datum.day == day & datum.location != 'PR'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(df1, 'id', fields=["year", "month", "day", "population", "covid_rate", "avg_vaccine", "location", "state"])
).add_selection(
    vis1_selection
)

vis1_map1 = vis1_base.encode(
    color=vis1_colorCondition1
)

vis1_map2 = vis1_base.encode(
    color=vis1_colorCondition2
)

vis1 = (vis1_map1 & vis1_map2).resolve_scale(
    color='independent'
).properties(
    title='COVID case rate vs. vaccine dose per capita by state'
).configure_view(
    stroke=None,
    continuousHeight=240,
    continuousWidth=280
)

with col1:
    vis1


age = ['All', 'age<12', '12<=age<18', '18<=age<65', 'age>=65']
type = ['All', 'Janssen', 'Moderna', 'Pfizer', 'Unknown']

with col2:
    place_holder_vis2 = st.empty()
    place_holder_vis3 = st.empty()
    genre = st.radio(
     "Classify the vaccine data by: ",
     ('Vaccine type', 'Vaccinated age'))

dict = {'Vaccine type': type, 'Vaccinated age': age}
showby = dict[genre]

# visualization 2

df2 = pd.read_csv('data/df2.csv')
df2['date'] = pd.to_datetime(df2['date'])

vis2_selection1 = alt.selection_multi(fields=['vaccine_type'], bind='legend', empty="none")

vis2_selection2 = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['week_date'], empty='none')
vis2_selection3=alt.selection_interval(bind="scales", encodings=["x"])

vis2_base = alt.Chart(df2).transform_filter(
    datum.year <= year & datum.month <= month & datum.day <= day
).transform_filter(
    alt.FieldOneOfPredicate(field='vaccine_type', oneOf=showby)
).transform_aggregate(
    sum_case='sum(new_case)',
    sum_vaccine='sum(new_vaccine)',
    week_date='max(date)',
    groupby=['vaccine_type', 'year', 'week']
).encode(
    x=alt.X('week_date:T', title='Date')
)      

vis2_line1 = vis2_base.mark_line(size=3).encode(
    y=alt.Y('sum_case:Q', title='New COVID case (solid)'),
    color=alt.value("red")
)

vis2_line2 = vis2_base.mark_line(size=3).encode(
    y=alt.Y('sum_vaccine:Q', title='New administered vaccine (dashed)'),
    strokeDash=alt.value([5,5]),
    color=alt.Color('vaccine_type', scale=alt.Scale(scheme='dark2'), title='Vaccine type'),
    opacity=alt.condition(vis2_selection1, alt.value(1), alt.value(0.2))
).add_selection(
    vis2_selection1
)

vis2_selectors = vis2_base.mark_point().encode(
    opacity=alt.value(0),
).add_selection(
    vis2_selection2
)

vis2_points1 = vis2_base.mark_point(size=80, filled=True).encode(
    y=alt.Y('sum_case:Q', axis=None),
    opacity=alt.condition(vis2_selection2, alt.value(1), alt.value(0)),
    tooltip=['week_date:T', 'sum_case:Q'],
    color=alt.value("red")
)

vis2_points2 = vis2_base.mark_point(size=80, filled=True).encode(
    y=alt.Y('sum_vaccine:Q', axis=None),
    color=alt.Color('vaccine_type', scale=alt.Scale(scheme='dark2'), title='Vaccine type'),
    opacity=alt.condition(vis2_selection2 & vis2_selection1, alt.value(1), alt.value(0)),
    tooltip=['week_date:T', 'vaccine_type:N', 'sum_vaccine:Q']
)

vis2_rules = vis2_base.mark_rule(color='gray', size=2).transform_filter(
    vis2_selection2
)

vis2 = alt.layer(
    vis2_line1, vis2_line2, vis2_selectors, vis2_points1, vis2_points2, vis2_rules
).add_selection(
    vis2_selection3
).resolve_scale(
    y='independent'
).properties(
    width=600, height=200
).configure_view(
    stroke=None
)

place_holder_vis2.altair_chart(vis2)

# visualization 3

df = pd.DataFrame(
     np.random.randn(200, 3),
     columns=['a', 'b', 'c'])

vis3 = alt.Chart(df).mark_bar().encode(
    x='a', y='b', color='c', tooltip=['a', 'b', 'c']
).properties(
    width=600, height=200
).configure_view(
    stroke=None
)

place_holder_vis3.altair_chart(vis3)

# visualization 4,5,6

source = pd.DataFrame({"category": [1, 2, 3, 4, 5, 6], "value": [4, 6, 10, 3, 7, 8]})

vis4 = alt.Chart(source).mark_arc(innerRadius=20).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='reds')),
).properties(
    width=165, height=165
).configure_view(
    stroke=None
)

vis5 = alt.Chart(source).mark_arc(innerRadius=20).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='blues')),
).properties(
    width=165, height=165
).configure_view(
    stroke=None
)

vis6 = alt.Chart(source).mark_arc(innerRadius=20).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='greens')),
).properties(
    width=165, height=165
).configure_view(
    stroke=None
)

with col3:
    vis4
    vis5
    vis6