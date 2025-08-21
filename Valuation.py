import math
import time
from dataclasses import dataclass
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf


# ------------------------------- Helpers -------------------------------

@dataclass
class FinancialData:
    income: pd.DataFrame
    balance: pd.DataFrame
    cashflow: pd.DataFrame
    info: dict


@st.cache_data(show_spinner=False, ttl=60 * 15)
def fetch_financials(ticker: str) -> FinancialData:
    t = yf.Ticker(ticker)
    # Yahoo data comes with columns as line items and rows as dates; we transpose to make years rows
    inc = t.financials.transpose() if t.financials is not None else pd.DataFrame()
    bal = t.balance_sheet.transpose() if t.balance_sheet is not None else pd.DataFrame()
    cf = t.cash_flow.transpose() if t.cash_flow is not None else pd.DataFrame()

    for df in (inc, bal, cf):
        if not df.empty:
            df.index = pd.to_datetime(df.index).year
            df.sort_index(inplace=True)

    return FinancialData(inc, bal, cf, t.info or {})


def get_first_available(df: pd.DataFrame, candidates: List[str]):
    for c in candidates:
        if c in df.columns:
            return c
    return None


def safe_series(df: pd.DataFrame, col: str) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=float)
    s = pd.to_numeric(df[col], errors="coerce")
    s.index = df.index
    return s.dropna()


def growth_rates(series: pd.Series) -> pd.Series:
    # simple YoY growth
    ser = series.sort_index()
    return (ser / ser.shift(1) - 1.0).dropna()


def compute_cagr(first: float, last: float, years: int) -> float:
    if first <= 0 or years <= 0:
        return np.nan
    return (last / first) ** (1 / years) - 1


def discount_factor(rate: float, t: int) -> float:
    return 1.0 / ((1.0 + rate) ** t)


def fmt_pct(x: float) -> str:
    if pd.isna(x): return "—"
    return f"{x*100:.1f}%"


def fmt_num(x: float) -> str:
    if pd.isna(x): return "—"
    # scale to Cr/₹ etc. Keep as raw number with commas for simplicity
    return f"{x:,.0f}"


# ------------------------------- Streamlit UI -------------------------------

st.set_page_config(page_title="Valuation Dashboard (DCF • Sensitivity • Football Field)", layout="wide")

st.title("💹 Valuation Dashboard — DCF, Sensitivity & Football Field")

with st.sidebar:
    st.subheader("Inputs")
    ticker = st.text_input("Ticker (Yahoo Finance)", value="RELIANCE.NS").strip()

    horizon = st.number_input("Projection Horizon (years)", 3, 15, 5, 1)
    base_rev_growth_pct = st.number_input("Base Revenue Growth % (per year)", -50.0, 100.0, 10.0, 0.5)
    ebit_margin_pct = st.number_input("EBIT Margin %", -50.0, 80.0, 15.0, 0.5)
    tax_rate_pct = st.number_input("Tax Rate %", 0.0, 60.0, 25.0, 0.5)

    dep_as_rev_pct = st.number_input("Depreciation as % of Revenue", 0.0, 40.0, 6.0, 0.5)
    capex_as_rev_pct = st.number_input("Capex as % of Revenue", 0.0, 60.0, 8.0, 0.5)
    nwc_as_rev_pct = st.number_input("Net Working Capital as % of Revenue", -50.0, 100.0, 10.0, 0.5)

    wacc_pct = st.number_input("WACC %", 1.0, 60.0, 12.0, 0.5)
    terminal_growth_pct = st.number_input("Terminal Growth %", -5.0, 8.0, 3.0, 0.25)

    shares_override = st.text_input("Shares Outstanding (optional, numeric)")
    shares_override_val = pd.to_numeric(shares_override, errors="coerce")

    st.divider()
    st.caption("Football Field Multiples (user assumptions)")
    ev_ebitda_low = st.number_input("EV/EBITDA (low)", 2.0, 30.0, 10.0, 0.5)
    ev_ebitda_high = st.number_input("EV/EBITDA (high)", 2.0, 50.0, 16.0, 0.5)
    pe_low = st.number_input("P/E (low)", 2.0, 80.0, 18.0, 0.5)
    pe_high = st.number_input("P/E (high)", 2.0, 100.0, 28.0, 0.5)

    st.divider()
    st.caption("Sensitivity grid ranges")
    wacc_min = st.number_input("WACC min %", 2.0, 50.0, 8.0, 0.5)
    wacc_max = st.number_input("WACC max %", 3.0, 80.0, 16.0, 0.5)
    wacc_step = st.number_input("WACC step %", 0.25, 10.0, 1.0, 0.25)

    tg_min = st.number_input("Terminal growth min %", -3.0, 7.0, 1.0, 0.25)
    tg_max = st.number_input("Terminal growth max %", -2.0, 8.0, 5.0, 0.25)
    tg_step = st.number_input("Terminal growth step %", 0.25, 3.0, 0.5, 0.25)

    st.divider()
    run_btn = st.button("Run / Refresh", type="primary")

if run_btn or True:
    with st.spinner("Fetching data..."):
        data = fetch_financials(ticker)

    if data.income.empty:
        st.error("Could not fetch income statement for this ticker. Try a different one.")
        st.stop()

    # Identify columns
    rev_col = get_first_available(data.income, ["Total Revenue", "Operating Revenue", "Revenue"])
    ebit_col = get_first_available(data.income, ["EBIT", "Operating Income", "Ebit"])
    ebitda_col = get_first_available(data.income, ["EBITDA", "Ebitda"])
    net_income_col = get_first_available(data.income, ["Net Income", "Net Income Common Stockholders"])

    revenue_hist = safe_series(data.income, rev_col)
    ebit_hist = safe_series(data.income, ebit_col)
    ebitda_hist = safe_series(data.income, ebitda_col)
    net_income_hist = safe_series(data.income, net_income_col)

    # Try shares outstanding, cash, debt from balance sheet + info
    shares_info = data.info.get("sharesOutstanding", np.nan)
    shares = shares_override_val if pd.notna(shares_override_val) else shares_info

    cash_col = get_first_available(data.balance, [
        "Cash Cash Equivalents And Short Term Investments",
        "Cash And Cash Equivalents",
        "Cash And Short Term Investments"
    ])
    debt_col = get_first_available(data.balance, ["Total Debt", "Short Long Term Debt Total", "Total Liab"])  # fallback

    cash_hist = safe_series(data.balance, cash_col)
    debt_hist = safe_series(data.balance, debt_col)

    cash = cash_hist.sort_index().iloc[-1] if not cash_hist.empty else np.nan
    debt = debt_hist.sort_index().iloc[-1] if not debt_hist.empty else np.nan

    # -------------------- Revenue Forecasting --------------------
    st.subheader("📈 Revenue — History & Forecast")

    if revenue_hist.empty or len(revenue_hist) < 2:
        st.warning("Not enough historical revenue to compute growth. Showing raw values.")
    rev_df = revenue_hist.to_frame("Revenue")
    rev_df.index.name = "Year"

    # derive growth
    yoy = growth_rates(revenue_hist)
    cagr = compute_cagr(revenue_hist.iloc[0], revenue_hist.iloc[-1], len(revenue_hist) - 1) if len(revenue_hist) >= 2 else np.nan
    avg_yoy = yoy.mean() if not yoy.empty else np.nan

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Avg YoY Growth", fmt_pct(avg_yoy))
    col_b.metric("CAGR", fmt_pct(cagr))
    col_c.metric("Latest Revenue", fmt_num(revenue_hist.iloc[-1]) if not revenue_hist.empty else "—")

    # Forecast using base growth
    base_g = base_rev_growth_pct / 100.0
    last_year = int(revenue_hist.index.max()) if not revenue_hist.empty else 2024
    forecast_years = [last_year + i for i in range(1, horizon + 1)]

    revenue_forecast = {}
    last_rev = revenue_hist.iloc[-1] if not revenue_hist.empty else 1e9
    for i, y in enumerate(forecast_years, start=1):
        last_rev = last_rev * (1 + base_g)
        revenue_forecast[y] = last_rev

    rev_plot_df = pd.concat([
        rev_df,
        pd.DataFrame({"Revenue": pd.Series(revenue_forecast)})
    ])
    rev_plot_df["Type"] = np.where(rev_plot_df.index <= last_year, "Historical", "Forecast")

    fig_rev = px.bar(
        rev_plot_df.reset_index(),
        x="index", y="Revenue", color="Type",
        title=f"Revenue (Historical & Forecast) — {ticker}",
        labels={"index": "Year", "Revenue": "₹"}
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    st.caption("Forecast method: constant annual growth based on the sidebar input.")

    # -------------------- DCF Core --------------------
    st.subheader("💰 DCF — Assumptions & Valuation")

    ebit_margin = ebit_margin_pct / 100.0
    tax_rate = tax_rate_pct / 100.0
    dep_pct = dep_as_rev_pct / 100.0
    capex_pct = capex_as_rev_pct / 100.0
    nwc_pct = nwc_as_rev_pct / 100.0
    wacc = wacc_pct / 100.0
    tg = terminal_growth_pct / 100.0

    # Build forward table
    # Working capital modeled as % of revenue; ΔNWC ~ % * ΔRevenue
    proj_rows = []
    base_prev_rev = revenue_hist.iloc[-1] if not revenue_hist.empty else revenue_forecast[forecast_years[0]] / (1 + base_g)
    for i, y in enumerate(forecast_years, start=1):
        rev_y = revenue_forecast[y]
        ebit_y = rev_y * ebit_margin
        nopat_y = ebit_y * (1 - tax_rate)
        dep_y = rev_y * dep_pct
        capex_y = rev_y * capex_pct
        d_nwc_y = (rev_y - base_prev_rev) * nwc_pct  # incremental tied-up capital
        fcff_y = nopat_y + dep_y - capex_y - d_nwc_y
        proj_rows.append([y, rev_y, ebit_y, nopat_y, dep_y, capex_y, d_nwc_y, fcff_y])
        base_prev_rev = rev_y

    proj = pd.DataFrame(proj_rows, columns=["Year", "Revenue", "EBIT", "NOPAT", "Dep", "Capex", "ΔNWC", "FCFF"])
    proj["t"] = np.arange(1, len(proj) + 1)
    proj["DF"] = (1 + wacc) ** (-proj["t"])
    proj["PV_FCFF"] = proj["FCFF"] * proj["DF"]

    tv = proj["FCFF"].iloc[-1] * (1 + tg) / (wacc - tg) if wacc > tg else np.nan
    pv_tv = tv * ((1 + wacc) ** (-proj["t"].iloc[-1])) if pd.notna(tv) else np.nan

    ev = proj["PV_FCFF"].sum() + (pv_tv if pd.notna(pv_tv) else 0.0)

    # Equity bridge
    # Fall back if not found; users can override shares
    if pd.isna(shares):
        # last known from balance sheet (not ideal, but keep flow)
        shares = data.info.get("floatShares", np.nan)

    equity_value = ev + (cash if pd.notna(cash) else 0.0) - (debt if pd.notna(debt) else 0.0)
    per_share = equity_value / shares if (pd.notna(shares) and shares > 0) else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Enterprise Value (DCF, ₹)", fmt_num(ev))
    k2.metric("Equity Value (₹)", fmt_num(equity_value))
    k3.metric("Per-share Value (₹)", "—" if pd.isna(per_share) else f"{per_share:,.2f}")
    k4.metric("Terminal Value PV (₹)", "—" if pd.isna(pv_tv) else fmt_num(pv_tv))

    with st.expander("Projected FCFF detail"):
        st.dataframe(
            proj.set_index("Year")[["Revenue", "EBIT", "NOPAT", "Dep", "Capex", "ΔNWC", "FCFF", "PV_FCFF"]],
            use_container_width=True
        )

    fig_fcff = px.bar(proj, x="Year", y="FCFF", title="Projected FCFF")
    st.plotly_chart(fig_fcff, use_container_width=True)

    # -------------------- Sensitivity (WACC × Terminal Growth) --------------------
    st.subheader("🧪 DCF Sensitivity — WACC vs Terminal Growth")

    wacc_grid = np.arange(wacc_min / 100.0, wacc_max / 100.0 + 1e-9, wacc_step / 100.0)
    tg_grid = np.arange(tg_min / 100.0, tg_max / 100.0 + 1e-9, tg_step / 100.0)

    def dcf_value_for(w: float, g: float) -> Tuple[float, float]:
        if w <= g:  # invalid in Gordon growth
            return (np.nan, np.nan)
        df = proj.copy()
        df["DF"] = (1 + w) ** (-df["t"])
        df["PV_FCFF"] = df["FCFF"] * df["DF"]
        tv_ = df["FCFF"].iloc[-1] * (1 + g) / (w - g)
        pv_tv_ = tv_ * ((1 + w) ** (-df["t"].iloc[-1]))
        ev_ = df["PV_FCFF"].sum() + pv_tv_
        eq_ = ev_ + (cash if pd.notna(cash) else 0.0) - (debt if pd.notna(debt) else 0.0)
        ps_ = eq_ / shares if (pd.notna(shares) and shares > 0) else np.nan
        return ev_, ps_

    heat = []
    for g in tg_grid:
        row = []
        for w in wacc_grid:
            _, ps = dcf_value_for(w, g)
            row.append(ps)
        heat.append(row)

    heat_df = pd.DataFrame(heat, index=[f"{x*100:.1f}%" for x in tg_grid], columns=[f"{x*100:.1f}%" for x in wacc_grid])
    fig_heat = px.imshow(
        heat_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="Per-share Value (₹) — Sensitivity to WACC & Terminal Growth"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Quick 1D sensitivities (tornado-style inputs)
    st.subheader("🎯 One-way Sensitivities (Revenue Growth & EBIT Margin)")

    rg_range = np.linspace(max(-0.5, base_g - 0.1), base_g + 0.1, 9)  # ±10% around base growth
    em_range = np.linspace(max(-0.2, ebit_margin - 0.05), min(0.7, ebit_margin + 0.05), 9)

    def per_share_given(base_g_, ebit_margin_) -> float:
        # rebuild FCFF quickly under new assumptions (faster than full recompute)
        base_prev_rev = revenue_hist.iloc[-1] if not revenue_hist.empty else list(revenue_forecast.values())[0] / (1 + base_g)
        tmp = []
        last = revenue_hist.iloc[-1] if not revenue_hist.empty else list(revenue_forecast.values())[0] / (1 + base_g)
        for y in forecast_years:
            last = last * (1 + base_g_)
            rev_y = last
            ebit_y = rev_y * ebit_margin_
            nopat_y = ebit_y * (1 - tax_rate)
            dep_y = rev_y * dep_pct
            capex_y = rev_y * capex_pct
            d_nwc_y = (rev_y - base_prev_rev) * nwc_pct
            fcff_y = nopat_y + dep_y - capex_y - d_nwc_y
            tmp.append(fcff_y)
            base_prev_rev = rev_y
        tmp = np.array(tmp)
        tvec = np.arange(1, len(tmp) + 1)
        pv = (tmp / ((1 + wacc) ** tvec)).sum()
        tv_ = tmp[-1] * (1 + tg) / (wacc - tg) if wacc > tg else np.nan
        pv_tv_ = tv_ / ((1 + wacc) ** tvec[-1]) if pd.notna(tv_) else 0.0
        ev_ = pv + pv_tv_
        eq_ = ev_ + (cash if pd.notna(cash) else 0.0) - (debt if pd.notna(debt) else 0.0)
        return eq_ / shares if (pd.notna(shares) and shares > 0) else np.nan

    rg_ps = [per_share_given(g, ebit_margin) for g in rg_range]
    em_ps = [per_share_given(base_g, m) for m in em_range]

    fig_rg = px.line(x=[f"{(g*100):.1f}%" for g in rg_range], y=rg_ps, markers=True,
                     title="Per-share Value vs Revenue Growth (holding other inputs constant)",
                     labels={"x": "Revenue Growth", "y": "Per-share (₹)"})
    fig_em = px.line(x=[f"{(m*100):.1f}%" for m in em_range], y=em_ps, markers=True,
                     title="Per-share Value vs EBIT Margin (holding other inputs constant)",
                     labels={"x": "EBIT Margin", "y": "Per-share (₹)"})
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_rg, use_container_width=True)
    c2.plotly_chart(fig_em, use_container_width=True)

    # -------------------- Football Field --------------------
    st.subheader("🏟️ Football Field — Valuation Ranges")

    # 1) DCF range from sensitivity: choose a reasonable core window around current inputs
    # pick percentile range of WACC/TG grid for per-share
    sens_values = pd.Series(np.array(heat).flatten())
    dcf_low = np.nanpercentile(sens_values, 25) if not sens_values.dropna().empty else np.nan
    dcf_high = np.nanpercentile(sens_values, 75) if not sens_values.dropna().empty else np.nan

    # 2) EV/EBITDA range -> convert to per-share: EV = mult * EBITDA; Equity = EV + cash - debt
    latest_year = int(ebitda_hist.index.max()) if not ebitda_hist.empty else (int(ebit_hist.index.max()) if not ebit_hist.empty else None)
    latest_ebitda = (ebitda_hist.loc[latest_year] if (latest_year and latest_year in ebitda_hist.index) else
                     (ebit_hist.loc[latest_year] if (latest_year and latest_year in ebit_hist.index) else np.nan))
    ev_low = ev_ebitda_low * latest_ebitda if pd.notna(latest_ebitda) else np.nan
    ev_high = ev_ebitda_high * latest_ebitda if pd.notna(latest_ebitda) else np.nan
    eq_low = ev_low + (cash if pd.notna(cash) else 0.0) - (debt if pd.notna(debt) else 0.0) if pd.notna(ev_low) else np.nan
    eq_high = ev_high + (cash if pd.notna(cash) else 0.0) - (debt if pd.notna(debt) else 0.0) if pd.notna(ev_high) else np.nan
    ev_ebitda_ps_low = eq_low / shares if (pd.notna(eq_low) and pd.notna(shares) and shares > 0) else np.nan
    ev_ebitda_ps_high = eq_high / shares if (pd.notna(eq_high) and pd.notna(shares) and shares > 0) else np.nan

    # 3) P/E range: Equity = P/E * EPS * shares; per-share = P/E * EPS
    latest_ni = net_income_hist.sort_index().iloc[-1] if not net_income_hist.empty else np.nan
    eps = (latest_ni / shares) if (pd.notna(latest_ni) and pd.notna(shares) and shares > 0) else np.nan
    pe_ps_low = pe_low * eps if pd.notna(eps) else np.nan
    pe_ps_high = pe_high * eps if pd.notna(eps) else np.nan

    ff_df = pd.DataFrame([
        {"Method": "DCF (sensitivity IQR)", "Low": dcf_low, "High": dcf_high},
        {"Method": "EV/EBITDA", "Low": ev_ebitda_ps_low, "High": ev_ebitda_ps_high},
        {"Method": "P/E", "Low": pe_ps_low, "High": pe_ps_high},
    ])

    # drop rows with all NaNs
    ff_df = ff_df.dropna(subset=["Low", "High"], how="all")

    if ff_df.empty:
        st.info("Not enough data to build football field (check EBITDA, Net Income, or shares).")
    else:
        ff_df["Low"], ff_df["High"] = ff_df["Low"].astype(float), ff_df["High"].astype(float)
        # Ensure Low <= High
        mask = ff_df["Low"] > ff_df["High"]
        ff_df.loc[mask, ["Low", "High"]] = ff_df.loc[mask, ["High", "Low"]].values

        fig_ff = go.Figure()
        for i, row in ff_df.iterrows():
            fig_ff.add_trace(go.Scatter(
                x=[row["Low"], row["High"]],
                y=[row["Method"], row["Method"]],
                mode="lines",
                line=dict(width=14),
                showlegend=False
            ))
            # Midpoint marker
            mid = np.nanmean([row["Low"], row["High"]])
            fig_ff.add_trace(go.Scatter(
                x=[mid], y=[row["Method"]],
                mode="markers+text",
                text=[f"{mid:,.0f}"],
                textposition="middle right",
                showlegend=False
            ))
        fig_ff.update_layout(
            title="Football Field (Per-share, ₹)",
            xaxis_title="Per-share Value (₹)",
            yaxis_title="",
            xaxis=dict(showgrid=True),
            height=350 + 40 * len(ff_df),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        st.plotly_chart(fig_ff, use_container_width=True)

    # -------------------- Notes & Caveats --------------------
    with st.expander("Notes, caveats, and tips"):
        st.markdown(
            """
- **Data source:** Yahoo Finance via `yfinance` — line items sometimes differ across tickers.  
- **Revenue forecast:** constant growth; for more realism, swap to a fade schedule or segment growth.  
- **NWC modeling:** uses *ΔNWC = NWC% × ΔRevenue* (quick proxy).  
- **Terminal value:** Gordon Growth; ensure **WACC > Terminal growth**.  
- **Football field:**  
  - DCF range = interquartile range of your WACC×g sensitivity grid.  
  - EV/EBITDA range uses latest EBITDA (falls back to EBIT if missing) and your multiple inputs.  
  - P/E uses latest net income and shares to estimate EPS.  
- You can **override shares** in the sidebar if auto-detected value looks off.
"""
        )
