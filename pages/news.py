# pages/news.py

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from utils.data_handler import fetch_market_news

dash.register_page(__name__, name='News & Insights')

layout = dbc.Container([
    html.H2("Latest Market News & Insights", className="mb-4 text-center"),
    dcc.Loading(
        id="loading-news",
        type="default",
        children=html.Section(id="news-feed-container")
    )
], fluid=True, className="mt-4")

@callback(
    Output("news-feed-container", "children"),
    Input("news-feed-container", "id") # Trigger callback on page load
)
def update_news_feed(_):
    news_articles = fetch_market_news()
    
    if not news_articles or "Error" in news_articles[0]['title']:
        return dbc.Alert("Could not load market news. Please try again later.", color="warning")

    news_cards = []
    for article in news_articles:
        if 'link' in article:
            card = html.Article(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(html.A(article['title'], href=article.get('link'), target='_blank', className="stretched-link text-decoration-none text-light")),
                        html.P(f"Publisher: {article.get('publisher', 'N/A')}", className="small text-muted mb-0")
                    ]),
                    className="mb-3"
                )
            )
            news_cards.append(card)
    
    return news_cards
