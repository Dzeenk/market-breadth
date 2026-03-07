import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os, sys, json, time

CSV_PATH = "market_breadth_200d_REAL.csv"
LOG_PATH = "update_log.json"

def get_tickers():
    try:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        tickers = tables[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
        print(f"Got {len(tickers)} tickers from Wikipedia")
        return tickers
    except Exception as e:
        print(f"Wikipedia failed: {e}, using fallback list")
        return ['AAPL','MSFT','NVDA','AMZN','META','GOOGL','TSLA','BRK-B','JPM','UNH','LLY','XOM','V','AVGO','MA','PG','COST','HD','MRK','CVX','ABBV','PEP','KO','WMT','ADBE','CRM','TMO','MCD','CSCO','ACN','ABT','BAC','DHR','PFE','TXN','NFLX','CMCSA','WFC','AMD','HON','UPS','NEE','RTX','AMGN','QCOM','IBM','CAT','GE','INTU','SPGI','BLK','GS','LOW','AXP','ISRG','MDT','SYK','VRTX','REGN','ZTS','CI','MMC','PLD','AMT']

def get_prices(tickers, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    all_data = []
    for i in range(0, len(tickers), 100):
        batch = tickers[i:i+100]
        try:
            df = yf.download(batch, start=start, end=end, progress=False, auto_adjust=True, threads=True)['Close']
            all_data.append(df)
            time.sleep(0.5)
        except Exception as e:
            print(f"Batch {i//100+1} failed: {e}")
    if not all_data:
        raise RuntimeError("No data downloaded")
    data = pd.concat(all_data, axis=1)
    data = data.dropna(axis=1, how='all')
    print(f"Downloaded {data.shape[1]} stocks x {data.shape[0]} days")
    return data

def calc_row(data, i):
    if i < 1:
        return None
    d = data.iloc[i] / data.iloc[i-1] - 1
    d = d.dropna()
    q_start = max(0, i-65)
    q = data.iloc[i] / data.iloc[q_start] - 1
    q = q.dropna()
    m_start = max(0, i-20)
    m = data.iloc[i] / data.iloc[m_start] - 1
    m = m.dropna()
    return {
        'Date': data.index[i].strftime('%Y-%m-%d'),
        'Up_4pct_Daily': int((d >= 0.04).sum()),
        'Down_4pct_Daily': int((d <= -0.04).sum()),
        'Up_2pct_Daily': int((d >= 0.02).sum()),
        'Down_2pct_Daily': int((d <= -0.02).sum()),
        'Up_25pct_Quarter': int((q >= 0.25).sum()),
        'Down_25pct_Quarter': int((q <= -0.25).sum()),
        'Up_50pct_Quarter': int((q >= 0.50).sum()),
        'Up_25pct_Month': int((m >= 0.25).sum()),
        'Total_Stocks': int(d.count()),
    }

def add_metrics(df):
    df = df.copy()
    df['10Day_Bulls'] = df['Up_4pct_Daily'].rolling(10, min_periods=5).sum().round(0).astype('Int64')
    df['10Day_Bears'] = df['Down_4pct_Daily'].rolling(10, min_periods=5).sum().round(0).astype('Int64')
    df['10Day_Ratio'] = (df['10Day_Bulls'] / df['10Day_Bears'].replace(0, 1)).round(2)
    df['DCR'] = (df['Up_4pct_Daily'] - df['Down_4pct_Daily']).cumsum()

    def get_regime(row):
        r = float(row['10Day_Ratio']) if pd.notna(row['10Day_Ratio']) else 0
        q = int(row['Up_25pct_Quarter'])
        if r >= 2.0 and q >= 300:
            return 'BULL'
        elif r >= 1.5 and q >= 200:
            return 'NEUTRAL'
        elif r < 1.0 or q < 150:
            return 'BEAR'
        else:
            return 'CAUTION'

    def get_signal(row):
        r = float(row['10Day_Ratio']) if pd.notna(row['10Day_Ratio']) else 0
        q = int(row['Up_25pct_Quarter'])
        if r >= 2.0 and q >= 250:
            return 'TRADE'
        elif r >= 1.5 and q >= 180:
            return 'SELECTIVE'
        else:
            return 'CASH'

    df['Market_Regime'] = df.apply(get_regime, axis=1)
    df['Swing_Signal'] = df.apply(get_signal, axis=1)
    return df

def backfill(tickers):
    print("Running full 200-day backfill...")
    data = get_prices(tickers, days=320)
    rows = [calc_row(data, i) for i in range(1, len(data))]
    rows = [r for r in rows if r]
    df = pd.DataFrame(rows).tail(200).reset_index(drop=True)
    df = add_metrics(df)
    df.to_csv(CSV_PATH, index=False)
    print(f"Backfill done: {len(df)} rows")
    return df

def daily_update(tickers, existing):
    print("Running daily update...")
    data = get_prices(tickers, days=90)
    today = data.index[-1].strftime('%Y-%m-%d')
    if today in existing['Date'].values:
        print(f"Already have {today}, skipping")
        return existing
    row = calc_row(data, len(data)-1)
    if not row:
        print("Could not calculate today")
        return existing
    df = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
    df = df.tail(200).reset_index(drop=True)
    df = add_metrics(df)
    df.to_csv(CSV_PATH, index=False)
    last = df.iloc[-1]
    print(f"Updated: {today} | Ratio: {last['10Day_Ratio']} | Signal: {last['Swing_Signal']}")
    return df

def save_log(df):
    last = df.iloc[-1].to_dict()
    log = {
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'latest_date': str(last.get('Date', '')),
        'ratio': float(last.get('10Day_Ratio', 0)),
        'up25q': int(last.get('Up_25pct_Quarter', 0)),
        'dn25q': int(last.get('Down_25pct_Quarter', 0)),
        'up4': int(last.get('Up_4pct_Daily', 0)),
        'dn4': int(last.get('Down_4pct_Daily', 0)),
        'regime': str(last.get('Market_Regime', '')),
        'signal': str(last.get('Swing_Signal', '')),
        'total_rows': len(df),
    }
    with open(LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)
    print(f"Log saved")

if __name__ == '__main__':
    print("=" * 50)
    print(f"Market Breadth Updater - {datetime.today().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    tickers = get_tickers()
    existing = pd.read_csv(CSV_PATH) if os.path.exists(CSV_PATH) else pd.DataFrame()
    do_backfill = '--backfill' in sys.argv or existing.empty or len(existing) < 10
    df = backfill(tickers) if do_backfill else daily_update(tickers, existing)
    save_log(df)
    print(f"Done: {len(df)} rows | Signal: {df.iloc[-1]['Swing_Signal']} | Regime: {df.iloc[-1]['Market_Regime']}")
    print("=" * 50)
