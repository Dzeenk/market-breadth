name: Daily Market Breadth Update

on:
  schedule:
    # Runs at 22:30 UTC = 5:30 PM ET (after NYSE close) every weekday
    - cron: '30 22 * * 1-5'
  
  # Allow manual trigger from GitHub Actions tab
  workflow_dispatch:
    inputs:
      backfill:
        description: 'Run full 200-day backfill instead of daily update'
        required: false
        default: 'false'
        type: boolean

jobs:
  update-breadth:
    runs-on: ubuntu-latest
    
    # Give write permissions so we can push the updated CSV back
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install yfinance pandas requests lxml html5lib beautifulsoup4

      - name: Run breadth update
        run: |
          if [ "${{ github.event.inputs.backfill }}" = "true" ]; then
            echo "Running full backfill..."
            python breadth_update.py --backfill
          else
            echo "Running daily update..."
            python breadth_update.py
          fi

      - name: Commit and push updated files
        run: |
          git config --local user.name  "github-actions[bot]"
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git add market_breadth_200d_REAL.csv update_log.json
          git diff --staged --quiet && echo "No changes to commit" || \
            git commit -m "📊 Daily breadth update $(date +'%Y-%m-%d')" && git push

      - name: Upload CSV as artifact (for debugging)
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: breadth-data-${{ github.run_id }}
          path: |
            market_breadth_200d_REAL.csv
            update_log.json
          retention-days: 7
