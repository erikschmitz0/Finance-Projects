import yfinance as yf
WATCHLIST = {"S&P 500": "^GSPC", "DJIA": "^DJI", "NASDAQ": "^IXIC", "10Y Yield": "^TNX", "VIX": "^VIX", "VVIX": "^VVIX", "Gold": "GC=F", "WTI Crude": "CL=F", "Brent Crude": "BZ=F"}
print(f"{'Name':<12}{'Ticker':<8}{'Open':>10}{'Price':>10}{'Chg $':>9}{'Chg %':>8}")
for name, sym in WATCHLIST.items():
    try:
        fi = yf.Ticker(sym).fast_info
        o, p, pc = fi.open or float('nan'), fi.last_price or float('nan'), fi.previous_close or float('nan')
        print(f"{name:<12}{sym:<8}{o:>10,.2f}{p:>10,.2f}{p-pc:>+9,.2f}{(p/pc-1)*100:>+7.2f}%")
    except Exception as e:
        print(f"{name:<12}{sym:<8}error: {e}")
