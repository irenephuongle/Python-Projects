import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from scipy.stats import nbinom

# Load the dataset
villagers = pd.read_csv('villagers.csv')

def calculate_probability(villager_name, same_species, df=villagers):
    villager_row = df[df['Name'].str.lower() == villager_name.lower()]
    if villager_row.empty:
        raise ValueError(f"Villager '{villager_name}' not found in the dataset.")

    species = villager_row['Species'].values[0]
    species_total = len(df['Species'].unique())
    villagers_given_species = len(df[df['Species'].str.lower() == species.lower()])

    # Ensure villagers_given_species is at least 1 to avoid division by zero
    villagers_given_species = max(1, villagers_given_species)

    probability = (1 / species_total) * (1 / (villagers_given_species - same_species))
    return probability

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Animal Crossing Villager Hunt Probability Prediction", className="text-center text-primary mt-3 mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dbc.Label("Select a Villager:", className="font-weight-bold"),
                            dcc.Dropdown(
                                id="villager-dropdown",
                                options=[{"label": row['Name'], "value": row['Name']} for index, row in villagers.iterrows()],
                                placeholder="Select a villager",
                                className="mb-3",
                            ),
                            dbc.Label("Number of Nook Mile Tickets:", className="font-weight-bold"),
                            dbc.Input(id="nmt", type="number", value=1, min=1, step=1, className="mb-3"),
                            dbc.Label("Number of villagers of the same species on your island:", className="font-weight-bold"),
                            dbc.Input(id="same-species", type="number", value=1, min=0, step=1, className="mb-3"),
                            dbc.Button("Calculate", id="calculate-button", color="primary", className="mt-2"),
                        ]
                    ),
                ],
                className="shadow-sm p-3 mb-5 bg-white rounded"
            ),
        ], width=4),
        dbc.Col([
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(id="probability-output", className="text-primary"),
                            dcc.Graph(id="probability-plot", config={"displayModeBar": False}),
                        ]
                    ),
                ],
                className="shadow-sm p-3 mb-5 bg-white rounded"
            ),
        ], width=8)
    ]),
], fluid=True)

# Define callback to update the output
@app.callback(
    [Output("probability-output", "children"),
     Output("probability-plot", "figure")],
    [Input("calculate-button", "n_clicks")],
    [State("villager-dropdown", "value"),
     State("nmt", "value"),
     State("same-species", "value")]
)
def update_output(n_clicks, villager_name, nmt, same_species):
    if villager_name is None or nmt is None or nmt < 1 or same_species is None or same_species < 0 or same_species > 10:
        return "Please select a villager, enter a valid number of attempts, and enter a valid number of villagers of the same species.", {}

    try:
        p = calculate_probability(villager_name, same_species)
    except ValueError as e:
        return str(e), {}

    # Calculate the probability using the negative binomial cumulative distribution function
    nmt_probability = (nbinom.cdf(nmt, 1, p)) * 100

    # Generate the plot
    x = range(1, nmt)
    y = [(nbinom.cdf(i, 1, p)) * 100 for i in x]

    fig = {
        "data": [{
            "x": list(x),
            "y": list(y),
            "type": "line",
            "name": "Probability",
            "marker": {"color": "#007BFF"},
        }],
        "layout": {
            "title": {
                "text": "Probability of finding your dream villager",
                "x": 0.5,
                "font": {"size": 20},
            },
            "xaxis": {"title": "Nook Mile Tickets", "titlefont": {"size": 18}, "tickfont": {"size": 14}},
            "yaxis": {"title": "Probability (%)", "titlefont": {"size": 18}, "tickfont": {"size": 14}},
            "margin": {"l": 40, "r": 20, "t": 60, "b": 40},
            "plot_bgcolor": "#f8f9fa",
            "paper_bgcolor": "#f8f9fa",
        }
    }
    if nmt == 1:
        return f"The probability of finding {villager_name} with 1 Nook Mile Ticket is: {p * 100:.2f}%", fig
    return f"The probability of finding {villager_name} in a single attempt is: {p * 100:.2f}%\n\n and the probability of finding {villager_name} with {nmt} Nook Mile Tickets is: {nmt_probability:.2f}%", fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)