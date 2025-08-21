# 💹 Valuation Dashboard — DCF, Sensitivity & Football Field

A Streamlit app that pulls financials from Yahoo Finance (via `yfinance`) and builds a quick, defensible valuation view for any listed company—complete with a DCF model, WACC × Terminal Growth sensitivity heatmap, one-way sensitivities, and a football-field chart using DCF, EV/EBITDA, and P/E ranges.

> Default example ticker: `RELIANCE.NS` (NSE India). Works with most Yahoo tickers (e.g., `AAPL`, `TSLA`, `INFY.NS`).

---

## ✨ Features

- 📊 Auto-fetch income statement, balance sheet, cash flow with caching  
- 🔮 Revenue history & forecast (constant growth baseline)  
- 💰 Discounted Cash Flow (FCFF + Terminal Value, Gordon Growth)  
- 🧪 Sensitivity analysis
  - 2D heatmap: Per-share value across WACC × Terminal Growth  
  - 1D “tornado” style: Revenue Growth and EBIT Margin  
- 🏟️ Football field valuation ranges (DCF, EV/EBITDA, P/E)  
- ⚙️ Override levers: shares, margins, WACC, TG, Capex/Dep/NWC, multiples  

---

## 📦 Tech Stack

- [Python 3.9+](https://www.python.org/)  
- [Streamlit](https://streamlit.io/) for UI  
- [yfinance](https://pypi.org/project/yfinance/) for data  
- [pandas](https://pandas.pydata.org/) / [numpy](https://numpy.org/) for computation  
- [plotly](https://plotly.com/python/) for charts  

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
