import streamlit as st
import pandas as pd
import altair as alt

# -------------------- Chargement des données --------------------


@st.cache_data
def load_data():
    df = pd.read_csv("dpt2020.csv", sep=";")
    df = df[df["preusuel"] != "_PRENOMS_RARES"]
    df = df[df["annais"] != "XXXX"]
    df["annais"] = df["annais"].astype(int)
    return df


df = load_data()

# -------------------- Interface Streamlit --------------------
st.title("Évolution des prénoms modernes vs traditionnels")

# Choix des départements
dpts = st.multiselect(
    "Départements à comparer (codes INSEE)",
    sorted(df['dpt'].unique()),
    default=["75", "85"]
)

# Choix des prénoms traditionnels
prenoms_trad = st.multiselect(
    "Prénoms traditionnels",
    sorted(df['preusuel'].unique()),
    default=[
        'JEAN', 'PIERRE', 'MICHEL', 'CLAUDE', 'PAUL', 'MARIE',
        'CATHERINE', 'FRANÇOIS', 'GÉRARD'
    ]
)

# Choix des prénoms modernes
prenoms_modern = st.multiselect(
    "Prénoms modernes",
    sorted(df['preusuel'].unique()),
    default=[
        'EMMA', 'LÉO', 'LOUISE', 'MILA', 'NOAH', 'MAËL'
    ]
)

# -------------------- Préparation des données --------------------
df = df[df['dpt'].isin(dpts)].copy()
df['type'] = 'AUTRE'
df.loc[df['preusuel'].isin(prenoms_trad), 'type'] = 'TRADITIONNEL'
df.loc[df['preusuel'].isin(prenoms_modern), 'type'] = 'MODERNE'

# -------------------- Graphe 1 : Proportion relative parmi prénoms sélectionnés --------------------
df1 = df[df['type'].isin(['TRADITIONNEL', 'MODERNE'])]

totals1 = df1.groupby(['annais', 'dpt'])[
    'nombre'].sum().reset_index(name='total')
type_sums1 = df1.groupby(['annais', 'dpt', 'type'])[
    'nombre'].sum().reset_index(name='count')
merged1 = pd.merge(type_sums1, totals1, on=['annais', 'dpt'])
merged1['ratio'] = merged1['count'] / merged1['total']

color_scale = alt.Scale(scheme='dark2')

chart1 = alt.Chart(merged1).mark_line(point=True).encode(
    x=alt.X('annais:Q', title='Année'),
    y=alt.Y('ratio:Q', title='Part des prénoms sélectionnés',
            axis=alt.Axis(format='%')),
    color=alt.Color('dpt:N', title='Département', scale=color_scale),
    opacity=alt.Opacity('type:N', title='Type', scale=alt.Scale(
        domain=['TRADITIONNEL', 'MODERNE'], range=[1.0, 0.5])),
    strokeDash=alt.StrokeDash('type:N', title='Type', scale=alt.Scale(
        domain=['TRADITIONNEL', 'MODERNE'], range=[[1, 0], [5, 5]])),
    tooltip=[
        alt.Tooltip('annais:Q', title='Année'),
        alt.Tooltip('dpt:N', title='Département'),
        alt.Tooltip('type:N', title='Type'),
        alt.Tooltip('ratio:Q', title='Proportion', format='.1%'),
        alt.Tooltip('count:Q', title='Nombre'),
        alt.Tooltip('total:Q', title='Total (sélection)')
    ]
).properties(
    width=800,
    height=400,
    title="1. Part relative des prénoms sélectionnés (moderne vs traditionnel)"
)

st.altair_chart(chart1, use_container_width=True)

# -------------------- Graphe 2 : Proportion par rapport au total des naissances --------------------
df2 = df[df['type'].isin(['TRADITIONNEL', 'MODERNE'])]

# Total absolu : toutes les naissances du département et année (pas seulement sélectionnées)
total_all = df.groupby(['annais', 'dpt'])[
    'nombre'].sum().reset_index(name='total_all')
type_sums2 = df2.groupby(['annais', 'dpt', 'type'])[
    'nombre'].sum().reset_index(name='count')
merged2 = pd.merge(type_sums2, total_all, on=['annais', 'dpt'])
merged2['ratio'] = merged2['count'] / merged2['total_all']

chart2 = alt.Chart(merged2).mark_line(point=True).encode(
    x=alt.X('annais:Q', title='Année'),
    y=alt.Y('ratio:Q', title='Part des naissances (absolue)',
            axis=alt.Axis(format='%')),
    color=alt.Color('dpt:N', title='Département', scale=color_scale),
    opacity=alt.Opacity('type:N', title='Type', scale=alt.Scale(
        domain=['TRADITIONNEL', 'MODERNE'], range=[1.0, 0.5])),
    strokeDash=alt.StrokeDash('type:N', title='Type', scale=alt.Scale(
        domain=['TRADITIONNEL', 'MODERNE'], range=[[1, 0], [5, 5]])),
    tooltip=[
        alt.Tooltip('annais:Q', title='Année'),
        alt.Tooltip('dpt:N', title='Département'),
        alt.Tooltip('type:N', title='Type'),
        alt.Tooltip('ratio:Q', title='Proportion', format='.1%'),
        alt.Tooltip('count:Q', title='Nombre'),
        alt.Tooltip('total_all:Q', title='Total (département)')
    ]
).properties(
    width=800,
    height=400,
    title="2. Part réelle des prénoms sélectionnés dans la population totale"
)

st.altair_chart(chart2, use_container_width=True)
