# dashboard.py
import dash
from dash.dependencies import Input, Output
from dash import html, dcc, dash_table
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine, text
import dash_leaflet as dl
from geopy.geocoders import Nominatim
import plotly.express as px
import time
import os
# URL de connexion à Supabase
DATABASE_URL = "postgresql://postgres.lpdyhnlgdpnheclcpzzg:B5BEKdICOZVYMp2m@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"

try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("Connexion réussie à la base de données !")
    connection.close()
except Exception as e:
    print(f"Erreur de connexion : {e}")

# Fonction pour récupérer les KPIs
def get_kpis():
    with engine.connect() as connection:
        total_annonces = connection.execute(text("SELECT COUNT(*) FROM annonces;")).scalar()
        prix_moyen = connection.execute(text("SELECT AVG(prix) FROM annonces;")).scalar()
        prix_moyen = round(prix_moyen, 2) if prix_moyen else 0
        loc_freq_query = """
            SELECT localisation, COUNT(*) as count 
            FROM annonces 
            GROUP BY localisation 
            ORDER BY count DESC 
            LIMIT 1;
        """
        loc_freq = connection.execute(text(loc_freq_query)).fetchone()
        localisation_freq = loc_freq[0] if loc_freq else "N/A"
        date_recente = connection.execute(text("SELECT MAX(date_publication) FROM annonces;")).scalar()
        date_recente = date_recente.strftime("%d/%m/%Y") if date_recente else "N/A"
        nb_types = connection.execute(text("SELECT COUNT(DISTINCT type) FROM annonces;")).scalar()
        
        return {
            "total_annonces": total_annonces,
            "prix_moyen": prix_moyen,
            "localisation_freq": localisation_freq,
            "date_recente": date_recente,
            "nb_types": nb_types if nb_types else 0
        }

# Fonction pour récupérer les données de distribution
def get_distribution_data():
    with engine.connect() as connection:
        type_query = """
            SELECT type, COUNT(*) as count 
            FROM annonces 
            GROUP BY type;
        """
        type_data = pd.read_sql(type_query, connection)
        
        loc_query = """
            SELECT localisation, COUNT(*) as count 
            FROM annonces 
            GROUP BY localisation;
        """
        loc_data = pd.read_sql(loc_query, connection)
        
        prix_loc_query = """
            SELECT localisation, AVG(prix) as avg_prix 
            FROM annonces 
            GROUP BY localisation;
        """
        prix_loc_data = pd.read_sql(prix_loc_query, connection)
        
        annonces_query = """
            SELECT titre, prix, type, localisation, date_publication, lien 
            FROM annonces;
        """
        annonces_data = pd.read_sql(annonces_query, connection)

        prix_min_max_query = """
            SELECT DISTINCT localisation, MAX(prix) as max_prix, MIN(prix) as min_prix
            FROM annonces 
            GROUP BY localisation;
        """
        prix_min_max_data = pd.read_sql(prix_min_max_query, connection)

        return type_data, loc_data, prix_loc_data, annonces_data, prix_min_max_data


# Chargement ou création du cache
cache_file = "geocache.csv"
if os.path.exists(cache_file):
    cache_df = pd.read_csv(cache_file)
else:
    cache_df = pd.DataFrame(columns=["localisation", "lat", "lon"])

# Lire les localisations des annonces
with engine.connect() as conn:
    df = pd.read_sql("SELECT DISTINCT localisation ,titre FROM annonces", conn)

# Initialiser le géocodeur
#C’est un service de géocodage gratuit fourni par OpenStreetMap. 
# Il permet de convertir des adresses (ou noms de lieux) 
# en coordonnées GPS (latitude et longitude)
geolocator = Nominatim(user_agent="dash_leaflet_app", timeout=5)
locations = []

# Fonction d'ajout au cache
def ajouter_au_cache(loc_name, lat, lon):
    global cache_df
    nouveau = pd.DataFrame([{
        "localisation": loc_name,
        "lat": lat,
        "lon": lon
    }])
    cache_df = pd.concat([cache_df, nouveau], ignore_index=True)
    cache_df.to_csv(cache_file, index=False)

# Géocoder les localisations
for index, row in df.iterrows():
    loc_name = row["localisation"]

    if not isinstance(loc_name, str) or not loc_name.strip():
        continue  # Ignorer les valeurs vides

    # Vérifier si déjà dans le cache
    if loc_name in cache_df["localisation"].values:
        cached = cache_df[cache_df["localisation"] == loc_name].iloc[0]
        lat, lon = cached["lat"], cached["lon"]
        locations.append({
            "titre": row["titre"],
            "localisation": loc_name,
            "lat": lat,
            "lon": lon
        })
    else:
        try:
            loc = geolocator.geocode(loc_name)
            if loc:
                lat, lon = loc.latitude, loc.longitude
                print(f"[✔] {loc_name} -> ({lat}, {lon})")

                locations.append({
                    "titre": row["titre"],
                    "localisation": loc_name,
                    "lat": lat,
                    "lon": lon
                })

                ajouter_au_cache(loc_name, lat, lon)

            else:
                print(f"[✘] Localisation introuvable : {loc_name}")

            time.sleep(1)  # Limite pour ne pas surcharger Nominatim

        except Exception as e:
            print(f"Erreur de géocodage pour {loc_name} : {e}")

print(f"\n➡️ {len(cache_df)} localisations dans le cache.")
print(f"➡️ {len(locations)} localisations utilisées pour les marqueurs.\n")

# Créer des marqueurs Leaflet
markers = [
    dl.Marker(
        position=(loc["lat"], loc["lon"]),
        children=dl.Popup([html.B(loc["titre"]), html.Br(), loc["localisation"]])
    )
    for loc in locations
]

# Récupérer les données
kpis = get_kpis()
type_data, loc_data, prix_loc_data, annonces_data, prix_min_max_data = get_distribution_data()

# Convertir date_publication en format datetime pour le filtrage
annonces_data['date_publication'] = pd.to_datetime(annonces_data['date_publication'])

# Remove duplicates and sort for top 5 most expensive and least expensive
annonces_data_unique = annonces_data.drop_duplicates(subset=["titre", "prix", "localisation"])
top_5_expensive = annonces_data_unique.nlargest(5, "prix")
top_5_cheapest = annonces_data_unique.nsmallest(5, "prix")

# Combine titre and localisation for the y-axis labels
top_5_expensive["combined_title"] = top_5_expensive["titre"] + " - " + top_5_expensive["localisation"]
top_5_cheapest["combined_title"] = top_5_cheapest["titre"] + " - " + top_5_cheapest["localisation"]

# Create horizontal bar chart for top 5 most expensive
fig_expensive = go.Figure(
    data=[
        go.Bar(
            y=top_5_expensive["combined_title"],
            x=top_5_expensive["prix"],
            orientation="h",
            text=[f"{price:,.0f} TND" for price in top_5_expensive["prix"]],
            textposition="auto",
            textfont=dict(size=14, color="black"),
            marker=dict(color="#ff6b6b"),
        )
    ],
    layout=go.Layout(
        title="Top 5 des annonces les plus chères",
        xaxis=dict(title="Prix (TND)", tickformat=",.0f"),
        yaxis=dict(title="Titre", automargin=True),
        margin=dict(l=200, r=50, t=50, b=50),
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
)

# Create horizontal bar chart for top 5 least expensive
fig_cheapest = go.Figure(
    data=[
        go.Bar(
            y=top_5_cheapest["combined_title"],
            x=top_5_cheapest["prix"],
            orientation="h",
            text=[f"{price:,.0f} TND" for price in top_5_cheapest["prix"]],
            textposition="auto",
            textfont=dict(size=15, color="black"),
            marker=dict(color="#ccccff"),
        )
    ],
    layout=go.Layout(
        title="Top 5 des annonces les plus basses",
        xaxis=dict(title="Prix (TND)", tickformat=",.0f"),
        yaxis=dict(title="Titre", automargin=True),
        margin=dict(l=200, r=50, t=50, b=50),
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
)

# Créer les graphiques avec Plotly
fig_types = px.pie(type_data, names='type', values='count', hole=0.5)
fig_types.update_traces(textinfo='percent+label', textposition='outside')

fig_locations = px.pie(loc_data, names='localisation', values='count')
fig_locations.update_traces(textinfo='percent+label', textposition='inside')

fig_prix_loc = px.bar(
    prix_loc_data,
    x='localisation',
    y='avg_prix',
    title="Répartition des prix par localisation",
    labels={'avg_prix': 'Prix moyen (TND)', 'localisation': 'Localisation'}
)
fig_prix_loc.update_layout(
    xaxis_title="Localisation",
    yaxis_title="Prix moyen (TND)",
    xaxis_tickangle=-45,
    yaxis_tickformat=",.0f"
)

# Convertir la colonne 'date_publication' en datetime si ce n'est pas déjà fait
annonces_data['date_publication'] = pd.to_datetime(annonces_data['date_publication'])

# Regrouper par mois (ou par semaine si vous préférez)
# Pour un regroupement par mois :
annonces_par_mois = annonces_data.groupby(annonces_data['date_publication'].dt.to_period('M')).size().reset_index(name='nombre_annonces')
annonces_par_mois['date_publication'] = annonces_par_mois['date_publication'].dt.to_timestamp()

# Créer le graphique avec Plotly
fig_evolution_temporelle = px.line(
    annonces_par_mois,
    x='date_publication',
    y='nombre_annonces',
    title="Évolution du nombre d'annonces dans le temps",
    labels={'date_publication': 'Date de publication', 'nombre_annonces': 'Nombre d’annonces'},
    template='plotly_white'
)

# Personnaliser le graphique
fig_evolution_temporelle.update_layout(
    xaxis_title="Date (par mois)",
    yaxis_title="Nombre d'annonces",
    font=dict(size=14),
    title_x=0.5,  # Centrer le titre
    plot_bgcolor='#f9f9f9',
    paper_bgcolor='#f9f9f9',
    margin=dict(l=40, r=40, t=60, b=40)
)

fig_evolution_temporelle.update_traces(
    line_color='#6b64f3',  # Couleur de la courbe correspondant à votre thème
    line_width=2
)

# Initialisation de l'application Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    ],
    suppress_callback_exceptions=True  # Allow callbacks for components that might not exist initially
)

# Création de la carte centrée sur la Tunisie
tunisia_center = [34.0, 9.0]
tunisia_zoom = 6

# Création des marqueurs
markers = [
    dl.Marker(
        position=(loc["lat"], loc["lon"]),
        children=dl.Popup(f"{loc['titre']} - {loc['localisation']}")
    ) for loc in locations
]
# Styles
kpi_style = {
    "border": "2px solid #6b64f3",
    "border-radius":"6px",
    "padding": "10px",
    "margin": "10px",
    "text-align": "center",
    "width": "18%",
    "display": "inline-block",
    "background-color": "#f9f9f9",
    "box-shadow": "1px 5px 60px 0px #100a886b"
}

date_recente_style = {
    "position": "absolute",
    "left": "80%",
    "top": "10%",
    "width": "15%",
    "height": "40px",
    "text-align": "center",
    "font-family": "Arial, sans-serif",
    "background-color": "#6366f1",
    "color": "white",
    "border-radius": "6px",
    "overflow": "hidden",
    "transition": "all 0.5s ease-in-out",
    "display": "flex",
    "flex-direction": "column",
    "justify-content": "center",
    "padding": "5px",
}

container_style = {
    "display": "flex",
    "justify-content": "space-between",
    "width": "90%",
    "margin": "20px 0"
}

filters_container_style = {
    "display": "flex",
    "justify-content": "space-between",
    "width": "80%",
    "margin": "20px 0"
}

filter_column_style = {
    "width": "60%",
    "display": "flex",
    "flex-direction": "column",
    "gap": "10px"
}

column_style = {
    "width": "60%",
    "text-align": "center"
}

table_style = {
    "margin": "20px auto",
    "width": "80%",
    "borderCollapse": "collapse",
    "fontFamily": "Arial, sans-serif",
    "margin-left":"9px"
}

table_header_style = {
    "backgroundColor": "#6366f1",
    "color": "white",
    "textAlign": "center",
    "fontWeight": "bold",
    "fontSize": "18px"
}

table_cell_style = {
    "border": "2px solid #ddd",
    "padding": "12px",
    "textAlign": "center"
}


# Styles pour la carte Uiverse.io d'alexmaracinaru
card_style = {
    "width": "130px",
    "height": "230px",
    "background": "#3405a3",
    "borderRadius": "15px",
    "boxShadow": "1px 5px 60px 0px #100a886b",
    "margin": "0px",
    "display": "inline-block",  # Pour s'aligner avec les autres KPIs
    "position":"absolute",
    "left":"87%",
    "top":"18.2%"
  
}

card_border_top_style = {
    "width": "50%",
    "height": "3%",
    "background": "#6b64f3",
    "margin": "auto",
    "borderRadius": "0px 0px 15px 15px",
    
}

img_style = {
    "width": "50px",
    "height": "60px",
    "background": "#6b64f3",
    "borderRadius": "15px",
    "margin": "auto",
    "marginTop": "25px",
}

span_style = {
    "fontWeight": "600",
    "color": "white",
    "textAlign": "center",
    "display": "block",
    "paddingTop": "10px",
    "fontSize": "16px",
}

job_style = {
    "fontWeight": "400",
    "color": "white",
    "display": "block",
    "textAlign": "center",
    "paddingTop": "3px",
    "fontSize": "12px",
}

button_style = {
    "padding": "8px 25px",
    "display": "block",
    "margin": "auto",
    "borderRadius": "8px",
    "border": "none",
    "marginTop": "30px",
    "background": "#6b64f3",
    "color": "white",
    "fontWeight": "600",
    "cursor": "pointer",
}

button_hover_style = {
    "background": "#534bf3",
}


# Options pour les filtres
type_options = [{'label': t, 'value': t} for t in annonces_data['type'].unique()]
localisation_options = [{'label': loc, 'value': loc} for loc in annonces_data['localisation'].unique()]

# Define Page 1 Layout (Main Dashboard)
page_1_layout = html.Div([
    html.H1("Tableau de bord des annonces immobilières",className="dashboard-title"),
    html.H2("KPIs"),
    html.Div([
        html.Div([
            html.I(className="fas fa-calendar-alt", style={"margin-right": "10px", "font-size": "16px"}),
            html.H4("Date Récente", style={"margin": "0", "font-size": "16px", "display": "inline-block"})
        ], style={"display": "flex", "align-items": "center"}),
        html.P(f"{kpis['date_recente']}", style={"margin": "0", "font-size": "15px"})
    ], style=date_recente_style),
    
    html.Div([
        html.Div([
            html.H3("Total Annonces"),
            html.P(f"{kpis['total_annonces']}")
        ], style=kpi_style),
        html.Div([
            html.H3("Prix Moyen (TND)"),
            html.P(f"{kpis['prix_moyen']}")
        ], style=kpi_style),
        html.Div([
            html.H3("Localisation Fréquente"),
            html.P(f"{kpis['localisation_freq']}")
        ], style=kpi_style),
        html.Div([
            html.H3("Nb Types Immobilier"),
            html.P(f"{kpis['nb_types']}")
        ], style=kpi_style),
    ]),
    html.Div([
        html.Div(style=card_border_top_style),  # Bordure supérieure
        html.Div(style=img_style),  # Placeholder pour l'image (peut être remplacé par une icône si besoin)
        html.Span(f"Toutes Annonces:", style=span_style),  # Afficher le nombre total d'annonces
        html.P("Voir détails", className="job", style=job_style),  # Description
        dcc.Link(
            html.Button("Click", style=button_style),  # Bouton cliquable
            href="/page-2"  # Redirige vers la deuxième page
        )
    ], style=card_style),

    html.H2("Prix Min/Max par Localisation"),
    dash_table.DataTable(
        columns=[
            {"name": "Localisation", "id": "localisation"},
            {"name": "Prix Max (TND)", "id": "max_prix"},
            {"name": "Prix Min (TND)", "id": "min_prix"}
        ],
        data=prix_min_max_data.to_dict("records"),
        style_table=table_style,
        style_header=table_header_style,
        style_cell=table_cell_style,
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"}
        ],
        page_size=8,
        page_action="native"
    ),
    html.H2("Analyse des Annonces"),
    html.Div([
        dcc.Graph(figure=fig_expensive, style={"width": "48%", "display": "inline-block", "margin": "1%"}),
        dcc.Graph(figure=fig_cheapest, style={"width": "48%", "display": "inline-block", "margin": "1%"})
    ]),
    html.Div([
        html.Div([
            html.H2("Distribution des types d'immobiliers"),
            dcc.Graph(figure=fig_types)
        ], style=column_style),
        html.Div([
            html.H2("Distribution des localisations"),
            dcc.Graph(figure=fig_locations)
        ], style=column_style)
    ], style=container_style),
    html.H2("Répartition des prix par localisation"),
    dcc.Graph(figure=fig_prix_loc, style={"width": "100%", "margin": "20px 0"}),
    
  html.Div([
    # Conteneur de gauche : Graphique
    html.Div([
        html.H2("Évolution temporelle des annonces"),
        dcc.Graph(
            figure=fig_evolution_temporelle,
            style={"width": "100%", "height": "70vh", "margin": "20px 0"}
        )
    ], style={"flex": "1", "padding": "10px"}),

    # Conteneur de droite : Carte
    html.Div([
        html.H2("Carte des Annonces immobilières en Tunisie 📍"),
        dl.Map(
            center=[34.0, 9.0],
            zoom=6,
            style={"width": "100%", "height": "70vh"},
            children=[
                dl.TileLayer(),
                dl.LayerGroup(markers)
            ]
        )
    ], style={"flex": "1", "padding": "10px"}),

], style={
    "display": "flex",
    "flexDirection": "row",
    "gap": "20px",        # Espace entre les colonnes
    "flexWrap": "wrap"    # Permet d'adapter en responsive
}),

    
   
    dcc.Link(
        html.Button("Go to Page 2", style={
            "margin": "20px auto",
            "display": "block",
            "padding": "10px 20px",
            "backgroundColor": "#6366f1",
            "color": "white",
            "border": "none",
            "borderRadius": "5px",
            "cursor": "pointer",
            "fontSize": "16px"
        }),
        href="/page-2"
    )
])

# Define Page 2 Layout
page_2_layout = html.Div([
    html.H1("Tableau interactif des annonces", style={"textAlign": "center"}),
    html.Div([
        html.Div([
            html.Div([
                html.Label("Filtrer par type :"),
                dcc.Dropdown(
                    id='type-filter',
                    options=[{'label': 'Tous', 'value': 'all'}] + type_options,
                    value='all',
                    style={'width': '100%', "backgroundColor": "#6b64f3", "color": "black"}
                ),
                html.Label("Filtrer par localisation :", style={'marginTop': '10px'}),
                dcc.Dropdown(
                    id='localisation-filter',
                    options=[{'label': 'Tous', 'value': 'all'}] + localisation_options,
                    value='all',
                    style={'width': '100%', "backgroundColor": "#6b64f3", "color": "black"}
                ),
            ], style=filter_column_style),
            html.Div([
                html.Label("Plage de prix (TND) :"),
                dcc.RangeSlider(
                    id='prix-range',
                    min=annonces_data['prix'].min(),
                    max=annonces_data['prix'].max(),
                    value=[annonces_data['prix'].min(), annonces_data['prix'].max()],
                    marks={int(annonces_data['prix'].min()): str(int(annonces_data['prix'].min())),
                           int(annonces_data['prix'].max()): str(int(annonces_data['prix'].max()))},
                    step=1000,
                    className="dash-slider"  # Ajout d'une classe pour cibler le RangeSlider dans le CSS
                ),
                html.Label("Plage de dates :", style={'marginTop': '5px'}),
                dcc.DatePickerRange(
                    id='date-range',
                    min_date_allowed=annonces_data['date_publication'].min(),
                    max_date_allowed=annonces_data['date_publication'].max(),
                    start_date=annonces_data['date_publication'].min(),
                    end_date=annonces_data['date_publication'].max(),
                    style={'fontSize': '14px','margin-left':'10px','margin-top':'10px'}  # Ajuster la taille de la police pour cohérence
                ),
            ], style=filter_column_style),
        ], style=filters_container_style),
        dash_table.DataTable(
            id='annonces-table',
            columns=[
                {'name': 'Titre', 'id': 'titre', 'type': 'text', 'presentation': 'markdown'},
                {'name': 'Prix (TND)', 'id': 'prix', 'type': 'numeric'},
                {'name': 'Type', 'id': 'type', 'type': 'text'},
                {'name': 'Localisation', 'id': 'localisation', 'type': 'text'},
                {'name': 'Date Publication', 'id': 'date_publication', 'type': 'datetime'}
            ],
            data=annonces_data.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '5px'},
            style_header={
                'backgroundColor': '#6b64f3',  # Couleur de l'en-tête (correspond au thème)
                'color': 'white',
                'fontWeight': 'bold',
                'fontSize': '18px',  # Augmenter la taille de la police
                'height': '50px',  # Augmenter la hauteur de l'en-tête
                'lineHeight': '50px'  # Centrer verticalement le texte
            },
            sort_action='native',
            page_size=6,
        )
    ]),
    dcc.Link(
        html.Button("Back to Dashboard", style={
            "margin": "20px auto",
            "display": "block",
            "padding": "10px 20px",
            "backgroundColor": "#6366f1",
            "color": "white",
            "border": "none",
            "borderRadius": "5px",
            "cursor": "pointer",
            "fontSize": "16px"
        }),
        href="/"
    )
], style={"backgroundColor": "#ccccff", "minHeight": "100vh", "padding": "20px"})  # Appliquer la couleur de fond à toute la page

# Define the app layout with routing
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Callback pour mettre à jour le tableau en fonction des filtres
@app.callback(
    Output('annonces-table', 'data'),
    [
        Input('type-filter', 'value'),
        Input('localisation-filter', 'value'),
        Input('prix-range', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_table(type_filter, localisation_filter, prix_range, start_date, end_date):
    filtered_data = annonces_data.copy()
    
    if type_filter != 'all':
        filtered_data = filtered_data[filtered_data['type'] == type_filter]
    
    if localisation_filter != 'all':
        filtered_data = filtered_data[filtered_data['localisation'] == localisation_filter]
    
    filtered_data = filtered_data[
        (filtered_data['prix'] >= prix_range[0]) & 
        (filtered_data['prix'] <= prix_range[1])
    ]
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered_data = filtered_data[
        (filtered_data['date_publication'] >= start_date) & 
        (filtered_data['date_publication'] <= end_date)
    ]
    
    filtered_data['titre'] = filtered_data.apply(
        lambda row: f"[{row['titre']}]({row['lien']})", axis=1
    )
    
    return filtered_data.to_dict('records')

# Callback to render the correct page based on the URL
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/page-2":
        return page_2_layout
    else:
        return page_1_layout

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)