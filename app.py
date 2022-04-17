import altair as alt
from altair import datum
from vega_datasets import data
import pandas as pd
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
col4, col5 = st.columns([1, 3.5])

d = st.date_input(
     "Filter data up to which date",
     value=datetime.date(2022, 4, 14),
     min_value=datetime.date(2020, 12, 14),
     max_value=datetime.date(2022, 4, 14))
st.caption('Note: Data on vaccination status by age group were incompletely recorded before 2021.5.14 and therefore are not included in analysis.')

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
    tooltip=[alt.Tooltip("state:N",title="State"), 
                alt.Tooltip("covid_rate:Q",format=".2%",title="COVID case rate"), 
                alt.Tooltip("avg_vaccine:Q",format=".4f",title="Average vaccine dose")]
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
    continuousHeight=273,
    continuousWidth=330
)

with col1:
    vis1


age = ['All', 'age<12', '12<=age<18', '18<=age<65', 'age>=65']
type = ['All', 'Janssen', 'Moderna', 'Pfizer', 'Unknown']

with col2:
    place_holder_vis2 = st.empty()
    move = st.slider('The number of week difference between COVID-19 case data and vaccination data: ', 0, 50, 0) # choose the number to filter  
    genre = st.radio(
        "Show the vaccination data by: ",
        ('Vaccine type', 'Age group'))

title_dict = {'Vaccine type': 'Vaccine type', 'Age group': 'Age group'}
filter_dict = {'Vaccine type': type, 'Age group': age}
title = title_dict[genre]
showby = filter_dict[genre]

movetitle = 'New COVID-19 case (solid)' if move == 0 else 'New COVID-19 case after ' + str(move) + ' weeks (solid)'
movetooltip = 'New COVID-19 cases' if move == 0 else 'New COVID-19 cases after ' + str(move) + ' weeks'

# visualization 2

df2 = pd.read_csv('data/df2.csv')
df2['date'] = pd.to_datetime(df2['date'])

tmp = df2.copy()
for i in range(len(df2)):
    if i < len(df2) - move:
        tmp.loc[i, 'new_case'] = df2.loc[move + i, 'new_case']
    else:
        tmp.loc[i, 'new_case'] = 0

vis2_selection1 = alt.selection_multi(fields=['vaccine_type'], bind='legend', empty="none")

vis2_selection2 = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['date'], empty='none')
vis2_selection3=alt.selection_interval(bind="scales", encodings=["x"]) 

vis2_base = alt.Chart(tmp).transform_filter(
    (datum.year < year) | (datum.year == year & datum.month < month) | (datum.year == year & datum.month == month & datum.day <= day)
).encode(
    x=alt.X('date:T', title='Date')
)  

vis2_line1 = vis2_base.mark_line(size=3).encode(
    y=alt.Y('new_case:Q', title=movetitle),
    color=alt.value("red")
)

vis2_line2 = vis2_base.mark_line(size=3).transform_fold(
    showby,
    as_=["vaccine_type","new_vaccine"]
).encode(
    y=alt.Y('new_vaccine:Q', title='New administered vaccine (dashed)'),
    strokeDash=alt.value([5,5]),
    color=alt.Color('vaccine_type:N', scale=alt.Scale(scheme='dark2'), title=title),
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
    y=alt.Y('new_case:Q', axis=None),
    opacity=alt.condition(vis2_selection2, alt.value(1), alt.value(0)),
    tooltip=[alt.Tooltip('date:T',title="Date of a week"), 
                alt.Tooltip('new_case:Q',format='s',title=movetooltip)],
    color=alt.value("red")
)

vis2_points2 = vis2_base.mark_point(size=80, filled=True).transform_fold(
    showby,
    as_=["vaccine_type","new_vaccine"]
).encode(
    y=alt.Y('new_vaccine:Q', axis=None),
    color=alt.Color('vaccine_type:N', scale=alt.Scale(scheme='dark2'), title=title),
    opacity=alt.condition(vis2_selection2 & vis2_selection1, alt.value(1), alt.value(0)),
    tooltip=[alt.Tooltip('date:T',title="Date of a week"), 
                alt.Tooltip('new_case:Q',format='s',title=movetooltip),
                alt.Tooltip('vaccine_type:N',title=title),
                alt.Tooltip('new_vaccine:Q',format='s',title='New vaccine doses'),]
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
    width=550, height=350, title='COVID-19 cases and vaccinations by week'
).configure_view(
    stroke=None
)

place_holder_vis2.altair_chart(vis2)

# visualization 3, 4, 5

df3 = pd.read_csv('data/df3.csv')
df3['date'] = pd.to_datetime(df3['date'])

tmp2 = df3[(df3['year'] == year) & (df3['month'] == month) & (df3['day'] == day)]
source1 = pd.DataFrame({"category": ["Infected", "Uninfected"], "rate": [tmp2['tot_case'].values[0] / tmp2['population'].values[0], 1 - tmp2['tot_case'].values[0] / tmp2['population'].values[0]], "value": [tmp2['tot_case'].values[0], tmp2['population'].values[0] - tmp2['tot_case'].values[0]]})
source2 = pd.DataFrame({"category": ["Vaccinated", "Unvaccinated"], "rate": [tmp2['Dose1_Complete'].values[0] / tmp2['population'].values[0], 1 - tmp2['Dose1_Complete'].values[0] / tmp2['population'].values[0]], "value": [tmp2['Dose1_Complete'].values[0], tmp2['population'].values[0] - tmp2['Dose1_Complete'].values[0]]})
source3 = pd.DataFrame({"category": ["Vaccinated", "Unvaccinated"], "rate": [tmp2['Series_Complete'].values[0] / tmp2['population'].values[0], 1 - tmp2['Series_Complete'].values[0] / tmp2['population'].values[0]], "value": [tmp2['Series_Complete'].values[0], tmp2['population'].values[0] - tmp2['Series_Complete'].values[0]]})

vis3 = alt.Chart(source1).mark_arc(innerRadius=10, outerRadius=60).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", sort=['Uninfected', 'Infected'], scale=alt.Scale(scheme='reds'), legend=alt.Legend(
        orient='bottom',
        direction='horizontal')),
    tooltip=[alt.Tooltip('category:N',title="Category"), 
                alt.Tooltip('value:Q',format='s',title="Number of people"), 
                alt.Tooltip('rate:Q',format=".2%",title="Proportion of people")],
).properties(
    width=180, height=215,
    title='Covid-19 infection proportion'
).configure_view(
    stroke=None
).configure_title(
    dy= -10
)

vis4 = alt.Chart(source2).mark_arc(innerRadius=10, outerRadius=60).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='blues'), legend=alt.Legend(
        orient='bottom',
        direction='horizontal')),
    tooltip=[alt.Tooltip('category:N',title="Category"), 
                alt.Tooltip('value:Q',format='s',title="Number of people"), 
                alt.Tooltip('rate:Q',format=".2%",title="Proportion of people")],
).properties(
    width=180, height=215,
    title='First dose vaccination rate'
).configure_view(
    stroke=None
).configure_title(
    dy= -10
)

vis5 = alt.Chart(source3).mark_arc(innerRadius=10, outerRadius=60).encode(
    theta=alt.Theta(field="value", type="quantitative"),
    color=alt.Color(field="category", type="nominal", scale=alt.Scale(scheme='greens'), legend=alt.Legend(
        orient='bottom',
        direction='horizontal')),
    tooltip=[alt.Tooltip('category:N',title="Category"), 
                alt.Tooltip('value:Q',format='s',title="Number of people"), 
                alt.Tooltip('rate:Q',format=".2%",title="Proportion of people")],
).properties(
    width=180, height=215,
    title='Complete vaccination rate'
).configure_view(
    stroke=None
).configure_title(
    dy= -10
)

with col3:
    vis3
    vis4
    vis5

##############################   The second row   ##############################


# Vaccination rate of all ages  #

df4 = pd.read_csv('data/df4.csv')
df4['date'] = pd.to_datetime(df4['date'])

with col4:
    criteria=st.radio(
        "Rank the states by: ",
        ('Completed series percentage', 'COVID case rate'))
    high_low=st.radio(
        "View the data from: ",
        ('Highest to lowest', 'Lowest to highest'))  # reverse order or not
    genre2 = st.radio(
        "Show the series data by: ",
        ('Vaccine type', 'Age group'))

with col5:
    place_holder_vis6 = st.empty()
    show_number = st.slider('The number of states shown in the graphs: ', 1, 20, 4) # choose the number to filter    

# Determine the rank order
reverse_order='descending'
if (high_low=='Lowest to highest'):
    reverse_order='ascending'

# Determine the sort field
sortfield="Series_Complete_Pop_Pct"
if (criteria=="COVID case rate"):
    sortfield="covid_rate"

tmp3 = df4[(df4['year'] == year) & (df4['month'] == month) & (df4['day'] == day)]

# Base of first graph
vaccine_base=alt.Chart(tmp3).transform_window(
    rank='rank()',
    sort=[alt.SortField(sortfield, order=reverse_order)]
).encode(
    y=alt.Y('state:N',sort=alt.SortField(field=sortfield, order=reverse_order),title=""),
).transform_filter(
    (alt.datum.rank <= show_number)
)

select_bar=alt.selection_multi()
colorcondition=alt.condition(select_bar,alt.value(1),alt.value(0.2))

######## bar+point 1 ########
vaccine_vis1=vaccine_base.mark_bar().encode(
    x=alt.X('Series_Complete_Pop_Pct:Q',title="Percentage of completed series (bar)"),
    tooltip=[alt.Tooltip("state:N",title="State"), 
                alt.Tooltip('covid_rate',format=".2%",title="Covid case rate"),
                alt.Tooltip('Series_Complete_Pop_Pct',format=".2%",title="Completed series %")],
    color=alt.Color('Series_Complete_Pop_Pct:Q',title="Series percentage",scale=alt.Scale(scheme='greenblue')),
    opacity=colorcondition
).properties(
    height=alt.Step(80)  # controls width of bar.
)

case_vis1=vaccine_base.mark_tick(thickness=3, color='red',size=80*0.9).encode(
    x=alt.X('covid_rate:Q',title="COVID case rate (red ticks)"),
    tooltip=[alt.Tooltip("state:N",title="State"), 
                alt.Tooltip('covid_rate',format=".2%",title="Covid case rate"),
                alt.Tooltip('Series_Complete_Pop_Pct',format=".2%",title="Completed series %")],
    #size=alt.Size('covid_rate:Q'),
    opacity=colorcondition
)

vis71=alt.layer(vaccine_vis1,case_vis1).resolve_scale(
    x='independent',
    y='shared'
).add_selection(
    select_bar
).properties(
    title="Completed vaccination series and COVID case rate",
    width=310
)

######## bar+point 2 ########
case_vis2=vaccine_base.mark_bar().encode(
    x=alt.X('covid_rate:Q',title="COVID case rate (bar)"),
    tooltip=[alt.Tooltip("state:N",title="State"), 
                alt.Tooltip('covid_rate',format=".2%",title="Covid case rate"),
                alt.Tooltip('Series_Complete_Pop_Pct',format=".2%",title="Completed series %")],
    color=alt.Color('covid_rate:Q',title="Case rate",scale=alt.Scale(scheme='orangered')),
    opacity=colorcondition
).properties(
    height=alt.Step(80)  # controls width of bar.
)

vaccine_vis2=vaccine_base.mark_tick(thickness=3, color='blue',size=80*0.9).encode(
    x=alt.X('Series_Complete_Pop_Pct:Q',title="Percentage of completed series (blue ticks)"),
    tooltip=[alt.Tooltip("state:N",title="State"), 
                alt.Tooltip('covid_rate',format=".2%",title="Covid case rate"),
                alt.Tooltip('Series_Complete_Pop_Pct',format=".2%",title="Completed series %")],
    #size=alt.Size('Series_Complete_Pop_Pct:Q'),
    opacity=colorcondition
)

vis72=alt.layer(case_vis2,vaccine_vis2).resolve_scale(
    x='independent',
    y='shared'
).add_selection(
    select_bar
).properties(
    title="Completed vaccination series and COVID case rate",
    width=310
)

######## The detailed view of the selected states  #######

# The base dataframe

visbase7=alt.Chart(tmp3).transform_window(
    rank='rank()',
    sort=[alt.SortField(sortfield, order=reverse_order)]
).transform_fold(
    ['age>=12', 'age>=18', 'age>=65',],
    as_=["complete_pct","pct"]
).transform_calculate(
    Pfizer='datum.Pfizer_num/datum.population',
    Moderna='datum.Moderna_num/datum.population',
    Janssen='datum.Janssen_num/datum.population'
).transform_fold(
    ['Pfizer','Moderna','Janssen'],
    as_=["vaccine_types",'vac_num']
).transform_filter(
    (alt.datum.rank <= show_number)
)

vaccine_typevis=visbase7.mark_bar().transform_filter(
    datum.location!='US'
).encode(
    y=alt.Y('vaccine_types:N',axis=None),
    x=alt.X('vac_num:Q', title="Percentage of completed series"),
    tooltip=[alt.Tooltip("state:N",title="State"),
                alt.Tooltip('vaccine_types:N',title="Vaccine type"),
                alt.Tooltip('vac_num:Q',format=".2%",title="Percentage")],
    color=alt.Color('vaccine_types:N',
                    scale=alt.Scale(scheme='redpurple'),
                    title="Vaccine type"),
    row=alt.Row('state:N',title=None,sort=alt.SortField(field=sortfield, order=reverse_order)),
    opacity=colorcondition
).add_selection(
    select_bar
).properties(
    title="Completed series percentage by vaccine type",
    width=310
)

age_groupvis=visbase7.mark_bar().transform_filter(
    datum.location!='US' & datum.Series_Complete_Pop_Pct!=0 
).encode(
    y=alt.Y('complete_pct:N',axis=None,title=""),
    x=alt.X('pct:Q', title="Percentage of completed series"),
    color=alt.Color('complete_pct:N',
                    scale=alt.Scale(scheme='bluepurple'),
                    title="Age group"),
    tooltip=[alt.Tooltip("state:N",title="State"),
                alt.Tooltip('complete_pct:N',title="Age group"),
                alt.Tooltip('pct:Q',format=".2%",title="Percentage")],
    row=alt.Row('state:N',title=None,sort=alt.SortField(field=sortfield, order=reverse_order)),
    opacity=colorcondition
).add_selection(
    select_bar
).properties(
    title="Completed series percentage by age group",
    width=310
)


if (genre2 == "Vaccine type" and criteria=="COVID case rate"):
    place_holder_vis6.altair_chart((vis72 | vaccine_typevis).configure_title(
            fontSize=14,
            baseline='middle',
            dy=-10,
            anchor='middle',
            align="center",
            color='black'
        ))
elif (genre2 == "Vaccine type" and criteria == "Completed series percentage"):
    place_holder_vis6.altair_chart((vis71 | vaccine_typevis).configure_title(
            fontSize=14,
            baseline='middle',
            dy=-10,
            anchor='middle',
            align="center",
            color='black',
        ))        
elif (genre2 == "Age group" and criteria == "COVID case rate"):
    place_holder_vis6.altair_chart((vis72 | age_groupvis).configure_title(
            fontSize=14,
            baseline='middle',
            dy=-10,
            anchor='middle',
            align="center",
            color='black'
        ))
elif (genre2 =="Age group" and criteria == "Completed series percentage"):
    place_holder_vis6.altair_chart((vis71 | age_groupvis).configure_title(
            fontSize=14,
            baseline='middle',
            dy=-10,
            anchor='middle',
            align="center",
            color='black'
        ))
