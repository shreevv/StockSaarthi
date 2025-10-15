# pages/news.py
import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from utils.data_handler import fetch_market_news

dash.register_page(__name__, name='Market News')

layout = dbc.Container(fluid=True, className="mt-4", children=[
    html.H2("Latest Market News & Insights", className="text-center mb-4"),
    dcc.Loading(
        id="loading-news",
        type="default",
        children=html.Div(id="news-feed-container")
    )
])

@callback(
    Output("news-feed-container", "children"),
    Input("news-feed-container", "id")
)
def update_news_feed(_):
    news_articles = fetch_market_news()
    
    if not news_articles or "Error" in news_articles[0]['title']:
        return dbc.Alert(news_articles[0]['title'], color="warning")

    news_cards = [
        dbc.Col(md=6, lg=4, children=
            html.A(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(article['title'], className="h6"),
                        html.P(f"Publisher: {article.get('publisher', 'N/A')}", className="small text-muted mb-0")
                    ]),
                    className="mb-4 h-100" # h-100 for equal height cards
                ),
                href=article.get('link'),
                target='_blank',
                className="text-decoration-none"
            )
        ) for article in news_articles if 'link' in article
    ]
    
    return dbc.Row(news_cards)
