import pandas as pd
import altair as alt
import numpy as np

# Configuration d'Altair pour un meilleur rendu
alt.data_transformers.enable('json')


def clean_data(df):
    """Nettoie et prépare les données"""
    df_clean = df.copy()

    # Conversion des types
    df_clean['années'] = pd.to_numeric(df_clean['années'], errors='coerce')
    df_clean['nombre'] = pd.to_numeric(df_clean['nombre'], errors='coerce')

    # Suppression des valeurs nulles
    df_clean = df_clean.dropna(subset=['années', 'nombre'])

    # Nettoyage des noms de colonnes si nécessaire
    df_clean.columns = df_clean.columns.str.strip()

    return df_clean


# Supposons que votre DataFrame s'appelle 'df'
df = pd.read_csv('dpt2020.csv', sep=';')
df.columns = ['sexe', 'prénom', 'années', 'dpt', 'nombre']

# Fonctions de préparation des données


def prepare_temporal_data(df, top_n=15):
    """Prépare les données pour l'analyse temporelle"""
    # Convertir la colonne années en numérique
    df_copy = df.copy()
    df_copy['années'] = pd.to_numeric(df_copy['années'], errors='coerce')

    # Agrégation par prénom, année et sexe
    yearly_counts = df_copy.groupby(['prénom', 'années', 'sexe'])[
        'nombre'].sum().reset_index()

    # Top prénoms par sexe sur toute la période
    total_counts = df_copy.groupby(['prénom', 'sexe'])[
        'nombre'].sum().reset_index()
    top_prenoms_m = total_counts[total_counts['sexe'] == 'M'].nlargest(top_n, 'nombre')[
        'prénom'].tolist()
    top_prenoms_f = total_counts[total_counts['sexe'] == 'F'].nlargest(top_n, 'nombre')[
        'prénom'].tolist()

    # Filtrer pour les top prénoms
    top_prenoms = top_prenoms_m + top_prenoms_f
    filtered_data = yearly_counts[yearly_counts['prénom'].isin(top_prenoms)]

    return filtered_data


def prepare_regional_data(df, year_range=None):
    """Prépare les données pour l'analyse régionale"""
    if year_range:
        # Convertir la colonne années en numérique si elle ne l'est pas
        df_copy = df.copy()
        df_copy['années'] = pd.to_numeric(df_copy['années'], errors='coerce')
        df_filtered = df_copy[df_copy['années'].between(
            year_range[0], year_range[1])]
    else:
        df_filtered = df

    # Agrégation par département et prénom
    regional_counts = df_filtered.groupby(['dpt', 'prénom', 'sexe'])[
        'nombre'].sum().reset_index()

    # Calcul des pourcentages par département
    dept_totals = regional_counts.groupby('dpt')['nombre'].sum().reset_index()
    dept_totals.columns = ['dpt', 'total_dept']

    regional_data = regional_counts.merge(dept_totals, on='dpt')
    regional_data['pourcentage'] = (
        regional_data['nombre'] / regional_data['total_dept']) * 100

    return regional_data


def prepare_gender_data(df):
    """Prépare les données pour l'analyse des effets de genre"""
    # Convertir la colonne années en numérique
    df_copy = df.copy()
    df_copy['années'] = pd.to_numeric(df_copy['années'], errors='coerce')

    # Prénoms mixtes (donnés aux deux sexes)
    prenoms_mixtes = df_copy.groupby('prénom')['sexe'].nunique()
    prenoms_mixtes = prenoms_mixtes[prenoms_mixtes == 2].index.tolist()

    # Données pour prénoms mixtes
    mixed_data = df_copy[df_copy['prénom'].isin(prenoms_mixtes)]
    mixed_yearly = mixed_data.groupby(['prénom', 'années', 'sexe'])[
        'nombre'].sum().reset_index()

    return mixed_yearly

# ============================================================================
# VISUALISATION 1: ÉVOLUTION TEMPORELLE DES PRÉNOMS
# ============================================================================


def create_temporal_visualizations(df):
    """Crée les visualisations temporelles"""
    temporal_data = prepare_temporal_data(df, top_n=10)

    # Graphique 1: Évolution des top prénoms par sexe
    base_temporal = alt.Chart(temporal_data).add_params(
        alt.selection_point(fields=['prénom'])
    )

    temporal_chart = base_temporal.mark_line(point=True, strokeWidth=2).encode(
        x=alt.X('années:O', title='Année'),
        y=alt.Y('nombre:Q', title='Nombre de naissances'),
        color=alt.Color('prénom:N', title='Prénom'),
        strokeDash=alt.StrokeDash('sexe:N', title='Sexe'),
        tooltip=['prénom:N', 'années:O', 'sexe:N', 'nombre:Q']
    ).properties(
        width=800,
        height=400,
        title="Évolution des prénoms populaires dans le temps"
    ).facet(
        column=alt.Column('sexe:N', title='Sexe')
    )

    # Graphique 2: Heatmap de popularité
    # Convertir années en numérique pour la heatmap aussi
    df_copy = df.copy()
    df_copy['années'] = pd.to_numeric(df_copy['années'], errors='coerce')
    heatmap_data = df_copy.groupby(['années', 'prénom'])[
        'nombre'].sum().reset_index()
    top_20_prenoms = df_copy.groupby(
        'prénom')['nombre'].sum().nlargest(20).index.tolist()
    heatmap_filtered = heatmap_data[heatmap_data['prénom'].isin(
        top_20_prenoms)]

    heatmap = alt.Chart(heatmap_filtered).mark_rect().encode(
        x=alt.X('années:O', title='Année'),
        y=alt.Y('prénom:N', title='Prénom', sort='-x'),
        color=alt.Color('nombre:Q', scale=alt.Scale(
            scheme='viridis'), title='Naissances'),
        tooltip=['prénom:N', 'années:O', 'nombre:Q']
    ).properties(
        width=800,
        height=500,
        title="Heatmap de popularité des prénoms dans le temps (Top 20)"
    )

    return temporal_chart, heatmap

# ============================================================================
# VISUALISATION 2: ANALYSE RÉGIONALE
# ============================================================================


def create_regional_visualizations(df):
    """Crée les visualisations régionales"""
    regional_data = prepare_regional_data(
        df, year_range=(2010, 2020))  # Exemple sur 2010-2020

    # Sélection des prénoms populaires pour l'analyse
    top_prenoms_regional = df.groupby(
        'prénom')['nombre'].sum().nlargest(10).index.tolist()
    regional_filtered = regional_data[regional_data['prénom'].isin(
        top_prenoms_regional)]

    # Graphique 1: Carte de chaleur par département
    regional_heatmap = alt.Chart(regional_filtered).mark_rect().encode(
        x=alt.X('dpt:N', title='Département'),
        y=alt.Y('prénom:N', title='Prénom'),
        color=alt.Color('pourcentage:Q', scale=alt.Scale(
            scheme='blues'), title='% du département'),
        tooltip=['dpt:N', 'prénom:N', 'pourcentage:Q', 'nombre:Q']
    ).properties(
        width=1000,
        height=400,
        title="Distribution régionale des prénoms populaires (% par département)"
    )

    # Graphique 2: Variance régionale
    variance_data = regional_filtered.groupby('prénom').agg({
        'pourcentage': ['mean', 'std'],
        'nombre': 'sum'
    }).reset_index()
    variance_data.columns = ['prénom', 'mean_pct', 'std_pct', 'total']
    variance_data['cv'] = variance_data['std_pct'] / \
        variance_data['mean_pct']  # Coefficient de variation

    variance_chart = alt.Chart(variance_data).mark_circle(size=100).encode(
        x=alt.X('mean_pct:Q', title='Popularité moyenne (%)'),
        y=alt.Y('cv:Q', title='Coefficient de variation régionale'),
        size=alt.Size('total:Q', title='Total naissances'),
        color=alt.Color('prénom:N', title='Prénom'),
        tooltip=['prénom:N', 'mean_pct:Q', 'cv:Q', 'total:Q']
    ).properties(
        width=600,
        height=400,
        title="Variance régionale vs Popularité moyenne des prénoms"
    )

    return regional_heatmap, variance_chart

# ============================================================================
# VISUALISATION 3: ANALYSE DES EFFETS DE GENRE
# ============================================================================


def create_gender_visualizations(df):
    """Crée les visualisations des effets de genre"""
    gender_data = prepare_gender_data(df)

    # Sélection des prénoms mixtes avec suffisamment de données pour les deux sexes
    mixed_stats = gender_data.groupby(['prénom', 'sexe'])[
        'nombre'].sum().reset_index()
    mixed_pivot = mixed_stats.pivot(
        index='prénom', columns='sexe', values='nombre').fillna(0)

    # Filtrer les prénoms qui ont au moins 100 naissances pour chaque sexe
    mixed_pivot = mixed_pivot[(mixed_pivot.get('M', 0) >= 100) & (
        mixed_pivot.get('F', 0) >= 100)]
    valid_mixed_prenoms = mixed_pivot.index.tolist()[:15]  # Top 15

    gender_filtered = gender_data[gender_data['prénom'].isin(
        valid_mixed_prenoms)]

    if len(gender_filtered) == 0:
        print("Aucun prénom mixte trouvé avec suffisamment de données")
        # Créer des graphiques vides
        empty_data = pd.DataFrame(
            {'x': [0], 'y': [0], 'message': ['Pas de données']})
        empty_chart = alt.Chart(empty_data).mark_text(text='Pas de prénoms mixtes avec suffisamment de données').encode(
            x=alt.value(400), y=alt.value(200)
        ).properties(width=800, height=400)
        return empty_chart, empty_chart

    # Graphique 1: Évolution comparative par sexe
    gender_evolution = alt.Chart(gender_filtered).mark_line(point=True).encode(
        x=alt.X('années:O', title='Année'),
        y=alt.Y('nombre:Q', title='Nombre de naissances'),
        color=alt.Color('sexe:N', title='Sexe', scale=alt.Scale(
            domain=['F', 'M'], range=['#e74c3c', '#3498db'])),
        tooltip=['prénom:N', 'années:O', 'sexe:N', 'nombre:Q']
    ).properties(
        width=300,
        height=200
    ).facet(
        facet=alt.Facet('prénom:N', columns=5),
        title="Évolution des prénoms mixtes par sexe"
    ).resolve_scale(
        y='independent'
    )

    # Graphique 2: Ratio M/F dans le temps
    if len(gender_filtered) > 0:
        pivot_data = gender_filtered.pivot_table(
            index=['prénom', 'années'],
            columns='sexe',
            values='nombre',
            fill_value=0
        ).reset_index()

        # Vérifier et créer les colonnes manquantes
        if 'M' not in pivot_data.columns:
            pivot_data['M'] = 0
        if 'F' not in pivot_data.columns:
            pivot_data['F'] = 0

        # Filtrer pour ne garder que les prénoms qui ont des données pour les deux sexes
        pivot_data = pivot_data[(pivot_data['M'] > 0) | (pivot_data['F'] > 0)]
        pivot_data = pivot_data.groupby('prénom').filter(
            lambda x: (x['M'] > 0).any() and (x['F'] > 0).any())

        if len(pivot_data) > 0:
            pivot_data['ratio_mf'] = np.log10(
                (pivot_data['M'] + 1) / (pivot_data['F'] + 1))  # Log ratio
            pivot_data['total'] = pivot_data['M'] + pivot_data['F']

            ratio_chart = alt.Chart(pivot_data).mark_line(point=True).encode(
                x=alt.X('années:O', title='Année'),
                y=alt.Y('ratio_mf:Q', title='Log(Ratio M/F)',
                        scale=alt.Scale(domain=[-2, 2])),
                color=alt.Color('prénom:N', title='Prénom'),
                size=alt.Size('total:Q', title='Total naissances'),
                tooltip=['prénom:N', 'années:O', 'ratio_mf:Q', 'M:Q', 'F:Q']
            ).properties(
                width=800,
                height=400,
                title="Évolution du ratio Masculin/Féminin pour les prénoms mixtes"
            )
        else:
            # Graphique vide si pas de données
            ratio_chart = alt.Chart(pd.DataFrame({'x': [0], 'y': [0]})).mark_text(
                text='Pas de données suffisantes pour le ratio M/F'
            ).encode(x=alt.value(400), y=alt.value(200)).properties(width=800, height=400)
    else:
        ratio_chart = alt.Chart(pd.DataFrame({'x': [0], 'y': [0]})).mark_text(
            text='Pas de données pour les prénoms mixtes'
        ).encode(x=alt.value(400), y=alt.value(200)).properties(width=800, height=400)

    return gender_evolution, ratio_chart

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================


def analyze_prenoms(df):
    """Fonction principale d'analyse"""
    # Nettoyer les données d'abord
    print("Nettoyage des données...")
    df_clean = clean_data(df)

    print("Création des visualisations temporelles...")
    temporal_chart, heatmap = create_temporal_visualizations(df_clean)

    print("Création des visualisations régionales...")
    regional_heatmap, variance_chart = create_regional_visualizations(df_clean)

    print("Création des visualisations de genre...")
    gender_evolution, ratio_chart = create_gender_visualizations(df_clean)

    # Affichage des graphiques
    print("\n=== QUESTION 1: ÉVOLUTION TEMPORELLE ===")
    print("1. Évolution des prénoms populaires:")
    temporal_chart.show()

    print("2. Heatmap de popularité:")
    heatmap.show()

    print("\n=== QUESTION 2: EFFETS RÉGIONAUX ===")
    print("1. Distribution régionale:")
    regional_heatmap.show()

    print("2. Variance régionale vs popularité:")
    variance_chart.show()

    print("\n=== QUESTION 3: EFFETS DE GENRE ===")
    print("1. Évolution des prénoms mixtes par sexe:")
    gender_evolution.show()

    print("2. Ratio Masculin/Féminin dans le temps:")
    ratio_chart.show()

    return {
        'temporal': (temporal_chart, heatmap),
        'regional': (regional_heatmap, variance_chart),
        'gender': (gender_evolution, ratio_chart)
    }

# ============================================================================
# UTILISATION
# ============================================================================


# Chargez votre DataFrame et utilisez la fonction principale
visualizations = analyze_prenoms(df)

# Exemple de statistiques descriptives


def print_summary_stats(df):
    """Affiche quelques statistiques descriptives"""
    print("=== STATISTIQUES DESCRIPTIVES ===")
    print(f"Période couverte: {df['années'].min()} - {df['années'].max()}")
    print(f"Nombre total de prénoms uniques: {df['prénom'].nunique()}")
    print(f"Nombre de départements: {df['dpt'].nunique()}")
    print(f"Total des naissances: {df['nombre'].sum():,}")

    print("\nTop 10 prénoms masculins:")
    top_m = df[df['sexe'] == 'M'].groupby(
        'prénom')['nombre'].sum().nlargest(10)
    for nom, count in top_m.items():
        print(f"  {nom}: {count:,}")

    print("\nTop 10 prénoms féminins:")
    top_f = df[df['sexe'] == 'F'].groupby(
        'prénom')['nombre'].sum().nlargest(10)
    for nom, count in top_f.items():
        print(f"  {nom}: {count:,}")

# print_summary_stats(df)
