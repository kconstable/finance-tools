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
from dash.dependencies import Input, Output, State
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


# CARDS -----------------------------------------------------------------------
card_mtg_purchase = dbc.Card(
    [
        dbc.CardHeader("Mortgage Purchase"),
        dbc.CardBody([
            html.P("Purchase Price", className="card-subtitle pt-2"),
            dcc.Input(id='price', type='number', value=900000, min=100000,
                      max=1000000, step=50000, style={'format': '$0.00'}),
            html.P("Deposit", className='card-subtitle pt-2'),
            dcc.Input(id='deposit', type='number', value=140000, min=0,
                      max=250000, step=10000),
            html.P("Interest (annual %)", className='card-subtitle pt-2'),
            dcc.Input(id='ir_annual', type='number', min=0,
                      max=10, step=0.05, value=1.45),
        ], style={'font-size': 14}),
    ], color="secondary", outline=True, className="mb-1"
)

card_mtg_payments = dbc.Card(
    [
         dbc.CardHeader("Mortgage Payments"),
         dbc.CardBody([
             html.P("Payment Frequency", className='card-subtitle'),
             dcc.Dropdown(
                          id='dd_freq',
                          options=[
                              {'label': 'Monthly', 'value': 'm'},
                              {'label': 'Bi-Weekly', 'value': 'b'},
                              ],
                          value='m'
                          ),
             html.P("Payment", className='card-subtitle pt-2'),
             dcc.Input(id='payment', type='number', value=3500, min=500,
                       max=6000, step=100),
             ], style={'font-size': 14}
         )
    ], color='secondary', outline=True, className="mb-1"
)

card_mtg_equity = dbc.Card(
    [
         dbc.CardHeader("Mortgage Equity"),
         dbc.CardBody(
            [
             html.P("Appreciation (annual %)", className='card-subtitle'),
             dcc.Input(id='apr_annual', type='number', min=-10,
                       max=10, step=0.05, value=5.0),
             html.P("Real Estate Fee (%)", className='card-subtitle pt-2'),
             dcc.Input(id='re_fee', type='number', min=0,
                       max=10, step=0.05, value=5.0),
            ], style={'font-size': 14})
    ], color='secondary', outline=True, className="mb-1"
)

card_rent = dbc.Card(
    [
     dbc.CardHeader("Rent Parameters"),
     dbc.CardBody(
         [
             html.P("Rent (monthly)", className='card-subtitle'),
             dcc.Input(id='rent', type='number', min=0, max=10000, step=100, value=2500),
             html.P("Maintainence Fees (monthly)", className='card-subtitle pt-2'),
             dcc.Input(id='main-fees', type='number', min=0, max=1500, step=50, value=650),
             html.P("Taxes (annual)", className='card-subtitle pt-2'),
             dcc.Input(id='tax', type='number', min=0, max=10000, step=50, value=5500),
             html.P("Investment Rate (Annual)", className='card-subtitle pt-2'),
             dcc.Input(id="inv-rate", type="number", min=-8, max=15, step=0.5, value=8.0)
         ], style={'font-size': 14}
     )
    ], color='secondary', outline=True, className="mb-1"
)

card_prepayments = dbc.Card(
    [
     dbc.CardHeader("Pre-Payments"),
     dbc.CardBody(
         [
             html.P("Amount", className='card-subtitle'),
             dcc.Input(id='prepay', type='number', min=0, max=100000,
                       step=1000, value=10000),
             html.P("Date of Payment", className='card-subtitle pt-2'),
             dcc.Input(id='prepay-date', type='text', value='yyyy-mm-dd'),
             html.Br(),
             html.Button("Add Payment", id='add-prepay', n_clicks=0,
                         className='btn btn-primary mt-2'),
             html.Button("Reset", id='reset-prepay', n_clicks=0,
                         className='btn btn-primary mt-2 ms-2'),
             dcc.Store(id='prepay-store', data=[], storage_type='memory')
         ], style={'font-size': 14}
     )
    ], color='secondary', outline=True, className="mb-1"
)

card_scenario = dbc.Card(
    [
     dbc.CardHeader("Scenarios"),
     dbc.CardBody(
         [
             html.P("Name", className='card-subtitle'),
             dcc.Input(id='scenario-name', type='text', value='Base'),
             html.Button("Add Scenario", id='add-scenario', n_clicks=0,
                         className='btn btn-primary mt-2'),
             html.Button("Reset", id='reset-scenario', n_clicks=0,
                         className='btn btn-primary mt-2 ms-2'),
             dcc.Store(id='store-scenario', data=[], storage_type='memory')
         ], style={'font-size': 14}
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
            dbc.CardGroup([card_mtg_purchase, card_mtg_payments, card_mtg_equity, card_prepayments,card_scenario]),
            html.Br(),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(id='plot-amort', className='shadow-lg'), width=8),
                    dbc.Col(dcc.Markdown(id='md-amort'), width=4, align='center')
                ]
            )
        ])
    elif active_tab == "rent_vs_buy":
        return html.Div([
            dbc.CardGroup([card_mtg_purchase, card_mtg_payments, card_mtg_equity, card_rent]),
            html.Br(),
            dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id='plot-rent-vs-buy', className="shadow-lg"), width=8),
                        dbc.Col(dcc.Markdown(id='md-rent-vs-buy'), width=4)
                    ]
                )
            ]),

    # elif active_tab == 'invest':
    #     return html.Div([

        # ])


@app.callback(
    [
     Output("plot-amort", 'figure'),
     Output('md-amort', 'children'),
     Output('prepay-store', 'data')
    ],
    [
     Input('price', 'value'),
     Input('deposit', 'value'),
     Input('payment', 'value'),
     Input('ir_annual', 'value'),
     Input('apr_annual', 'value'),
     Input('re_fee', 'value'),
     Input('dd_freq', 'value'),
     Input('add-prepay', 'n_clicks'),
     Input('reset-prepay', 'n_clicks'),
     State('prepay', 'value'),
     State('prepay-date', 'value'),
     State('prepay-store', 'data')
    ]
)
def plot_amortization(price, deposit, payment, ir, apr, fee, freq, n_prepay,
                      n_prepay_reset, prepay_value, prepay_date, prepay_store):

    # get a list of id's that changed
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # get the current date
    start_date = date.today()

    if n_prepay >= 1:
        if prepay_store is None:
            # create the first store
            prepay = [{'date': prepay_date, 'value': prepay_value}]
            prepay_store = prepay.copy()
        else:
            # append additional prepayments to the store
            prepay = {'date': prepay_date, 'value': prepay_value}
            prepay_store.append(prepay)
    else:
        # no prepayments
        prepay_store = None

    # if the reset prepayment button was clicked
    if 'reset-prepay' in changed_id:
        prepay_store = None

    # get the schedule
    df, end_date = loan_calc.get_amortization(start_date, price, deposit,
                                              payment, 25, ir, apr, freq, fee,
                                              prepay_store)
    # update the markdown summary
    total_int = df.interest.sum()
    end_equity = df.equity.max()
    diff = relativedelta(end_date, df.date.min())
    payback = f"{diff.years} Years, {diff.months} Months"

    # get prepayment summary for markdown summary
    prepay_str_title = ""
    prepay_str = ""
    if prepay_store is not None:
        prepay_str_title = """**Prepayments** """
        for prepayment in prepay_store:
            prepay_str += "${:,.0f} on {}  ".format(prepayment['value'],prepayment['date'])

    # summary text for markdown
    md = f"""
    
    #### Summary
    **Total Interest:**${total_int:,.0f}  
    **Ending Equity:** ${end_equity:,.0f}  
    **Payback Period:** {payback}
    
    {prepay_str_title}  
    {prepay_str}  
    """
    # create the plot
    fig = loan_calc.plot_amortization(df, end_date, yrs=[5, 10, 15])

    return fig, md, prepay_store

@app.callback(
    [Output("plot-rent-vs-buy", "figure"), Output("md-rent-vs-buy", "children")],
    [Input("rent" ,"value"),
     Input("main-fees" ,"value"),
     Input("tax", "value"),
     Input("inv-rate","value"),
     Input('price', 'value'),
     Input('deposit', 'value'),
     Input('payment','value'),
     Input('ir_annual','value'),
     Input('apr_annual', 'value'),
     Input('re_fee', 'value'),
     Input('dd_freq', 'value')
     ]
    )
def plot_rent_vs_buy(rent, fee, tax, inv_rate, price, deposit, payment,
                     ir, apr, re_fee, freq):

    # get the current date
    start_date = date.today()
    
    # get the amortization schedule
    df = loan_calc.get_rent_vs_own(start_date, price, deposit, payment, 25,
                                   ir, apr, freq, re_fee, rent, inv_rate,
                                   fee, tax)
    # create the plot
    fig = loan_calc.plot_rent_vs_own(df)

    # calculate values for the summary markdown
    if freq=='m':
        frequency='Monthly'
        diff_payments = payment - rent
        taxes = tax/12
        main = fee
    else:
        frequency='Bi-Weekly'
        diff_payments = payment - rent
        taxes = tax/24
        main = fee/2
        
    md = f"""
    #### Rent Vs Buy
    This plot compares purchasing a home vs renting.  Owning a home requires additional 
    costs which are invested in the stock market for comparision.  
    
    **Invest in the Stock Market**  (Annual Return Assumption {inv_rate:.2f}%)
    + Downpayment:${deposit:,.0f}
    + Maintenence Fees ({frequency}):${main:,.0f}
    + Taxes ({frequency}):${taxes:,.0f}
    + Difference in Mortgage Payments vs Rent:${diff_payments:,.0f}
    
    **Mortgage Equity**  
    Equity is calculated as the difference in home value (annual appreciation 
    rate of {apr:.2f}%), less the outstanding mortgage and real estate fees of
    {re_fee:.2f}%.
    """
    
    return fig, md

# @app.callback(
#     [Output('prepay-store', 'data'),Output('plot-amort', 'figure')],
#     Input('add-prepay', 'n_clicks'),
#     [State('prepay-date', 'value'), 
#       State('prepay', 'value'),
#       State('price', 'value'),
#       State('deposit', 'value'),
#       State('payment', 'value'),
#       State('ir_annual', 'value'),
#       State('apr_annual', 'value'),
#       State('re_fee', 'value'),
#       State('dd_freq', 'value')
#       ],
    
# )
# def store_prepay_data(n, prepay_date, prepay_value, price, deposit, 
#                       payment, ir, apr, fee, freq):
    
#     # update the dataset
#     prepay = {'date': prepay_date, 'value': prepay_value}
    
#     # get the current date
#     start_date = date.today()
    
#     # get the schedule
#     df, end_date = loan_calc.get_amortization(start_date, price, deposit, payment, 25,
#                                     ir, apr, freq, fee, prepay)
    
    
    
#     fig = loan_calc.plot_amortization(df, end_date)
        
#     PREPAYMENTS.append(prepay)
    
#     return prepay, fig

    
