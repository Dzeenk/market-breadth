import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import json
import time

CSV_PATH = "market_breadth_200d_REAL.csv"
LOG_PATH = "update_log.json"

def get_sp500_tickers():
    try:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        tickers = tables[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
        print(f"  S&P 500: {len(tickers)} tickers")
        return tickers
    except Exception as e:
        print(f"  Warning: could not fetch S&P 500 list: {e}")
        return []

def get_ticker_universe():
    tickers = get_sp500_tickers()
    if not tickers:
        tickers = [
            'AAPL','MSFT','NVDA','AMZN','META','GOOGL','TSLA','BRK-B','JPM','UNH',
            'LLY','XOM','V','AVGO','MA','PG','COST','HD','MRK','CVX','ABBV','PEP',
            'KO','WMT','ADBE','CRM','TMO','MCD','CSCO','ACN','ABT','BAC','DHR','PFE',
            'TXN','NFLX','CMCSA','WFC','PM','INTC','AMD','HON','UPS','NEE','RTX',
            'AMGN','QCOM','IBM','CAT','GE','INTU','SPGI','BLK','GS','LOW','AXP',
            'ISRG','ELV','MDT','SYK','VRTX','REGN','ZTS','CI','MMC','PLD','AMT',
        ]
        print(f"  Fallback universe: {len(tickers)} tickers")
    return tickers

def download_price_data(tickers, days_back=120):
    end = datetime.today()
    start = end - timedelta(days=days_back)
    print(f"  Downloading prices for {len(tickers)} tickers ({start.date()} to {end.date()})...")
    batch_size = 100
    all_data = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        try:
            df = yf.download(batch, start=start, end=end, progress=False, auto_adjust=True, threads=True)['Close']
            all_data.append(df)
            time.sleep(0.5)
        except Exception as e:
            print(f"  Warning: batch {i//batch_size + 1} failed: {e}")
    if not all_data:
        raise RuntimeError("Could not download any price data.")
    data = pd.concat(all_data, axis=1)
    data = data.dropna(axis=1, how='all')
    print(f"  Got {data.shape[1]} stocks x {data.shape[0]} days")
    return data

def calculate_breadth_for_date(data, date_idx):
    if date_idx < 1:
        return None
    daily_pct = data.iloc[date_idx] / data.iloc[date_idx - 1] - 1
    daily_pct = daily_pct.dropna()
    up4  = int((daily_pct >= 0.04).sum())
    dn4  = int((daily_pct <= -0.04).sum())
    up2  = int((daily_pct >= 0.02).sum())
    dn2  = int((daily_pct <= -0.02).sum())
    qtr_start = max(0, date_idx - 65)
    qtr_pct = data.iloc[date_idx] / data.iloc[qtr_start] - 1
    qtr_pct = qtr_pct.dropna()
    up25q = int((qtr_pct >= 0.25).sum())
    dn25q = int((qtr_pct <= -0.25).sum())
    up50q = int((qtr_pct >= 0.50).sum())
    mo_start = max(0, date_idx - 20)
    mo_pct = data.iloc[date_idx] / data.iloc[mo_start] - 1
    mo_pct = mo_pct.dropna()
    up25m = int((mo_pct >= 0.25).sum())
    return {
        'Date': data.index[date_idx].strftime('%Y-%m-%d'),
        'Up_4pct_Daily': up4, 'Down_4pct_Daily': dn4,
        'Up_2pct_Daily': up2, 'Down_2pct_Daily': dn2,
        'Up_25pct_Quarter': up25q, 'Down_25pct_Quarter': dn25q,
        'Up_50pct_Quarter': up50q, 'Up_25pct_Month': up25m,
        'Total_Stocks': int(daily_pct.count()),
    }

def add_rolling_metrics(df):
    df = df.copy()
    df['10Day_Bulls'] = df['Up_4pct_Daily'].rolling(10, min_periods=5).sum().round(0).astype('Int64')
    df['10Day_Bears'] = df['Down_4pct_Daily'].rolling(10, min_periods=5).sum().round(0).astype('Int64')
    df['10Day_Ratio'] = (df['10Day_Bulls'] / df['10Day_Bears'].replace(0, 1)).round(2)
    df['DCR'] = (df['Up_4pct_Daily'] - df['Down_4pct_Daily']).cumsum()

    def regime(row):
        r = row['10Day_Ratio'] if pd.notna(row['10Day_Ratio']) else 0
        q = row['Up_25pct_Quarter']
        if r >=
