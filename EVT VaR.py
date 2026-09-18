"""
Portfolio VaR & Expected Shortfall: Historical, Gaussian, and EVT (GPD) methods,
run on live prices pulled via yfinance for any portfolio you define.
"""
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats


def fetch_portfolio_losses(tickers, weights, lookback="5y"):
    """Download prices, return the portfolio's daily loss series (% terms, positive = loss)."""
    weights = np.array(weights) / np.sum(weights)
    prices = yf.download(tickers, period=lookback, progress=False)['Close']
    returns = prices.pct_change().dropna()
    port_returns = (returns * weights).sum(axis=1)
    return -port_returns * 100


def historical_var_es(losses, alpha):
    var = losses.quantile(alpha)
    es = losses[losses >= var].mean()
    return var, es


def gaussian_var_es(losses, alpha):
    mu, sigma = losses.mean(), losses.std(ddof=1)
    z = stats.norm.ppf(alpha)
    var = mu + sigma * z
    es = mu + sigma * stats.norm.pdf(z) / (1 - alpha)
    return var, es


def fit_gpd(losses, threshold_pct=0.95):
    losses = np.asarray(losses)
    u = np.quantile(losses, threshold_pct)
    exceed = losses[losses > u] - u
    xi, _, beta = stats.genpareto.fit(exceed, floc=0)
    return u, xi, beta, len(exceed), len(losses)


def evt_var_es(losses, alpha, threshold_pct=0.95):
    u, xi, beta, Nu, n = fit_gpd(losses, threshold_pct)
    if abs(xi) < 1e-6:
        var = u + beta * np.log(Nu / (n * (1 - alpha)))
    else:
        var = u + (beta / xi) * ((n / Nu * (1 - alpha)) ** (-xi) - 1)
    es = (var + beta - xi * u) / (1 - xi) if xi < 1 else np.inf
    return var, es, xi


def portfolio_risk_report(tickers, weights, portfolio_value=100_000,
                           confidence_levels=(0.95, 0.99, 0.999),
                           lookback="5y", threshold_pct=0.95):
    losses = fetch_portfolio_losses(tickers, weights, lookback)
    print(f"\n=== PORTFOLIO RISK REPORT: {', '.join(tickers)} ===")
    print(f"Value: ${portfolio_value:,.0f}   Trading days used: {len(losses)}\n")
    hdr = f"{'conf':>6} {'Hist VaR':>10} {'Hist CVaR':>10} {'Gauss VaR':>10} {'Gauss CVaR':>10} {'EVT VaR':>10} {'EVT CVaR':>10}"
    print(hdr); print("-" * len(hdr))
    xi = None
    for a in confidence_levels:
        hv, he = historical_var_es(losses, a)
        gv, ge = gaussian_var_es(losses, a)
        ev, ee, xi = evt_var_es(losses, a, threshold_pct)
        d = lambda pct: f"${portfolio_value * pct / 100:,.0f}"
        print(f"{a:>6.3f} {d(hv):>10} {d(he):>10} {d(gv):>10} {d(ge):>10} {d(ev):>10} {d(ee):>10}")
    print(f"\nFitted tail shape xi = {xi:.3f} "
          f"({'heavy tail, Gaussian likely too optimistic' if xi > 0.1 else 'roughly thin-tailed'})")


def get_portfolio_from_user():
    """Prompt for a custom portfolio: tickers, weights, and size."""
    tickers = [t.strip().upper() for t in input("Tickers, comma-separated (e.g. VOO,QQQ,GLD): ").split(",")]
    w_raw = input(f"Weights for {tickers}, comma-separated (blank = equal-weight): ").strip()
    weights = [float(w) for w in w_raw.split(",")] if w_raw else [1 / len(tickers)] * len(tickers)
    value = float(input("Portfolio value in $ (blank = 100000): ") or 100_000)
    return tickers, weights, value


if __name__ == "__main__":
    tickers, weights, value = get_portfolio_from_user()
    portfolio_risk_report(tickers, weights, portfolio_value=value)