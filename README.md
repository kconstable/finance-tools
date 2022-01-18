# Finance-tools
A collection of tools used for finance.  This is a work in progress.  A deployment of the current tools can be viewed here.

## Mortgage Amortization Calculator
This calculator simulates mortgage amortization schedules based on the input parameters. Interest is calculated daily and compounded between payment periods. You can add pre-payments and compare schedules by saving scenarios. The current tool supports monthly, bi-weekly(24 payments per year), or accelerated (26 payments per year) payment frequencies

![image](https://user-images.githubusercontent.com/1649676/149950357-2ceaf9ce-7076-4c8a-9a0e-cd555ab61f65.png)


## Rent vs Buy Calculator
This plot compares purchasing a home vs renting. Owning a home requires additional costs which could be invested in the stock market instead of purchasing real estate.  Generally, you must hold real estate for a number of years to make a profit and cover the transaction costs.  In the example below, owning provides more equity than investing after 1.33 years, but the situation reverses after ~19 years based on the input assumptions.

**Mortgage Equity**  
Mortgage equity is calculated as the difference in the home value (compounded at the annual appreciation rate), less the outstanding mortgage and real estate fees after selling. This calculator assumes only real estate fees are incurred on selling (no capital gains or additional land transfer taxes etc)

**Investment Equity**  
The following items are invested in the stock market and compounded at the annual investment rate;  
+ The downpayment that would be used for a mortgage
+ Maintenance/HOA fees (monthly) 
+ Taxes (monthly)
+ The difference in Mortgage Payments vs Rent (if your rent is lower than your mortgage payment)

![image](https://user-images.githubusercontent.com/1649676/149949740-54837077-b716-40e4-9f83-e07fe6a999c0.png)
