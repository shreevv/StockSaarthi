import dash
import dash_bootstrap_components as dbc

# Initialize the app here and import it everywhere else
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP])
