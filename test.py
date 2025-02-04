
import yfinance as yf
from rich import print
import pandas as pd
import numpy as np
import tkinter as tk


# data = yf.Ticker("RELIANCE.NS")



#---------------------- Input data -------------------------------------------------------------------------------------------------------
import tkinter as tk
from tkinter import messagebox

def get_inputs():
    global inp_company_name, inp_revenue_growth, inp_EBIT_margin, inp_Depreciation_as_revenue, inp_NWC_as_revenue, inp_debt_as_revenue, inp_capex_as_revenue, inp_outstanding_shares, inp_WACC, inp_terminal_growth, inp_tax
    
    inp_company_name = entry_company_name.get() if entry_company_name.get() else "RELIANCE.NS"
    
    try:
        inp_revenue_growth = float(entry_revenue_growth.get()) if entry_revenue_growth.get() else 0.0
    except ValueError:
        inp_revenue_growth = 0.0
    
    try:
        inp_EBIT_margin = float(entry_EBIT_margin.get()) if entry_EBIT_margin.get() else 0.0
    except ValueError:
        inp_EBIT_margin = 0.0
    
    try:
        inp_Depreciation_as_revenue = float(entry_Depreciation_as_revenue.get()) if entry_Depreciation_as_revenue.get() else 0.0
    except ValueError:
        inp_Depreciation_as_revenue = 0.0
    
    try:
        inp_NWC_as_revenue = float(entry_NWC_as_revenue.get()) if entry_NWC_as_revenue.get() else 0.0
    except ValueError:
        inp_NWC_as_revenue = 0.0
    
    try:
        inp_debt_as_revenue = float(entry_debt_as_revenue.get()) if entry_debt_as_revenue.get() else 0.0
    except ValueError:
        inp_debt_as_revenue = 0.0
    
    try:
        inp_capex_as_revenue = float(entry_capex_as_revenue.get()) if entry_capex_as_revenue.get() else 0.0
    except ValueError:
        inp_capex_as_revenue = 0.0
    
    try:
        inp_outstanding_shares = float(entry_outstanding_shares.get()) if entry_outstanding_shares.get() else 0.0
    except ValueError:
        inp_outstanding_shares = 0.0
    
    try:
        inp_WACC = float(entry_WACC.get()) if entry_WACC.get() else 0.0
    except ValueError:
        inp_WACC = 0.0
    
    try:
        inp_terminal_growth = float(entry_terminal_growth.get()) if entry_terminal_growth.get() else 0.0
    except ValueError:
        inp_terminal_growth = 0.0
    
    try:
        inp_tax = float(entry_tax.get()) if entry_tax.get() else 0.0
    except ValueError:
        inp_tax = 0.0
    
    messagebox.showinfo("Inputs Received", f"Company Name: {inp_company_name}\nRevenue Growth: {inp_revenue_growth}%\nEBIT Margin: {inp_EBIT_margin}%\nDepreciation as Revenue: {inp_Depreciation_as_revenue}%\nNWC as Revenue: {inp_NWC_as_revenue}%\nDebt as Revenue: {inp_debt_as_revenue}%\nCapex as Revenue: {inp_capex_as_revenue}%\nOutstanding Shares: {inp_outstanding_shares}\nWACC: {inp_WACC}%\nTerminal Growth: {inp_terminal_growth}%\nTax: {inp_tax}%")
    
# Create main window
root = tk.Tk()
root.title("Financial Inputs")
root.geometry("400x550")

# Labels and Entry Widgets
tk.Label(root, text="Company Name:").pack()
entry_company_name = tk.Entry(root)
entry_company_name.pack()

tk.Label(root, text="Revenue Growth (%):").pack()
entry_revenue_growth = tk.Entry(root)
entry_revenue_growth.pack()

tk.Label(root, text="EBIT Margin (%):").pack()
entry_EBIT_margin = tk.Entry(root)
entry_EBIT_margin.pack()

tk.Label(root, text="Depreciation as Revenue (%):").pack()
entry_Depreciation_as_revenue = tk.Entry(root)
entry_Depreciation_as_revenue.pack()

tk.Label(root, text="NWC as Revenue (%):").pack()
entry_NWC_as_revenue = tk.Entry(root)
entry_NWC_as_revenue.pack()

tk.Label(root, text="Debt as Revenue (%):").pack()
entry_debt_as_revenue = tk.Entry(root)
entry_debt_as_revenue.pack()

tk.Label(root, text="Capex as Revenue (%):").pack()
entry_capex_as_revenue = tk.Entry(root)
entry_capex_as_revenue.pack()

tk.Label(root, text="Outstanding Shares:").pack()
entry_outstanding_shares = tk.Entry(root)
entry_outstanding_shares.pack()

tk.Label(root, text="WACC (%):").pack()
entry_WACC = tk.Entry(root)
entry_WACC.pack()

tk.Label(root, text="Terminal Growth (%):").pack()
entry_terminal_growth = tk.Entry(root)
entry_terminal_growth.pack()

tk.Label(root, text="Tax (%):").pack()
entry_tax = tk.Entry(root)
entry_tax.pack()

# Submit Button
submit_button = tk.Button(root, text="Submit", command=get_inputs)
submit_button.pack()

# Run the Tkinter event loop
root.mainloop()

#----------------------Company name -------------------
# data = yf.Ticker("RELIANCE.NS")
data = yf.Ticker(inp_company_name)

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
revenue_2021 =float(income_statement.query('Year == 2021')['Total Revenue'].dropna().iloc[0])
revenue_2022 =float(income_statement.query('Year == 2022')['Total Revenue'].dropna().iloc[0])
revenue_2023 =float(income_statement.query('Year == 2023')['Total Revenue'].dropna().iloc[0])
revenue_2024 =float(income_statement.query('Year == 2024')['Total Revenue'].dropna().iloc[0])

revenue = [
    float(income_statement.query('Year == 2021')['Total Revenue'].dropna().iloc[0]),
    float(income_statement.query('Year == 2022')['Total Revenue'].dropna().iloc[0]),
    float(income_statement.query('Year == 2023')['Total Revenue'].dropna().iloc[0]),
    float(income_statement.query('Year == 2024')['Total Revenue'].dropna().iloc[0])
]

revpercent1 = (revenue_2022/revenue_2021 -1)
revpercent2 = (revenue_2023/revenue_2022 -1)
revpercent3 = (revenue_2024/revenue_2023 -1)
revenue_growth = (revpercent1+revpercent2+revpercent3)/3


if inp_revenue_growth != 0:
    revenue_growth = inp_revenue_growth/100
else: 
    revenue_growth = revenue_growth 

# print(revenue_growth)

# revenue_2024 = revenue_2024*(1+revenue_growth)
# revenue_2025 = revenue_2024*(1+revenue_growth)
# revenue_2026 = revenue_2025*(1+revenue_growth)
# revenue_2027 = revenue_2026*(1+revenue_growth)
# revenue_2028 = revenue_2027*(1+revenue_growth)

# revenue = [
#     float(income_statement.query('Year == 2021')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2022')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2023')['Total Revenue'].dropna()),
#     float(income_statement.query('Year == 2024')['Total Revenue'].dropna())
# ]

# # Project future revenue using revenue growth rate
# for _ in range(5): 
#     revenue.append(revenue[-1] * (1 + revenue_growth))

# print(revenue_2028)

revenue = {
    2021: float(income_statement.query('Year == 2021')['Total Revenue'].dropna().iloc[0]),
    2022: float(income_statement.query('Year == 2022')['Total Revenue'].dropna().iloc[0]),
    2023: float(income_statement.query('Year == 2023')['Total Revenue'].dropna().iloc[0]),
    2024: float(income_statement.query('Year == 2024')['Total Revenue'].dropna().iloc[0])
}

# Project future revenue using revenue growth rate
for year in range(2025, 2030):
    revenue[year] = revenue[year - 1] * (1 + revenue_growth)

# print(revenue)

#------------------------ EBIT Forecasting --------------------------------------------------------

EBIT_2021 =float(income_statement.query('Year == 2021')['EBIT'].dropna().iloc[0])
EBIT_2022 =float(income_statement.query('Year == 2022')['EBIT'].dropna().iloc[0])
EBIT_2023 =float(income_statement.query('Year == 2023')['EBIT'].dropna().iloc[0])
EBIT_2024 =float(income_statement.query('Year == 2024')['EBIT'].dropna().iloc[0])

EBITpercent1 = EBIT_2021/revenue_2021
EBITpercent2 = EBIT_2022/revenue_2022
EBITpercent3 = EBIT_2023/revenue_2023
EBITpercent4 = EBIT_2024/revenue_2024

EBITpercent = (EBITpercent1+EBITpercent2+EBITpercent3+EBITpercent4)/4

if inp_EBIT_margin != 0:
    EBITpercent = inp_EBIT_margin/100
else: 
    EBITpercent = EBITpercent 

EBIT = {
    2021: float(income_statement.query('Year == 2021')['EBIT'].dropna().iloc[0]),
    2022: float(income_statement.query('Year == 2022')['EBIT'].dropna().iloc[0]),
    2023: float(income_statement.query('Year == 2023')['EBIT'].dropna().iloc[0]),
    2024: float(income_statement.query('Year == 2024')['EBIT'].dropna().iloc[0])
}

# Project future EBIT using EBITpercent

for year in range(2025, 2030):
    EBIT[year] = revenue[year] * EBITpercent


# print(revenue)
# print(EBIT)

#------------------------------Deducting tax-------------------------

if inp_tax != 0:
    taxpercent = inp_tax/100
else: 
    taxpercent = 0.18 

# Project future NOPAT using Tax percent

NOPAT = {
    
}

for year in range(2021, 2030):
    NOPAT[year] = EBIT[year] * (1-taxpercent)







# print(income_statement)
# EBIT_2024 = float(income_statement.query('Year == 2024')['EBIT'].dropna())
# print(EBIT_2024)

# revenue20 = float(income_statement.query('Year == 2024')['EBIT'].dropna())

#--------------------- revenue input ---------------------
# net_debt = float(cash_flow.query('Year == 2024')['Repayment of Debt'].dropna())
# print(net_debt)


