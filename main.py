import yfinance as yf
from rich import print
import pandas as pd
import numpy as np

data = yf.Ticker("RS")

#----------------------Data Import --------------------------

income_statement = data.financials.transpose()
income_statement.index = pd.to_datetime(income_statement.index)
income_statement = income_statement.infer_objects()
income_statement['Year'] = income_statement.index.year

Balance_sheet = data.balance_sheet.transpose()
Balance_sheet.index = pd.to_datetime(Balance_sheet.index)
Balance_sheet = Balance_sheet.infer_objects()
Balance_sheet['Year'] = Balance_sheet.index.year

cash_flow = data.cash_flow.transpose()
cash_flow.index = pd.to_datetime(cash_flow.index)
cash_flow = cash_flow.infer_objects()
cash_flow['Year'] = cash_flow.index.year

#--------------------------- DCF Calculation ----------------------------------------
#-------revenue forecasting -------------
revenue_2020 =float(income_statement.query('Year == 2020')['Total Revenue'].dropna())
revenue_2021 =float(income_statement.query('Year == 2021')['Total Revenue'].dropna())
revenue_2022 =float(income_statement.query('Year == 2022')['Total Revenue'].dropna())
revenue_2023 =float(income_statement.query('Year == 2023')['Total Revenue'].dropna())

revenue = [
    float(income_statement.query('Year == 2020')['Total Revenue'].dropna()),
    float(income_statement.query('Year == 2021')['Total Revenue'].dropna()),
    float(income_statement.query('Year == 2022')['Total Revenue'].dropna()),
    float(income_statement.query('Year == 2023')['Total Revenue'].dropna())
]

revpercent1 = (revenue_2021/revenue_2020 -1)
revpercent2 = (revenue_2022/revenue_2021 -1)
revpercent3 = (revenue_2023/revenue_2022 -1)
revenue_growth = (revpercent1+revpercent2+revpercent3)/3

# revenue_2024 = revenue_2023*(1+revenue_growth)
# revenue_2025 = revenue_2024*(1+revenue_growth)
# revenue_2026 = revenue_2025*(1+revenue_growth)
# revenue_2027 = revenue_2026*(1+revenue_growth)
# revenue_2028 = revenue_2027*(1+revenue_growth)

# revenue = [
#     float(income_statement.query('Year == 2020')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2021')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2022')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2023')['Total Revenue'].dropna())
# ]

# # Project future revenue using revenue growth rate
# for _ in range(5):  
#     revenue.append(revenue[-1] * (1 + revenue_growth))

# print(revenue_2028)

revenue = {
    2020: float(income_statement.query('Year == 2020')['Total Revenue'].dropna()),
    2021: float(income_statement.query('Year == 2021')['Total Revenue'].dropna()),
    2022: float(income_statement.query('Year == 2022')['Total Revenue'].dropna()),
    2023: float(income_statement.query('Year == 2023')['Total Revenue'].dropna())
}

# Project future revenue using revenue growth rate
for year in range(2024, 2029):
    revenue[year] = revenue[year - 1] * (1 + revenue_growth)

print(revenue)






# print(income_statement)
# ebitda_2023 = float(income_statement.query('Year == 2023')['EBITDA'].dropna())
# print(ebitda_2023)

# revenue20 = float(income_statement.query('Year == 2023')['EBITDA'].dropna())

#--------------------- revenue input ---------------------
# net_debt = float(cash_flow.query('Year == 2023')['Repayment of Debt'].dropna())
# print(net_debt)

