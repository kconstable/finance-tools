#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 30 11:36:06 2021

@author: ken
"""
# import plotly.graph_objects as go
import plotly.io as pio
import dash
from dash import html
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import Input, Output
from datetime import date
from dateutil.relativedelta import relativedelta
import loan_calc

# Render plots in a browswer
pio.renderers.default = 'browser'


# start the dash app
app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.UNITED],
                meta_tags=[{"name": "viewport",
                            "content": "width=device-width, initial-scale=1"}])
app.config['suppress_callback_exceptions'] = True
app.title = 'Investment Tools'

# LAYOUT ----------------------------------------------------------------------
app.layout = dbc.Container(
    [
        html.H1("Investment Tools"),
        html.Hr(),

        dbc.Tabs(
            [
                dbc.Tab(label="Mortgage Amortization", tab_id="mortgage"),
                dbc.Tab(label="Rent vs Buy", tab_id="rent_vs_buy"),
                dbc.Tab(label="Investment Projections", tab_id='invest'),
            ],
            id="tabs",
            active_tab="mortgage",
        ),
        html.Div(id="tab-content", className="p-4"),
    ]
)


CARD_STYLE = {
    'font-size': 12
    # "position": "fixed",
    # "top": 0,
    # "left": 0,
    # "bottom": 0,
    # "width": "16rem",
    # "padding": "2rem 1rem",
    # "background-color": "#f8f9fa",
}
# money = FormatTemplate.money(2)

# CARDS -----------------------------------------------------------------------
card_mtg_purchase = dbc.Card(
    [
        dbc.CardHeader("Mortgage Purchase"),
        dbc.CardBody([
            dbc.Row(
                [
                    dbc.Col(html.P("Purchase Date", className='card-text')),
                    dbc.Col(dcc.DatePickerSingle(
                                            id='start-date',
                                            min_date_allowed=date(2022, 1, 1),
                                            initial_visible_month=date(2022, 1, 1),
                                            date=date(2022, 1, 1)
                                        )),
                ]),
            html.P("Purchase Price", className="card-text"),
            dcc.Input(id='price', type='number', value=900000,style={'format':'$0.00'}),
            html.P("Deposit", className='card-text'),
            dcc.Input(id='deposit', type='number', value=140000),
        ],style = {'font-size':14}),
    ], color="secondary",outline=True, className="mb-1"
)

card_mtg_payments = dbc.Card(
    [   
         dbc.CardHeader("Mortgage Payments"),
         dbc.CardBody([
             html.P("Payment Frequency", className='card-text'),
             dcc.Dropdown(
                          id='dd_freq',
                          options=[
                              {'label': 'Monthly', 'value': 'm'},
                              {'label': 'Bi-Weekly', 'value': 'b'},
                              ],
                          value='m'
                          ),
             html.P("Payment", className='card-text'),
             dcc.Input(id='payment', type='number', value=3500),
             dbc.Row(
                 [
                     dbc.Col(html.P("Interest (annual %)", className='card-text')),
                     dbc.Col(dcc.Input(id='ir_annual', type='number', min=0,
                                       max=10, step=0.05, value=1.45)),
                     ]),
             # html.P("Interest (annual %)", className='card-text'),
             # dcc.Input(id='ir_annual', type='number', min=0,
             #                   max=10, step=0.05, value=1.45),
        ],style = {'font-size':14})
    ], color='secondary', outline=True, className="mb-1"
)

card_mtg_equity = dbc.Card(
    [
         dbc.CardHeader("Mortgage Equity"),
         dbc.CardBody([
             html.P("Appreciation (annual %)", className='card-text'),
             dbc.Col(dcc.Input(id='apr_annual', type='number', min=-10,
                               max=10, step=0.05, value=5.0)),
             html.P("Real Estate Fee (%)", className='card-text'),
             dbc.Col(dcc.Input(id='re_fee', type='number', min=0,
                               max=10, step=0.05, value=5.0)),
        ],style = {'font-size':14})
    ], color='secondary', outline=True, className="mb-1"
)

card_rent = dbc.Card(
    [
     dbc.CardHeader("Rent Parameters"),
     dbc.CardBody(
         [
             html.P("Rent (monthly)",className='card-text'),
             dcc.Input(id='rent', type='number', min=0, max=10000, step=100, value=2500),
             html.P("Maintainence Fees (monthly)",className='card-text'),
             dcc.Input(id='main-fees', type='number', min=0, max=1500, step=50, value=650),
             html.P("Taxes (annual)",className='card-text'),
             dcc.Input(id='tax', type='number', min=0, max=10000, step=50, value=5500),
             html.P("Investment Rate (Annual)",className='card-text'),
             dcc.Input(id="inv-rate", type="number", min=-8, max=15, step=0.5, value=8.0)
         ],style = {'font-size':14}
    )
    ], color='secondary', outline=True, className="mb-1"
)


# CALLBACKS--------------------------------------------------------------------
# tab content
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """

    if active_tab == "mortgage":
        return html.Div([
            dbc.CardGroup([card_mtg_purchase,card_mtg_payments,card_mtg_equity]),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id='plot-amort',className = 'shadow-lg'), width=8),
                    dbc.Col(dcc.Markdown(id='md-amort'), width=4,align = 'center')
                ]
            )
        ])
    elif active_tab == "rent_vs_buy":
        return html.Div([
            dbc.CardGroup([card_mtg_purchase, card_mtg_payments, card_mtg_equity, card_rent]),
            html.Br(),
            dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='plot-rent-vs-buy',className="shadow-lg"), width=8),
                        dbc.Col(dcc.Markdown(id='md-rent-vs-buy'), width=4)
                    ]
                )
            ]),

    # elif active_tab == 'invest':
    #     return html.Div([

        # ])


@app.callback(
    [Output("plot-amort", 'figure'), Output('md-amort', 'children')], [
        Input('start-date', 'date'),
        Input('price', 'value'),
        Input('deposit', 'value'),
        Input('payment', 'value'),
        Input('ir_annual', 'value'),
        Input('apr_annual', 'value'),
        Input('re_fee', 'value'),
        Input('dd_freq', 'value')
        ]
    )
def plot_amortization(start_date, price, deposit, payment, ir, apr, fee, freq):
    # get the schedule
    df = loan_calc.get_amortization(start_date, price, deposit, payment, 25,
                                    ir, apr, freq, fee)

    # update the markdown summary
    total_int = df.interest.sum()
    end_equity = df.equity.max()
    diff = relativedelta(df.date.max(), df.date.min())
    payback = f"{diff.years} Years, {diff.months} Months"

    md = f"""
    >
    > #### Summary
    > **Total Interest:**${total_int:,.0f}  
    > **Ending Equity:** ${end_equity:,.0f}  
    > **Payback Period:** {payback}
    """

    fig = loan_calc.plot_amortization(df, yrs=[5, 10])

    return fig, md

@app.callback(
    [Output("plot-rent-vs-buy", "figure"), Output("md-rent-vs-buy", "children")],
    [Input("rent" ,"value"),
     Input("main-fees" ,"value"),
     Input("tax", "value"),
     Input("inv-rate","value"),
     Input('start-date','date'),
     Input('price', 'value'),
     Input('deposit', 'value'),
     Input('payment','value'),
     Input('ir_annual','value'),
     Input('apr_annual', 'value'),
     Input('re_fee', 'value'),
     Input('dd_freq', 'value')
     ]
    )
def plot_rent_vs_buy(rent, fee, tax,inv_rate, start_date,price, deposit, payment,
                     ir,apr, re_fee,freq):
    
    df = loan_calc.get_rent_vs_own(start_date, price, deposit, payment, 25, ir, apr, freq,
                          re_fee, rent, inv_rate,
                          fee, tax)
    fig = loan_calc.plot_rent_vs_own(df)
    md = """ TBD """
    
    return fig, md
    
    
    
