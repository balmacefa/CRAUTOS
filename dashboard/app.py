import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title="CRAutos Dashboard")
server = app.server

# Database Connection
# Try to get DATABASE_URL from environment, fallback to a default (mainly for local testing)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://crautos_user:crautos_pass@localhost:5432/crautos_db"
)

# Function to fetch data from PostgreSQL
def get_data():
    try:
        engine = create_engine(DATABASE_URL)
        query = "SELECT marca, modelo, año, precio_numerico, provincia, kilometraje_numerico, transmision, combustible, estilo FROM cars WHERE activo = true;"
        df = pd.read_sql_query(query, engine)

        # Data cleaning/formatting
        if not df.empty:
            # Drop rows without prices or years
            df = df.dropna(subset=['precio_numerico', 'año'])
            df['precio_numerico'] = pd.to_numeric(df['precio_numerico'], errors='coerce')
            df['año'] = pd.to_numeric(df['año'], errors='coerce')
            df = df.dropna(subset=['precio_numerico', 'año'])

            # Convert year to int
            df['año'] = df['año'].astype(int)

        return df
    except Exception as e:
        print(f"Error connecting to database: {e}")
        # Return empty DataFrame with expected columns if DB fails
        return pd.DataFrame(columns=[
            'marca', 'modelo', 'año', 'precio_numerico', 'provincia',
            'kilometraje_numerico', 'transmision', 'combustible', 'estilo'
        ])

# Build the layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("🚗 CRAutos Market Dashboard", className="text-center my-4"), width=12)
    ]),

    # Store component for sharing data
    dcc.Store(id='store-data'),

    # Filters
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Marca"),
                    dcc.Dropdown(id='filter-marca', multi=True, placeholder="Seleccione marcas...")
                ], width=4),
                dbc.Col([
                    html.Label("Rango de Años"),
                    dcc.RangeSlider(
                        id='filter-ano',
                        min=1980,
                        max=2025,
                        step=1,
                        value=[2010, 2025],
                        marks={i: str(i) for i in range(1980, 2026, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=8),
            ]),
            html.Div(
                dbc.Button("Actualizar Datos", id="btn-refresh", color="primary", className="mt-3"),
                className="text-end"
            )
        ]),
        className="mb-4"
    ),

    # Key Metrics (KPIs)
    dbc.Row(id='kpi-row', className="mb-4"),

    # Charts
    dbc.Row([
        dbc.Col(dbc.Card(dcc.Graph(id='chart-brands')), width=6),
        dbc.Col(dbc.Card(dcc.Graph(id='chart-prices-year')), width=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dcc.Graph(id='chart-transmission')), width=4),
        dbc.Col(dbc.Card(dcc.Graph(id='chart-fuel')), width=4),
        dbc.Col(dbc.Card(dcc.Graph(id='chart-province')), width=4),
    ], className="mb-4"),

], fluid=True, className="p-4 bg-light")

@app.callback(
    Output('store-data', 'data'),
    Output('filter-marca', 'options'),
    [Input('btn-refresh', 'n_clicks')]
)
def load_data(n_clicks):
    df = get_data()
    if df.empty:
        return None, []

    # Update options for marca dropdown
    marcas = sorted(df['marca'].dropna().unique())
    options = [{'label': m, 'value': m} for m in marcas]

    # Store df as json
    return df.to_json(date_format='iso', orient='split'), options

@app.callback(
    Output('kpi-row', 'children'),
    Output('chart-brands', 'figure'),
    Output('chart-prices-year', 'figure'),
    Output('chart-transmission', 'figure'),
    Output('chart-fuel', 'figure'),
    Output('chart-province', 'figure'),
    [Input('store-data', 'data'),
     Input('filter-marca', 'value'),
     Input('filter-ano', 'value')]
)
def update_dashboard(jsonified_data, selected_marcas, year_range):
    # Default empty figures
    empty_fig = go.Figure()
    empty_fig.update_layout(template="simple_white", title="Sin datos")

    if jsonified_data is None:
        return [dbc.Col(html.H4("No hay datos disponibles en la base de datos.", className="text-danger"))], \
               empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    df = pd.read_json(jsonified_data, orient='split')
    if df.empty:
        return [dbc.Col(html.H4("No hay datos disponibles.", className="text-danger"))], \
               empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # Apply filters
    if selected_marcas:
        df = df[df['marca'].isin(selected_marcas)]

    if year_range:
        df = df[(df['año'] >= year_range[0]) & (df['año'] <= year_range[1])]

    if df.empty:
        return [dbc.Col(html.H4("No hay resultados para los filtros seleccionados.", className="text-warning"))], \
               empty_fig, empty_fig, empty_fig, empty_fig, empty_fig

    # 1. KPIs
    total_cars = len(df)
    avg_price = df['precio_numerico'].mean()
    median_price = df['precio_numerico'].median()
    top_brand = df['marca'].mode()[0] if not df['marca'].empty else "N/A"

    def make_kpi_card(title, value, color="primary"):
        return dbc.Col(dbc.Card([
            dbc.CardHeader(title, className=f"bg-{color} text-white fw-bold"),
            dbc.CardBody(html.H3(value, className="text-center mb-0"))
        ]), width=3)

    kpis = [
        make_kpi_card("Total Autos", f"{total_cars:,}"),
        make_kpi_card("Precio Promedio", f"₡{avg_price:,.0f}" if not pd.isna(avg_price) else "N/A", "success"),
        make_kpi_card("Precio Mediano", f"₡{median_price:,.0f}" if not pd.isna(median_price) else "N/A", "info"),
        make_kpi_card("Marca Más Popular", top_brand, "warning"),
    ]

    # 2. Charts

    # Top 10 Brands Bar Chart
    top_brands = df['marca'].value_counts().head(10).reset_index()
    top_brands.columns = ['Marca', 'Cantidad']
    fig_brands = px.bar(top_brands, x='Cantidad', y='Marca', orientation='h',
                        title='Top 10 Marcas Más Publicadas', color='Cantidad',
                        color_continuous_scale='Blues')
    fig_brands.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)

    # Average Price by Year (Line Chart)
    price_by_year = df.groupby('año')['precio_numerico'].mean().reset_index()
    fig_prices_year = px.line(price_by_year, x='año', y='precio_numerico', markers=True,
                              title='Evolución del Precio Promedio por Año',
                              labels={'año': 'Año', 'precio_numerico': 'Precio Promedio (₡)'})

    # Transmission Distribution (Pie Chart)
    trans_counts = df['transmision'].value_counts().reset_index()
    trans_counts.columns = ['Transmisión', 'Cantidad']
    fig_trans = px.pie(trans_counts, values='Cantidad', names='Transmisión', title='Distribución por Transmisión', hole=0.3)

    # Fuel Distribution (Pie Chart)
    fuel_counts = df['combustible'].value_counts().reset_index()
    fuel_counts.columns = ['Combustible', 'Cantidad']
    fig_fuel = px.pie(fuel_counts, values='Cantidad', names='Combustible', title='Distribución por Combustible', hole=0.3)

    # Top Provinces Bar Chart
    prov_counts = df['provincia'].value_counts().head(7).reset_index()
    prov_counts.columns = ['Provincia', 'Cantidad']
    fig_prov = px.bar(prov_counts, x='Provincia', y='Cantidad', title='Distribución por Provincia', color='Provincia')
    fig_prov.update_layout(showlegend=False)

    return kpis, fig_brands, fig_prices_year, fig_trans, fig_fuel, fig_prov

if __name__ == '__main__':
    # Usar debug=False para producción y puerto 8050
    app.run_server(host='0.0.0.0', port=8050, debug=False)
