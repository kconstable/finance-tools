# -*- coding: utf-8 -*-
"""
Created on Mon Dec 28 11:29:28 2020

@author: Ken Constable
"""

import pandas as pd
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
import calendar
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = 'browser'

# Mortgage Constants
IR = 1.45
YRS = 25
PAY = 3000
PRICE = 900000
DEPOSIT = 140000
APP_RATE = 5.0
START_DATE = date.today()
RE_FEES = 5.0
PRE_PAYMENTS = [{'date': '2024-06-01', 'value': 10000},
                {'date': '2026-12-22', 'value': 15000}
                ]


# Rent Constants
ANNUAL_INVEST_RATE = 10.0
MONTHLY_FEES = 650
ANNUAL_TAX = 5500
MONTHLY_RENT = 2500


def get_periods(start_date, yrs=25, frequency='b'):
    """
    Determine a range of dates from start_date to the number of years based
    on the frequency. Used to determine when mortgage payments will occur

    Parameters
    ----------
    start_date : date
        Start date of the projection
    yrs : int, optional
        Number of years to project. The default is 25.
    frequency : string, optional
        The freqency of dates: m=monthly, b=bi-monthly, a=every two weeks

    Returns
    -------
    A list of payment dates

    """

    # get end date
    end_date = start_date + timedelta(days=yrs*365)

    # get payment dates
    if frequency == 'd':
        # daily (calendar days)
        rng = pd.date_range(start_date, end=end_date, freq='D')
    elif frequency == 'm':
        # monthly
        rng = pd.date_range(start_date, end=end_date, freq='M')
    elif frequency == 'b':
        # bi-weekly: 15th, Last-day-of-month (24 pay-periods)
        rng = pd.date_range(start_date, end=end_date, freq='SM')
    elif frequency == 'a':
        # accelerated bi-weekly, every-14-days (26 pay-periods)
        rng = []
        dt = start_date
        while dt + timedelta(days=14) <= end_date:
            dt = dt + timedelta(days=14)
            rng.append(pd.Timestamp(dt))
    else:
        # undefined
        print('unknown frequency')
        rng = []

    return rng




def get_amortization(start_date, price, deposit, payment, yrs, int_rate, app_rate,
                     frequency, re_fees, prepayments=None, scenarios=None):
    """
    Creates an amortization schedule for a mortgage repayment. Assumes monthly
    or bi-weekly (15th, last of month) payments. Adjust payment according to
    the frequency. Interest rates are converted to monthly or bi-weekly, and
    charged at month-end or the 15th and month-end after payments have been
    applied. Creditors normally accrue interest daily.  This simplification
    will underestimate the interest paid, but will not have a material impact
    on the results

    Parameters
    ----------
    start_date: string
        Start date of the amortization schedule
    price : float
        Property purchase price
    deposit : float (dollars)
        deposit for down-payment in dollars
    payment: float
        A payment amount- should match the frequency: string
        'm'-monthly or 'b'-bi-weekly
    yrs : int
        Number of years to amortize
    int_rate : float (percent *100)
        Annual interest rate (1.45% = 4.45)
    app_rate : float (percent *100)
        Annual appreciation rate of the property (8% = 8.0)
    frequency : string
        frequency of payment: m-monthly, b=bi-weekly
    re_fees: float (percent *100)
        real estate fees - used to calculate mortgage equity on sale
    prepayments : List of dicts
        A list of dicts containing prepayments {date, amount}
    scenarios : List of dicts
        A list of dicts containing saved scearios (date,end)
    Returns
    -------
    A dataframe with the amortization schedule

    """

    # convert rates, calc mortgage, get date range
    ir = get_georeturn(int_rate, 'd')
    app = get_georeturn(app_rate, 'd')
    fees = re_fees / 100
    mortgage = price - deposit
    date_rng = get_periods(start_date, yrs, 'd')  # daily range
    pay_rng = get_periods(start_date, yrs, frequency)  # pay-periods

    # init the dataframe
    df = pd.DataFrame(date_rng, columns=['date'])
    df['frequency'] = frequency
    df['pay_period'] = False
    df['start'] = 0.0
    df['payment'] = 0.0
    df['prepayment'] = 0.0
    df['interest'] = 0.0
    df['end'] = 0.0
    df['value'] = 0.0
    df['equity'] = 0.0
    df['elapsed_years'] = 0

    # add prepayments
    if prepayments is not None:
        for prepayment in prepayments:

            # get the index for the prepayment date
            idx = df[df.date == prepayment['date']].index.values.astype(int)[0]

            # add the prepayment
            df.at[idx, 'prepayment'] = prepayment['value']

    # create the amortization schedule
    for idx, row in df.iterrows():

        # first period
        if idx == 0:
            df.at[0, 'start'] = mortgage
            end_date = start_date
            value = price

        # add payment if it's a pay period according to the frequency selected
        if row.date in pay_rng:
            pay = payment
        else:
            pay = 0

        # calc interest
        int_pay = (df.at[idx, 'start'] - pay - df.at[idx, 'prepayment']) * ir

        # calc end balance
        end = df.at[idx, 'start'] + int_pay - pay - df.at[idx, 'prepayment']

        # calc appreciation
        value = value * (1 + app)

        # update amortization schedule
        if end > 0:
            # update schedule
            df.at[idx, 'payment'] = pay
            df.at[idx, 'interest'] = int_pay
            df.at[idx, 'end'] = end
            df.at[idx, 'value'] = value
            df.at[idx, 'equity'] = (value - end) - (value * fees)
            df.at[idx + 1, 'start'] = end
            end_date = df.at[idx, 'date']

            # get elapsed time
            diff = relativedelta(end_date, start_date)
            diff_yrs = diff.years + diff.months/12
            df.at[idx, 'elapsed_yrs'] = diff_yrs

        else:
            # mortgage paid off
            df.at[idx, 'payment'] = df.at[idx, 'start']
            df.at[idx, 'interest'] = 0
            df.at[idx, 'end'] = 0
            df.at[idx, 'value'] = value
            df.at[idx, 'equity'] = (value - end) - (value * fees)
            end_date = df.at[idx, 'date']

            # get elapsed time
            diff = relativedelta(end_date, start_date)
            diff_yrs = diff.years + diff.months/12
            df.at[idx, 'elapsed_yrs'] = diff_yrs
            break

    # add scenarios if provided
    if scenarios is not None:
        # add the scenarios
        # scenario_store will be a list of dicts, convert to df
        scenarios_df = pd.DataFrame(scenarios)
        scenarios_df['date'] = pd.to_datetime(scenarios_df['date']).dt.date

        # join scenarios with current df based on date
        df = df.set_index('date').join(scenarios_df.set_index('date'), how='inner')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'date'}, inplace=True)

    # return the dataframe, exclcude nan rows (happens
    # when the mortgage isn't paid after 25 years)
    df = df[~df.date.isnull()]
    return df, end_date


def get_georeturn(rate, frequency='d'):
    """
    Converts annual rate of return to monthly, bi-weekly or daily

    Parameters
    ----------
    rate : float
        Annual rate of return (5.0)==5.0%
    frequency : string
        Frequency to convert to: m=monthly, d=daily

    Returns
    -------
    float

    """
    r = rate / 100

    if frequency == 'm':
        return (1 + r) ** (1 / 12) - 1
    elif frequency == 'd':
        return (1 + r) ** (1 / 365) - 1
    else:
        print('frequency not recongized')


def plot_amortization(df_amort, end_date, yrs=[5, 10, 15]):
    """
    Plot the amortization schedule (ending balance + cumulative interest)

    Parameters
    ----------
    df_amort : dataframe
        Dataframe containing the amortization schedule (output from get_amortization)
    yrs : list of ints
        A list of years. Used as annotations on the plot

    Returns
    -------
    Plotly figure

    """

    # copy df
    df = df_amort.copy()

    # get the number of years to pay-off
    if df.end.min() > 0:
        diff_yrs = "> 25 "
    else:
        diff = relativedelta(end_date, df.date.min())
        diff_yrs = str(diff.years)

    # get cumulative interest
    df['cum_interest'] = df.interest.cumsum()
    total_interest = df.interest.sum()

    # sub-title text
    subtitle = f'Amortization:{diff_yrs} Years | Total Interest:${total_interest:,.0f}'

    # create plots
    fig = go.Figure()

    # get extra data for hovertext
    customdata = list(zip(df['elapsed_yrs'], df.equity, df.cum_interest))

    # outstanding mortgage
    fig.add_trace(
        go.Scattergl(
            name='Mortgage',
            x=df.date,
            y=df.end,
            line=dict(color='#536872'),
            fill='tozeroy',
            customdata=customdata,
            hovertemplate="""<b>Mortgage:</b> $%{y:,.0f}
                               <br><b>Cumulative Interest:</b> $%{customdata[2]:,.0f}
                               <br><b>Equity:</b> $%{customdata[1]:,.0f}
                               <br><b>Elapsed Years:</b> %{customdata[0]:.2f}
                               <extra></extra>""",
        )
    )

    # cumulative interest
    fig.add_trace(
        go.Scattergl(
            name='Interest',
            x=df.date,
            y=df.cum_interest,
            line=dict(color='#E95420'),
            fill='tozeroy',
            hoverinfo='skip'
        )
    )
    # add sub-title
    fig.add_annotation(
        text=subtitle,
        xref="paper", yref="paper",
        x=-0.07, y=1.12,
        showarrow=False,
        font=dict(size=18)

    )

    # add scenarios if provided
    scenarios = [c for c in df.columns if 'scenario' in c]
    colors = ['#E95420', '#ff7f0e', 'gold', 'crimson']
    dash = ['dash', 'dot', 'dashdot', 'longdash']
    if len(scenarios) >= 1:
        for i, scen in enumerate(scenarios):
            fig.add_trace(
                go.Scattergl(
                    name=scen,
                    x=df.date,
                    y=df[scen],
                    line=dict(color=colors[i], dash=dash[i], width=3)
                )
            )

    fig.update_layout(
        title='Mortgage Amortization',
        template='plotly_white',
        hovermode="x",
        font=dict(size=20),
        legend=dict(
            yanchor='top',
            y=1.0,
            xanchor='right',
            x=0.98),
        hoverlabel=dict(
                bgcolor="#E95420",
                font_size=16,
                )
        
    )

    return fig


def get_rent_vs_own(start_date, price, deposit, payment, yrs, int_rate, app_rate,
                    frequency, re_fees, monthly_rent,
                    inv_rate, monthly_main, annual_tax):

    # get the mortgage amortization schedule
    df, end_date = get_amortization(start_date, price, deposit, payment, yrs,
                                    int_rate, app_rate, frequency, re_fees)

    # remove rows after the mortgage amortization is complete
    df = df[df.date <= end_date]

    # add investment columns
    df['invest_start'] = 0
    df['invest_end'] = 0
    df['cross_over_tmp'] = 'r'
    df['cross_over'] = 0

    # convert invest rates and fees to match frequency
    inv = get_georeturn(inv_rate, 'd')

    if frequency == 'm':
        # monthly
        tax = annual_tax / 12
        main = monthly_main
        rent = monthly_rent
    elif frequency == 'b':
        # bi-weekly (24 payments)
        tax = annual_tax / 24
        main = monthly_main / 2
        rent = monthly_rent / 2
    else:
        # accelerated bi-weekly (26 payments)
        tax = annual_tax / 26
        main = monthly_main * 12 / 26
        rent = monthly_rent * 12 / 26

    # calculate the investment returns
    for idx, row in df.iterrows():
        # first period. invest the downpayment + tax + main +
        # mortgage/rent difference

        if idx == 0:
            # first period, invest the downpayment at the daily invest rate
            invest = deposit
            df.at[idx, 'invest_start'] = deposit

            # calc the daily capital gains, roll the balance forward
            cap_gains = invest * (1 + inv)
            df.at[idx, 'invest_end'] = cap_gains
            df.at[idx + 1, 'invest_start'] = cap_gains
        elif df.at[idx, 'payment'] > 0:
            # payment period.  Invest the taxes, maintenence fees, mortgage
            # payment savings
            invest = df.at[idx, 'invest_start'] + tax + main + (payment - rent)
            cap_gains = invest * (1 + inv)
            df.at[idx, 'invest_end'] = cap_gains
            df.at[idx + 1, 'invest_start'] = cap_gains
        elif df.at[idx, 'payment'] == 0:
            # non-payment period, compound investment gains
            cap_gains = df.at[idx, 'invest_start'] * (1 + inv)
            df.at[idx, 'invest_end'] = cap_gains
            df.at[idx + 1, 'invest_start'] = cap_gains

        # find cross-over points
        if df.at[idx, 'invest_end'] > df.at[idx, 'equity']:
            df.at[idx, 'cross_over_tmp'] = 'r'
        else:
            df.at[idx, 'cross_over_tmp'] = 'o'
        # find dates where the equity/rental plots will cross
        if idx > 0:
            if df.at[idx-1, 'cross_over_tmp'] != df.at[idx, 'cross_over_tmp']:
                df.at[idx, 'cross_over'] = 1

    # remove temp column
    df.drop(columns=(['cross_over_tmp']), inplace=True)

    # when the mortgage isn't paid after 25 years)
    df = df[~df.date.isnull()]

    return df


def plot_rent_vs_own(df):
    """
    Plots rent vs own simulation

    Parameters
    ----------
    df : Dataframe
        A dataframe containing mortgage amortization and investment comparision
        Output from get_rent_vs_own

    Returns
    -------
    Plotly figure

    """
    # get cross-over date (if they exist)
    cross_overs = df[df.cross_over == 1]

    # create the plot
    fig = go.Figure()
    
    # get custom data for hover text
    customdata = list(zip(df.invest_end,df.elapsed_yrs))

    # mortgage equity
    fig.add_trace(
        go.Scattergl(
            name='Mortgage Equity',
            x=df.date,
            y=df.equity,
            customdata=customdata,
            line=dict(color='#536872', width=3),
            hovertemplate = """<b>Mortgage Equity:</b> $%{y:,.0f} 
                               <br><b>Investment Equity:</b> $%{customdata[0]:,.0f} 
                               <br><b>Elapsed Years:</b> %{customdata[1]:.2f}
                               <extra></extra>""",
        )
    )

    # rental/investment equity
    fig.add_trace(
        go.Scattergl(
            name='Rent/Investment Equity',
            x=df.date,
            y=df.invest_end,
            line=dict(color='#E95420', width=3),
            hoverinfo='skip',
        )
    )

    # add cross-over annotations if they exist
    if cross_overs.shape[0] >= 1:
        for idx, row in cross_overs.iterrows():
            # get the date/value of cross-over
            cross_over_date = df.at[idx, 'date']
            cross_over_value = df.at[idx, 'equity']

            # calculate the number of years before cross-over
            diff = relativedelta(cross_over_date, df.date.min())
            diff_str = f"{diff.years + diff.months/12:.2f} Years"

            # add the annotation
            fig.add_annotation(
                x=cross_over_date,
                y=cross_over_value,
                text=diff_str,
                showarrow=True,
                arrowhead=1,
                bordercolor="white",
                borderwidth=2,
                borderpad=4,
                bgcolor="#E95420",
                font=dict(size=16, color='#ffffff')
            )

    fig.update_layout(
        title='Rent Vs Buy: Equity Projection',
        template='plotly_white',
        hovermode='x',
        font=dict(size=20),
        yaxis_title='Equity',
        legend=dict(
            yanchor='bottom',
            y=0.10,
            xanchor='right',
            x=0.98,
            ),
        hoverlabel=dict(
            bgcolor="#E95420",
            font_size=16,
            )
    )

    return fig


def save_scenario(df, scenario_name, scenarios=None):
    """
    Save an amortization schedule as a scenario. Used in a store variable

    Parameters
    ----------
    df : dataframe
        dataframe that contains the amortization schedule.Output of
        get_amortization
    scenario_name : string
        Scenario name. Used in plot_amortization
    scenarios : list of dicts, optional
        Saved scenarios.  New scenarios are appended. From the scenario-store
        variable in the dash-app

    Returns
    -------
    TYPE
        DESCRIPTION.

    """

    # save the current scenario
    scen_name = 'scenario-' + scenario_name
    df_new = df[['date', 'end']].copy()
    df_new.columns = ['date', scen_name]
    df_new['date'] = pd.to_datetime(df_new['date']).dt.date
    df_new['date'] = df_new['date'].astype('datetime64')

    # combine with exisitng scenarios
    if scenarios is not None:
        # get stored scenarios as a dataframe
        df_old = pd.DataFrame(scenarios)
        df_old['date'] = pd.to_datetime(df_old['date']).dt.date
        df_old['date'] = df_old['date'].astype('datetime64')

        # join with the new scenario by date
        df_new = df_old.set_index('date').join(df_new.set_index('date'), how='inner')
        df_new.reset_index(inplace=True)
        df_new.rename(columns={'index': 'date'}, inplace=True)
        df_new['date'] = pd.to_datetime(df_new['date']).dt.date
        df_new['date'] = df_new['date'].astype('datetime64')
        
    return df_new.to_dict('records')




