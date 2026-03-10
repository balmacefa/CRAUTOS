import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import requests
import os
from datetime import datetime
import dash_bootstrap_components as dbc

# Define the base API URL (could be from environment)
API_URL = os.environ.get("API_URL", "http://backend:8000")

# --- 1. Inicialización de la App Dash ---
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Dashboard de CRAutos",
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
)
server = app.server

def fetch_data_from_api():
    try:
        print("Fetching data from backend API...")
        response = requests.get(f"{API_URL}/api/cars?limit=1000")
        if response.status_code == 200:
            cars = response.json()
            if not cars:
                return pd.DataFrame()

            # Map API fields to the format expected by the dashboard
            df = pd.DataFrame(cars)
            # rename or create necessary columns
            if 'precio_numerico' in df.columns:
                df['precio_crc'] = df['precio_numerico']
            if 'kilometraje_numerico' in df.columns:
                df['kilometraje'] = df['kilometraje_numerico']

            # Convert year to numeric and calculate 'antiguedad'
            df['año'] = pd.to_numeric(df['año'], errors='coerce')
            df['precio_crc'] = pd.to_numeric(df['precio_crc'], errors='coerce')
            df['kilometraje'] = pd.to_numeric(df['kilometraje'], errors='coerce')

            # Drop nulls where necessary
            df = df.dropna(subset=['precio_crc', 'año'])

            df['antiguedad'] = datetime.now().year - df['año']
            df['antiguedad'] = df['antiguedad'].apply(lambda x: max(0, x))

            if 'combustible' not in df.columns or df['combustible'].isnull().all():
                df['combustible'] = 'Gasolina'
            if 'transmision' not in df.columns or df['transmision'].isnull().all():
                df['transmision'] = 'Automática'
            if 'cantidad_extras' not in df.columns:
                df['cantidad_extras'] = 0
            if 'cilindrada' not in df.columns:
                df['cilindrada'] = 1500

            return df
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return pd.DataFrame()

df = fetch_data_from_api()

# Fallback empty dataframe if no data could be fetched
if df.empty:
    df = pd.DataFrame({
        "marca": ["Sin Data"], "modelo": ["Sin Data"], "año": [2020],
        "precio_crc": [0], "kilometraje": [0], "antiguedad": [0],
        "transmision": ["Manual"], "combustible": ["Gasolina"]
    })

# --- 2. Preparación de Datos para Análisis (Pre-cálculos) ---
print("Realizando pre-cálculos para el dashboard...")
# Estadísticas Generales
avg_price_total = df["precio_crc"].mean()
min_price_total = df["precio_crc"].min()
max_price_total = df["precio_crc"].max()

# Estadísticas por Marca
stats_by_brand = (
    df.groupby("marca")
    .agg({"precio_crc": ["mean", "count"], "kilometraje": "mean"})
    .reset_index()
)
stats_by_brand.columns = ["marca", "precio_promedio", "cantidad", "km_promedio"]
stats_by_brand = stats_by_brand.sort_values("cantidad", ascending=False)

# Datos para el gráfico de depreciación
depreciation_data = (
    df.groupby(["marca", "modelo", "antiguedad"])["precio_crc"].mean().reset_index()
)

# --- 3. Definición del Layout ---
print("Configurando la interfaz de usuario...")

navbar = dbc.NavbarSimple(
    brand="🚗 CRAutos Analytics Pro Dashboard",
    brand_href="#",
    color="primary",
    dark=True,
    fluid=True,
    className="mb-4 shadow",
)

app.layout = dbc.Container(
    [
        navbar,
        dcc.Tabs(
            [
                # Pestaña 1: Resumen del Mercado
                dcc.Tab(
                    label="📊 Resumen del Mercado",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.H4("Total de Vehículos", className="card-title"),
                                            html.H2(f"{len(df):,}", className="text-primary"),
                                        ],
                                        body=True,
                                        className="text-center shadow-sm h-100",
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.H4("Precio Promedio", className="card-title"),
                                            html.H2(
                                                f"₡{avg_price_total:,.0f}" if not pd.isna(avg_price_total) else "₡0",
                                                className="text-success",
                                            ),
                                        ],
                                        body=True,
                                        className="text-center shadow-sm h-100",
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.H4("Precio Mínimo", className="card-title"),
                                            html.H2(
                                                f"₡{min_price_total:,.0f}" if not pd.isna(min_price_total) else "₡0",
                                                className="text-info",
                                            ),
                                        ],
                                        body=True,
                                        className="text-center shadow-sm h-100",
                                    ),
                                    md=3,
                                ),
                                dbc.Col(
                                    dbc.Card(
                                        [
                                            html.H4("Precio Máximo", className="card-title"),
                                            html.H2(
                                                f"₡{max_price_total:,.0f}" if not pd.isna(max_price_total) else "₡0",
                                                className="text-danger",
                                            ),
                                        ],
                                        body=True,
                                        className="text-center shadow-sm h-100",
                                    ),
                                    md=3,
                                ),
                            ],
                            className="mb-4",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        figure=px.bar(
                                            stats_by_brand.head(15),
                                            x="cantidad",
                                            y="marca",
                                            orientation="h",
                                            title="Top 15 Marcas Más Populares",
                                            color="cantidad",
                                            color_continuous_scale="Viridis",
                                            template="plotly_white",
                                        ).update_layout(yaxis={"categoryorder": "total ascending"})
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        figure=px.histogram(
                                            df,
                                            x="precio_crc",
                                            nbins=50,
                                            title="Distribución de Precios",
                                            color_discrete_sequence=["skyblue"],
                                            template="plotly_white",
                                        ).update_layout(
                                            xaxis_title="Precio (CRC)",
                                            yaxis_title="Cantidad de Vehículos",
                                        )
                                    ),
                                    md=6,
                                ),
                            ]
                        ),
                    ],
                ),
                # Pestaña 2: Análisis Detallado
                dcc.Tab(
                    label="🔍 Análisis Detallado",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        figure=px.scatter(
                                            df,
                                            x="kilometraje",
                                            y="precio_crc",
                                            color="marca",
                                            hover_data=["modelo", "año"],
                                            title="Relación Precio vs Kilometraje",
                                            opacity=0.6,
                                            template="plotly_white",
                                        ).update_layout(
                                            xaxis_title="Kilometraje",
                                            yaxis_title="Precio (CRC)",
                                        )
                                    ),
                                    md=12,
                                    className="mb-4 mt-4",
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Graph(
                                        figure=px.box(
                                            df[
                                                df["marca"].isin(
                                                    stats_by_brand.head(10)["marca"]
                                                )
                                            ],
                                            x="marca",
                                            y="precio_crc",
                                            title="Rango de Precios por Marca (Top 10)",
                                            color="marca",
                                            template="plotly_white",
                                        ).update_layout(
                                            xaxis_title="Marca", yaxis_title="Precio (CRC)"
                                        )
                                    ),
                                    md=12,
                                )
                            ]
                        ),
                    ],
                ),
                # Pestaña 3: Depreciación por Modelo
                dcc.Tab(
                    label="📉 Curva de Depreciación",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Seleccione la Marca:", className="mt-4 fw-bold"),
                                        dcc.Dropdown(
                                            id="brand-depreciation-dropdown",
                                            options=sorted(df["marca"].unique()),
                                            value="Toyota" if "Toyota" in df["marca"].values else df["marca"].iloc[0],
                                            className="mb-3",
                                        ),
                                        html.Label("Seleccione el Modelo:", className="fw-bold"),
                                        dcc.Dropdown(
                                            id="model-depreciation-dropdown", className="mb-4"
                                        ),
                                    ],
                                    md=3,
                                ),
                                dbc.Col(
                                    [dcc.Graph(id="depreciation-chart")],
                                    md=9,
                                    className="mt-4",
                                ),
                            ]
                        )
                    ],
                ),
                # Pestaña 4: Herramienta de Predicción
                dcc.Tab(
                    label="🔮 Herramienta de Predicción",
                    children=[
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3(
                                        "Estima el valor de un vehículo usando la API de Predicción",
                                        className="card-title text-center",
                                    ),
                                    html.Hr(),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("Marca:", html_for="marca-dropdown"),
                                                    dcc.Dropdown(
                                                        id="marca-dropdown",
                                                        options=sorted(df["marca"].unique()),
                                                    ),
                                                    dbc.Label("Año:", html_for="año-input", className="mt-3"),
                                                    dbc.Input(
                                                        id="año-input",
                                                        type="number",
                                                        placeholder=f"Ej: {datetime.now().year - 3}",
                                                    ),
                                                    dbc.Label("Cilindrada (cc):", html_for="cilindrada-input", className="mt-3"),
                                                    dbc.Input(
                                                        id="cilindrada-input",
                                                        type="number",
                                                        placeholder="Ej: 1800",
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    dbc.Label("Modelo:", html_for="modelo-dropdown"),
                                                    dcc.Dropdown(id="modelo-dropdown"),
                                                    dbc.Label("Kilometraje:", html_for="kilometraje-input", className="mt-3"),
                                                    dbc.Input(
                                                        id="kilometraje-input",
                                                        type="number",
                                                        placeholder="Ej: 50000",
                                                    ),
                                                    dbc.Label("Tipo de Transmisión:", html_for="transmision-dropdown", className="mt-3"),
                                                    dcc.Dropdown(
                                                        id="transmision-dropdown",
                                                        options=df["transmision"].unique() if not df.empty else ["Automática", "Manual"],
                                                    ),
                                                ],
                                                md=6,
                                            ),
                                        ]
                                    ),
                                    dbc.Button(
                                        "Predecir Precio",
                                        id="predict-button",
                                        n_clicks=0,
                                        color="primary",
                                        className="w-100 mt-4 py-2 fs-5",
                                    ),
                                    html.Div(
                                        id="prediction-output",
                                        className="text-center h3 mt-4 p-3 border rounded",
                                    ),
                                ]
                            ),
                            className="mt-4",
                        )
                    ],
                ),
            ],
        ),
    ],
    fluid=True,
)


# --- 5. Callbacks de la App (Lógica Interactiva) ---

# Callback para actualizar el dropdown de modelos en la pestaña de predicción
@app.callback(Output("modelo-dropdown", "options"), Input("marca-dropdown", "value"))
def set_prediction_model_options(selected_marca):
    if not selected_marca or df.empty:
        return []
    return [{"label": i, "value": i} for i in sorted(df[df["marca"] == selected_marca]["modelo"].unique())]

# Callback para la predicción de precios (llamando a la API del backend)
@app.callback(
    Output("prediction-output", "children"),
    Input("predict-button", "n_clicks"),
    [
        State("marca-dropdown", "value"),
        State("modelo-dropdown", "value"),
        State("año-input", "value"),
        State("kilometraje-input", "value"),
        State("cilindrada-input", "value"),
        State("transmision-dropdown", "value"),
    ],
)
def predict_price(n_clicks, marca, modelo, año, kilometraje, cilindrada, transmision):
    if n_clicks == 0:
        return "Ingrese los datos del vehículo para obtener una estimación."
    if not all([marca, modelo, año, kilometraje, cilindrada, transmision]):
        return "⚠️ Por favor, complete todos los campos."

    payload = {
        "marca": marca,
        "modelo": modelo,
        "año": año,
        "kilometraje": kilometraje,
        "cilindrada": cilindrada,
        "transmision": transmision,
        "combustible": "Gasolina", # Defaulting for simplicity
        "cantidad_extras": 0 # Defaulting for simplicity
    }

    try:
        response = requests.post(f"{API_URL}/api/cars/predict_price", json=payload)
        if response.status_code == 200:
            result = response.json()
            precio_estimado = result.get("precio_estimado_crc", 0)
            return f"Precio Estimado: ₡{precio_estimado:,.0f}"
        else:
            return f"⚠️ Error en la predicción. Status: {response.status_code}"
    except Exception as e:
        return f"⚠️ Error de conexión con la API: {e}"

# Callback para actualizar el dropdown de modelos en la pestaña de depreciación
@app.callback(
    Output("model-depreciation-dropdown", "options"),
    Input("brand-depreciation-dropdown", "value"),
)
def set_depreciation_model_options(selected_marca):
    if not selected_marca or df.empty:
        return []
    return [{"label": i, "value": i} for i in sorted(df[df["marca"] == selected_marca]["modelo"].unique())]

# Callback para actualizar el gráfico de depreciación
@app.callback(
    Output("depreciation-chart", "figure"),
    Input("model-depreciation-dropdown", "value"),
    State("brand-depreciation-dropdown", "value"),
)
def update_depreciation_chart(selected_model, selected_brand):
    if not selected_model or not selected_brand or df.empty:
        return px.line(
            title="Seleccione una marca y modelo para ver su curva de depreciación",
            template="plotly_white",
        )

    filtered_data = depreciation_data[
        (depreciation_data["marca"] == selected_brand)
        & (depreciation_data["modelo"] == selected_model)
    ]

    if len(filtered_data) < 2:
        return px.line(
            title=f"No hay suficientes datos para graficar la depreciación de {selected_model}",
            template="plotly_white",
        )

    fig = px.line(
        filtered_data,
        x="antiguedad",
        y="precio_crc",
        title=f"Curva de Depreciación para {selected_brand} {selected_model}",
        labels={
            "antiguedad": "Antigüedad (Años)",
            "precio_crc": "Precio Promedio (CRC)",
        },
        markers=True,
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_title="Precio Promedio (CRC)",
        xaxis_title="Antigüedad (Años)",
    )
    return fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
