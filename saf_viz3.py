import pandas as pd
import plotly.express as px

df = pd.read_csv("/Users/user/Desktop/crawling/dpt2020.csv", delimiter=";")

# Load and clean
df = df[df['preusuel'] != '_PRENOMS_RARES']

# Compute total counts by name & sex
counts = (
    df
    .groupby(['preusuel','sexe'])['nombre']
    .sum()
    .unstack(fill_value=0)
    .rename(columns={1:'M', 2:'F'})  # adjust if your codes differ
)

# Compute proportions
counts['total']    = counts['M'] + counts['F']
counts['p_male']   = counts['M'] / counts['total']
counts['p_female'] = counts['F'] / counts['total']

# Keep only names where each sex ≥ 20%
balanced = counts[
    (counts['p_male']   >= 0.20) &
    (counts['p_female'] >= 0.20)
].index

df_balanced = df[df['preusuel'].isin(balanced)]

# Pick top 10 by total use
top_unisex = (
    df_balanced
    .groupby('preusuel')['nombre']
    .sum()
    .nlargest(5)
    .index
    .tolist()
)

df_top = df_balanced[df_balanced['preusuel'].isin(top_unisex)]

# Map sex codes to labels
df_top = df_top.copy()
df_top['Sex'] = df_top['sexe'].map({1:'Male', 2:'Female'})

# Plot
fig = px.line(
    df_top,
    x="annais", y="nombre", color="Sex",
    facet_col="preusuel", facet_col_wrap=5,
    title="Popularity of Truly Unisex Names Over Time",
    labels={"annais":"Year","nombre":"# of births"}
)
fig.update_layout(legend_title="Sex", hovermode="x unified")
fig.show()


filtered = df[df['preusuel'].isin(['CHARLIE', 'MARIE', 'CAMILLE', 'YAEL', 'JANICK',  'LOUISON', 'JANY', 'DOMINIQUE', 'SASHA', 'MAE', 'GABY'])]  # use your list
filtered['annais'] = pd.to_numeric(filtered['annais'], errors='coerce')
filtered = filtered.dropna(subset=['annais'])
filtered['annais'] = filtered['annais'].astype(int)

grouped = filtered.groupby(['preusuel', 'sexe', 'annais'], as_index=False)['nombre'].sum()

grouped['nombre_signed'] = grouped.apply(
    lambda row: -row['nombre'] if row['sexe'] == 2 else row['nombre'], axis=1
)

grouped['sexe'] = grouped['sexe'].astype(str)

chart = alt.Chart(grouped).mark_bar().encode(
    y=alt.Y('annais:O', title='Year', sort='descending'),
    x=alt.X('nombre_signed:Q', title='Number of births', axis=alt.Axis(format='~s')),
    color=alt.Color('sexe:N',
                    scale=alt.Scale(domain=['1', '2'], range=['steelblue', 'pink']),
                    title='Sex',
                    legend=alt.Legend(labelExpr="datum.value == '1' ? 'Boys' : 'Girls'")),
    tooltip=['preusuel:N', 'annais:O', 'sexe:N', 'nombre:Q']
).properties(
    width=700,
    height=1000
).facet(
    row=alt.Row('preusuel:N', title=None)
).resolve_scale(
    x='independent'
)

chart.show()
