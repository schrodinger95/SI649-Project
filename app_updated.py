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

col1, col2, col3 = st.columns([4.5, 5.5, 2])
col4, col5= st.columns([8,4])
col6, col7 =st.columns([4.5,8])

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
    continuousHeight=270,
    continuousWidth=330
)

with col1:
    vis1


age = ['All', 'age<12', '12<=age<18', '18<=age<65', 'age>=65']
type = ['All', 'Janssen', 'Moderna', 'Pfizer', 'Unknown']

with col2:
    place_holder_vis2 = st.empty()
    place_holder_vis3 = st.empty()
    genre = st.radio(
        "Classify the vaccination data by: ",
        ('Vaccine type', 'Age group'))
    st.caption('Note: Data on vaccination status by age group were incompletely recorded before 2021.5.14 and therefore are not included in analysis.')

title_dict = {'Vaccine type': 'Vaccine type', 'Age group': 'Age group'}
filter_dict = {'Vaccine type': type, 'Age group': age}
title = title_dict[genre]
showby = filter_dict[genre]

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
    y=alt.Y('sum_case:Q', title='COVID cases (solid)'),
    color=alt.value("red")
)

vis2_line2 = vis2_base.mark_line(size=3).encode(
    y=alt.Y('sum_vaccine:Q', title='Vaccines (dashed)'),
    strokeDash=alt.value([5,5]),
    color=alt.Color('vaccine_type', scale=alt.Scale(scheme='dark2'), title=title),
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
    color=alt.Color('vaccine_type', scale=alt.Scale(scheme='dark2'), title=title),
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
    width=550, height=200, title='COVID-19 cases and vaccinations by week'
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
    width=550, height=200
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
    width=180, height=180
).configure_view(
    stroke=None
)

vis5 = alt.Chart(source).mark_arc(innerRadius=20).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='blues')),
).properties(
    width=180, height=180
).configure_view(
    stroke=None
)

vis6 = alt.Chart(source).mark_arc(innerRadius=20).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='greens')),
).properties(
    width=180, height=180
).configure_view(
    stroke=None
)

with col3:
    vis4
    vis5
    vis6

##############################   The second row   ##############################


# Vaccination rate of all ages  #

age_url="https://raw.githubusercontent.com/schrodinger95/SI649-Project/main/data/agegroup.csv"
df3=pd.read_csv(age_url)
df3['Date'] = pd.to_datetime(df3['Date'])
datestr=str(year)+'-'+str(month)+'-'+str(day)
df3_date=df3[df3.Date==datestr]  # data used for the date
age = ['All', '5<age<12', '12<=age<18', '18<=age<65', 'age>=65']  # age group

with col4:
    #covid_case_placeholder=st.empty()
    show_number=st.slider('The number of states you want to see: ', 1, 50, 5) # choose the number to filter
with col5:
    high_low=st.radio(
     "View the data from: ",
     ('Highest to lowest', 'Lowest to highest'))  # reverse order or not
    criteria=st.radio(
     "Rank the states by: ",
        ('Series completed percentage', 'COVID case rate')
    )

with col6:
    placeholder_vis7=st.empty()

# Determine the rank order
reverse_order='descending'
if (high_low=='Lowest to highest'):
    reverse_order='ascending'

# combine the data into 1
df1_date=df1[df1.date==datestr]
df1_date.sample(10)
dff=df3_date.merge(df1_date,left_on='Location',right_on='location')

# Determine the sort field
sortfield="Series_Complete_Pop_Pct"
if (criteria=="COVID case rate"):
    sortfield="covid_rate"

# Base of first graph
vaccine_base=alt.Chart(dff).transform_window(
    rank='rank()',
    sort=[alt.SortField(sortfield, order=reverse_order)]
).encode(
    x=alt.X('state:N',sort=alt.SortField(field=sortfield, order=reverse_order)),
).transform_filter(
    (alt.datum.rank <= show_number)
)

######## bar+point 1 ########
vaccine_vis1=vaccine_base.mark_bar().encode(
    y=alt.Y('Series_Complete_Pop_Pct:Q',title="Percentage of completed series"),
    tooltip=[alt.Tooltip('Series_Complete_Pop_Pct',format=".2f",title="Completed series %")],
    color=alt.Color('Series_Complete_Pop_Pct:Q',title="Series percentage",scale=alt.Scale(scheme='greenblue'))
)
case_vis1=vaccine_base.mark_point(filled=True, color='red',size=100).encode(
    y=alt.Y('covid_rate:Q',title="COVID case rate"),
    tooltip=[alt.Tooltip('covid_rate',format=".2f",title="Covid case rate")],
    #size=alt.Size('covid_rate:Q')
)

vis71=alt.layer(vaccine_vis1,case_vis1).resolve_scale(
    y='independent',
    x='shared'
).properties(
    title="Completed vaccination series and COVID case rate"
).configure_title(
    fontSize=14,
    baseline='middle',
    dy=-5,
    anchor='middle',
    align="center",
    color='black'
)

######## bar+point 2 ########
case_vis2=vaccine_base.mark_bar().encode(
    y=alt.Y('covid_rate:Q',title="COVID case rate"),
    tooltip=[alt.Tooltip('covid_rate',format=".2f",title="Covid case rate")],
    color=alt.Color('covid_rate:Q',title="Case rate",scale=alt.Scale(scheme='orangered'))
)

vaccine_vis2=vaccine_base.mark_point(filled=True,color='blue').encode(
    y=alt.Y('Series_Complete_Pop_Pct:Q',title="Percentage of completed series"),
    tooltip=[alt.Tooltip('Series_Complete_Pop_Pct',format=".2f",title="Completed series %")],
    #size=alt.Size('Series_Complete_Pop_Pct:Q')
)

vis72=alt.layer(case_vis2,vaccine_vis2).resolve_scale(
    y='independent',
    x='shared'
).properties(
    title="Completed vaccination series and COVID case rate"
).configure_title(
    fontSize=14,
    baseline='middle',
    dy=-5,
    anchor='middle',
    align="center",
    color='black'
)

######
if (criteria=="COVID case rate"):
    placeholder_vis7.altair_chart(vis72)
else:
    placeholder_vis7.altair_chart(vis71)

######## The detailed view of the selected states  #######

# The base dataframe

visbase7=alt.Chart(dff).transform_window(
    rank='rank()',
    sort=[alt.SortField(sortfield, order=reverse_order)]
).transform_fold(
    ['Series_Complete_5PlusPop_Pct','Series_Complete_12PlusPop_Pct','Series_Complete_18PlusPop_Pct',
     'Series_Complete_65PlusPop_Pct'],
    as_=["complete_pct","pct"]
).transform_calculate(
    pfizer_pct='datum.Series_Complete_Pfizer/datum.population',
    moderna_pct='datum.Series_Complete_Moderna/datum.population',
    janssen_pct='datum.Series_Complete_Janssen/datum.population'
).transform_fold(
    ['pfizer_pct','moderna_pct','janssen_pct'],
    as_=["vaccine_types",'vac_num']
).transform_filter(
    (alt.datum.rank <= show_number)
)

select_type=alt.selection_multi(
    fields=['vaccine_types'],
    bind='legend'
)

vaccine_typevis=visbase7.mark_bar().transform_filter(
    datum.Location!='US'
).encode(
    x=alt.X('vaccine_types:N',axis=None),
    y=alt.Y('vac_num:Q'),
    tooltip=[alt.Tooltip('vac_num:Q',format=".4f",title="Percentage")],
    color=alt.Color('vaccine_types:N',
                    scale=alt.Scale(scheme='redpurple'),
                    title="Vaccine types"),
    column=alt.Column('state:N',title=None),
    opacity=alt.condition(select_type,alt.value(1),alt.value(0.05))
).add_selection(
    select_type
).properties(
    title="Completed series percentage by vaccine type"
).configure_title(
    fontSize=16,
    baseline='middle',
    dy=-10,
    anchor='middle',
    align="center",
    color='black'
)

select_age=alt.selection_multi(
    fields=['complete_pct'],
    bind='legend'
)

age_groupvis=visbase7.mark_bar().transform_filter(
    datum.Location!='US' & datum.Series_Complete_Pop_Pct!=0 
).encode(
    x=alt.X('complete_pct:N',axis=None,title=""),
    y=alt.Y('pct:Q'),
    color=alt.Color('complete_pct:N',
                    scale=alt.Scale(scheme='bluepurple'),
                    title="Age groups"),
    tooltip=[alt.Tooltip('pct:Q',format=".4f",title="Percentage")],
    column=alt.Column('state:N',title=None),
    opacity=alt.condition(select_age,alt.value(1),alt.value(0.05))
).add_selection(
    select_age
).properties(
    title="Completed series percentage by age group"
).configure_title(
    fontSize=16,
    baseline='middle',
    dy=-10,
    anchor='middle',
    align="center",
    color='black'
)

with col7:
    placeholder_vis8=st.empty()
    
if (genre == "Vaccine type"):
    placeholder_vis8.altair_chart(vaccine_typevis)
elif (genre == "Age group"):
    placeholder_vis8.altair_chart(age_groupvis)