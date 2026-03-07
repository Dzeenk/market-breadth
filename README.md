# 📊 Market Breadth Monitor

A fully automated market breadth dashboard based on **Pradeep Bonde's Stockbee methodology**.

Runs every weekday at 5:30 PM ET via **GitHub Actions** (free). Displays on **GitHub Pages** (free). Updates automatically — no server, no subscription, no cost.

---

## What it tracks

| Indicator | What it means |
|---|---|
| **10-Day Bull/Bear Ratio** | Core swing trade timing signal. >2.0 = favorable environment |
| **Up 25%+ Quarter** | Momentum stock universe. >300 = healthy bull phase |
| **Down 25%+ Quarter** | Damaged stocks. <200 = extreme bearish (contrarian buy signal) |
| **Up/Down 4%+ Daily** | Raw buying vs selling pressure each day |
| **Swing Signal** | TRADE / SELECTIVE / CASH based on combined breadth |

---

## Setup (10 minutes)

### Step 1 — Fork or create this repository

1. Go to [github.com](https://github.com) and create a free account if you don't have one
2. Create a **new repository** called `market-breadth`
3. Upload all these files maintaining the folder structure

### Step 2 — Enable GitHub Pages

1. In your repo, go to **Settings → Pages**
2. Under "Source", select **Deploy from a branch**
3. Choose branch: `main`, folder: `/docs`
4. Click **Save**
5. Your dashboard will be live at: `https://YOURUSERNAME.github.io/market-breadth`

### Step 3 — Run the first backfill

1. Go to **Actions** tab in your repo
2. Click **"Daily Market Breadth Update"**
3. Click **"Run workflow"**
4. Check the **"Run full 200-day backfill"** checkbox
5. Click **"Run workflow"** (green button)

This downloads 200 days of historical data. Takes about 5 minutes.

### Step 4 — Update the dashboard URL

Open `docs/index.html` and find this near the top of the `<script>` section:

```javascript
const GITHUB_USERNAME = 'GITHUB_USERNAME';  // ← Change this
const REPO_NAME       = 'market-breadth';   // ← Change if different
```

Replace `GITHUB_USERNAME` with your actual GitHub username, commit and push.

### Step 5 — Verify automation

After the backfill completes, the Actions tab will show a green checkmark.
Every weekday at 5:30 PM ET, GitHub will automatically:
1. Run `breadth_update.py`
2. Append today's data to the CSV
3. Commit and push the updated file
4. Your dashboard refreshes with new data next time you open it

---

## File structure

```
market-breadth/
├── .github/
│   └── workflows/
│       └── update.yml          ← GitHub Actions automation
├── docs/
│   └── index.html              ← Live dashboard (GitHub Pages)
├── breadth_update.py           ← Data fetching script
├── requirements.txt            ← Python dependencies
├── market_breadth_200d_REAL.csv ← Auto-generated data file
├── update_log.json             ← Latest run summary
└── README.md
```

---

## Trading signals explained

**TRADE** — Ratio ≥ 2.0 AND Up25Q ≥ 250. Full position sizes, look for momentum setups aggressively.

**SELECTIVE** — Ratio ≥ 1.5 AND Up25Q ≥ 180. Small position sizes only. Be very choosy.

**CASH** — Everything else. No new buys. Protect capital.

The Bonde methodology is clear: most of the money is made during TRADE phases. The skill is doing nothing during CASH phases.

---

## Data source & universe

- **Source**: Yahoo Finance via `yfinance` (free, no API key needed)
- **Universe**: S&P 500 (~503 stocks)
- **True Bonde breadth** uses all NYSE+NASDAQ (~8,000 stocks) — for that, you need TC2000 or a paid data vendor
- The signals behave the same way with S&P 500; absolute numbers are smaller but ratios are comparable

---

## Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# First run: full 200-day backfill
python breadth_update.py --backfill

# Daily update (run after 4 PM ET on weekdays)
python breadth_update.py
```

---

## Customising thresholds

The thresholds in `breadth_update.py` are calibrated for the S&P 500 universe (~503 stocks).
If you expand to a larger universe, adjust accordingly:

| Universe | Up25Q Bull threshold | Ratio threshold |
|---|---|---|
| S&P 500 (~503) | 300 | 2.0 |
| Russell 3000 (~3000) | 500 | 2.0 |
| All US stocks (~8000) | 400+ | 2.0 |

The **10-day ratio threshold of 2.0** stays the same regardless of universe size — it's a ratio, not an absolute number.

---

*Based on Pradeep Bonde's market breadth methodology — stockbee.blogspot.com*
