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
ANNUAL_INVEST_RATE = 6.0
MONTHLY_FEES = 800
ANNUAL_TAX = 5500
MONTHLY_RENT = 2500


def get_periods(start_date, yrs=25, frequency='m'):
    """
    Returns a list of dates from start-date to the number of years(yrs) by
    the frequency of payment (frequency, monthly or bi-monthly)

    Parameters
    ----------
    start_date : date (yyyy-mm-dd)
        Start date for amortization schedule
    yrs : Int
        Number of years in the amortization schedule
    frequency : string
        frequency of payments. m=monthly, b=bi-monthly

    Returns
    -------
    List of dates

    """

    # get end date
    end_date = start_date + timedelta(days=yrs*365)

    # create the list of date ranges
    if frequency == 'm':
        # monthly
        rng = pd.date_range(start_date, end=end_date, freq='M')
    elif frequency == 'b':
        # biweekly
        rng = pd.date_range(start=start_date, end=end_date, freq='SM')

    return rng


def get_georeturn(rate, frequency):
    """
    Converts annual rate of return to monthly or bi-weekly

    Parameters
    ----------
    rate : float
        Annual rate of return (5.0)==5.0%
    frequency : string
        Frequency to convert to: m=montthly, b=bi-weekly

    Returns
    -------
    float

    """
    r = rate / 100

    if frequency == 'm':
        return (1 + r) ** (1 / 12) - 1
    elif frequency == 'b':
        return (1 + r) ** (1 / 24) - 1
    else:
        print('frequency not recongized')


def get_amortization(start_date, price, deposit, payment, yrs, int_rate, app_rate,
                     frequency, re_fees, prepayments=None):
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
    Returns
    -------
    A dataframe with the amortization schedule

    """

    # convert rates, calc mortgage, get date range
    ir = get_georeturn(int_rate, frequency)
    app = get_georeturn(app_rate, frequency)
    fees = re_fees / 100
    mortgage = price - deposit
    date_rng = get_periods(start_date, yrs, frequency)

    # init the dataframe
    df = pd.DataFrame(date_rng, columns=['date'])
    df['frequency'] = frequency
    df['start'] = 0.0
    df['payment'] = 0.0
    df['prepayment'] = 0.0
    df['interest'] = 0.0
    df['end'] = 0.0
    df['value'] = 0.0
    df['equity'] = 0.0

    # add prepayments
    if prepayments is not None:
        for prepayment in prepayments:
            # get the date as string
            str_date = prepayment['date']

            # parse the month/year
            pay_date = datetime.strptime(str_date, '%Y-%m-%d').date()
            pay_mth = pay_date.month
            pay_yr = pay_date.year
            pay_day = calendar.monthrange(pay_yr, pay_mth)[1]
            dt = str(date(pay_yr, pay_mth, pay_day))

            # get the index value for that date
            idx = df[df.date == dt].index.values.astype(int)[0]

            # add the pre-payment at the month-end date
            df.at[idx, 'prepayment'] = prepayment['value']

    # create the amortization schedule
    for idx, row in df.iterrows():

        # first payment
        if idx == 0:
            df.at[0, 'start'] = mortgage
            end_date = start_date
            value = price

        # calc interest
        int_pay = (df.at[idx, 'start'] - payment - df.at[idx, 'prepayment']) * ir

        # calc end balance
        end = df.at[idx, 'start'] + int_pay - payment - df.at[idx, 'prepayment']

        # calc appreciation
        value = value * (1 + app)

        # update amortization schedule
        if end > 0:
            # update schedule
            df.at[idx, 'payment'] = payment
            df.at[idx, 'interest'] = int_pay
            df.at[idx, 'end'] = end
            df.at[idx, 'value'] = value
            df.at[idx, 'equity'] = (value - end) - (value * fees)
            df.at[idx + 1, 'start'] = end
            end_date = df.at[idx, 'date']
        else:
            # mortgage paid off
            df.at[idx, 'payment'] = df.at[idx, 'start']
            df.at[idx, 'interest'] = 0
            df.at[idx, 'end'] = 0
            df.at[idx, 'value'] = value
            df.at[idx, 'equity'] = (value - end) - (value * fees)
            end_date = df.at[idx, 'date']
            break

    # return the dataframe, exclcude nan rows (happens
    # when the mortgage isn't paid after 25 years)
    df = df[~df.date.isnull()]
    return df, end_date



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

    # get the frequency of payments
    freq = df.frequency.unique()

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

    # get the annotation data based on yrs
    d = {}
    for y in yrs:
        if freq == 'm':
            p = y * 12
            try:
                d[y] = {'date': df.at[p, 'date'], 'mtg': df.at[p, 'end'],
                        'name': f'{y} Years'}
            except:
                continue
        else:
            p = y * 24
            try:
                d[y] = {'date': df.at[p, 'date'], 'mtg': df.at[p, 'end'],
                        'name': f'{y} Years'}
            except:
                continue

    # create plots
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name='Mortgage',
            x=df.date,
            y=df.end,
            line=dict(color='#536872'),
            fill='tozeroy',
            hovertemplate=None
        )
    )
    fig.add_trace(
        go.Bar(
            name='Interest',
            x=df.date,
            y=df.cum_interest,
            marker_line_color='orange',
            hovertemplate=None
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

    # add yearly annotation
    for k, v in d.items():
        fig.add_annotation(
            x=v['date'],
            y=v['mtg'],
            text=v['name'],
            showarrow=True,
            arrowhead=1,
            bordercolor="#536872",
            borderwidth=2,
            borderpad=4,
            bgcolor="#ff7f0e"
        )

    fig.update_layout(
        title='Mortgage Amortization',
        template='plotly_white',
        width=800,
        height=500,
        hovermode="x unified",
        font=dict(size=20),
        legend=dict(
            yanchor='top',
            y=1.0,
            xanchor='right',
            x=0.98,
        )
    )

    return fig


def get_rent_vs_own(start_date, price, deposit, payment, yrs, int_rate, app_rate,
                    frequency, re_fees, monthly_rent,
                    inv_rate, monthly_main, annual_tax):
    
    # get the mortgage amortization schedule
    df, end_date = get_amortization(start_date, price, deposit, payment, yrs, int_rate,
                                    app_rate, frequency, re_fees)

    # remove rows after the mortgage amortization is complete
    df = df[df.date <= end_date]

    # add investment columns
    df['invest_start'] = 0
    df['invest_end'] = 0
    df['cross_over'] = 0

    # convert invest rates and fees to match frequency
    inv = get_georeturn(inv_rate, frequency)
    if frequency == 'm':
        # monthly
        tax = annual_tax / 12
        main = monthly_main
        rent = monthly_rent
    else:
        # bi-weekly
        tax = annual_tax / 24
        main = monthly_main / 2
        rent = monthly_rent / 2

    # calculate the investment returns
    cross_over = True
    for idx, row in df.iterrows():
        # first period. invest the downpayment + tax + main +
        # mortgage/rent difference
        if idx == 0:
            invest = deposit + tax + main + (payment - rent)
            df.at[idx, 'invest_start'] = invest
            df.at[idx, 'invest_end'] = invest * (1 + inv)
            df.at[idx + 1, 'invest_start'] = invest * (1 + inv)
        else:
            # subsequent periods
            invest = df.at[idx, 'invest_start'] + tax + main + (payment - rent)
            df.at[idx, 'invest_end'] = invest * (1 + inv)
            df.at[idx + 1, 'invest_start'] = invest * (1 + inv)
        # if df.at[idx, 'equity'] > df.at[idx, 'invest_end']:
        if cross_over is True and df.at[idx, 'equity'] > df.at[idx, 'invest_end']:
            cross_over = False
            df.at[idx, 'cross_over'] = 1
            
    # when the mortgage isn't paid after 25 years)
    df = df[~df.date.isnull()]

    return df


def plot_rent_vs_own(df):
    """


    Parameters
    ----------
    df : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    # get cross-over date (if it exists)
    try:
        cross_over_idx = df[df.cross_over == 1].index.item()
        cross_over_date = df.at[cross_over_idx, 'date']
        cross_over_value = df.at[cross_over_idx, 'equity']

        # calculate the number of years before cross-over
        diff = relativedelta(cross_over_date, df.date.min())
        diff_str = f"{diff.years} Year(s)|{diff.months} Month(s)"
    except:
        cross_over_idx = None

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            name='Equity-Own',
            x=df.date,
            y=df.equity,
            line=dict(color='#536872', width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            name='Equity-Rent',
            x=df.date,
            y=df.invest_end,
            line=dict(color='orange', width=3)
        )
    )

    if cross_over_idx is not None:
        fig.add_annotation(
            x=cross_over_date,
            y=cross_over_value,
            text=diff_str,
            showarrow=True,
            arrowhead=1,
            bordercolor="#536872",
            borderwidth=2,
            borderpad=4,
            bgcolor="#ff7f0e",
            font=dict(size=16)
        )

    fig.update_layout(
        title='Rent Vs Buy: Equity Projection',
        template='plotly_white',
        width=800,
        height=450,
        hovermode="x unified",
        font=dict(size=20),
        yaxis_title='Equity',
        legend=dict(
            yanchor='bottom',
            y=0.10,
            xanchor='right',
            x=0.98,
            )
    )

    # fig.show()
    return fig


# df, end_date = get_amortization(START_DATE, PRICE, DEPOSIT, PAY, YRS, IR, APP_RATE,
# 'm',RE_FEES,PRE_PAYMENTS)
# df = get_rent_vs_own(START_DATE, PRICE, DEPOSIT, PAY, YRS, IR, APP_RATE, 'm',
#                       RE_FEES, MONTHLY_RENT, ANNUAL_INVEST_RATE,
#                       MONTHLY_FEES, ANNUAL_TAX)
# plot_rent_vs_own(df)
# fig = plot_amortization(df,end_date, [5,10,20])
# fig.show()
