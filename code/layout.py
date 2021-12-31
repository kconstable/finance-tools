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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.UNITED])
app.config['suppress_callback_exceptions'] = True

# LAYOUT ----------------------------------------------------------------------
app.layout = dbc.Container(
    [
        # dcc.Store(id="store"),
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
            dbc.Row(
                [
                    dbc.Col(html.H6("Price")),
                    dbc.Col(dcc.Input(id='price', type='number', min=0, max=1000000, step=500, value=900000)),
                    dbc.Col(html.H6("Deposit")),
                    dbc.Col(dcc.Input(id='deposit', type='number', min=0, max=1000000, step=500, value=145000)),
                    dbc.Col(html.H6("Payment")),
                    dbc.Col(dcc.Input(id='payment', type='number', min=0, max=10000, step=100, value=3500)),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.H6("IR (annual)")),
                    dbc.Col(dcc.Input(id='ir_annual', type='number', min=0, max=10, step=0.05, value=1.45)),
                    dbc.Col(html.H6("APR (annual)")),
                    dbc.Col(dcc.Input(id='apr_annual', type='number', min=-10, max=10, step=0.05, value=5.0)),
                    dbc.Col(html.H6("Real Estate Fee")),
                    dbc.Col(dcc.Input(id='re_fee', type='number', min=0, max=10, step=0.05, value=5.0)),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.H6("Start Date")),
                    dbc.Col(dcc.DatePickerSingle(
                                    id='start-date',
                                    min_date_allowed=date(2022, 1, 1),
                                    initial_visible_month=date(2022, 1, 1),
                                    date=date(2022, 1, 1)
                                )),
                    dbc.Col(html.H6("Payment Frequency")),
                    dbc.Col(dcc.Dropdown(
                        id='dd_freq',
                        options=[
                            {'label': 'Monthly', 'value': 'm'},
                            {'label': 'Bi-Weekly', 'value': 'b'},
                            ],
                        value='m'
                        ))
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id='plot-amort'), width=8),
                    dbc.Col(dcc.Markdown(id='md-amort'), width=4)
                ]
            )
        ])
    elif active_tab == "rent_vs_buy":
        return html.Div([
            dbc.Row(
                [
                    dbc.Col(html.H6("Price")),
                    dbc.Col(dcc.Input(id='price', type='number', min=0, max=1000000, step=500, value=900000)),
                    dbc.Col(html.H6("Deposit")),
                    dbc.Col(dcc.Input(id='deposit', type='number', min=0, max=1000000, step=500, value=145000)),
                    dbc.Col(html.H6("Payment")),
                    dbc.Col(dcc.Input(id='payment', type='number', min=0, max=10000, step=100, value=3500)),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.H6("IR (annual)")),
                    dbc.Col(dcc.Input(id='ir_annual', type='number', min=0, max=10, step=0.05, value=1.45)),
                    dbc.Col(html.H6("APR (annual)")),
                    dbc.Col(dcc.Input(id='apr_annual', type='number', min=-10, max=10, step=0.05, value=5.0)),
                    dbc.Col(html.H6("Real Estate Fee")),
                    dbc.Col(dcc.Input(id='re_fee', type='number', min=0, max=10, step=0.05, value=5.0)),
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.H6("Start Date")),
                    dbc.Col(dcc.DatePickerSingle(
                                    id='start-date',
                                    min_date_allowed=date(2022, 1, 1),
                                    initial_visible_month=date(2022, 1, 1),
                                    date=date(2022, 1, 1)
                                )),
                    dbc.Col(html.H6("Payment Frequency")),
                    dbc.Col(dcc.Dropdown(
                        id='dd_freq',
                        options=[
                            {'label': 'Monthly', 'value': 'm'},
                            {'label': 'Bi-Weekly', 'value': 'b'},
                            ],
                        value='m'
                        ))
                ]
            ),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(html.H6("Rent (monthly)")),
                    dbc.Col(dcc.Input(id='rent', type='number', min=0, max=10000, step=100, value=2500)),
                    dbc.Col(html.H6("Fees (monthly)")),
                    dbc.Col(dcc.Input(id='main-fees', type='number', min=0, max=1500, step=50, value=650)),
                    dbc.Col(html.H6("Taxes (annual)")),
                    dbc.Col(dcc.Input(id='tax', type='number', min=0, max=10000, step=50, value=5500)),
                    dbc.Col(html.H6("Invest Rate(annual)")),
                    dbc.Col(dcc.Input(id="inv-rate", type="number", min=-8, max=15, step=0.5, value=8.0))
                ]
            ),
            html.Br(),
            dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='plot-rent-vs-buy'), width=8),
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
    
    
    
