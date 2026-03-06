# Research Roadmap

Personal reference for picking this project back up.

---

## 1. Where We Are Now

- **fetch_markets.py** — collects resolved binary markets from the Gamma API
- **fetch_prices.py** — fetches CLOB price history for each market
- **Data lives in** `research/data/markets.db` (SQLite)
- **Target**: 10,000 resolved markets with price histories

The pipeline fetches resolved markets, extracts final YES/NO prices from outcome data, and stores everything in SQLite. Price histories come from the CLOB API using token IDs.

---

## 2. Immediate Next Steps When Returning

1. **Check how much data we actually have:**
   ```sql
   SELECT COUNT(*) FROM markets;
   SELECT COUNT(*) FROM markets WHERE final_yes_price IS NOT NULL;
   SELECT COUNT(*) FROM markets WHERE final_yes_price IS NULL;
   ```

2. **Run fetch_prices.py** to backfill CLOB price histories for all fetched markets

3. **Basic data exploration:**
   - Distribution of `final_yes_price` — are resolved markets mostly 0/1 or spread across the range?
   - Category breakdown (politics, crypto, sports, etc.)
   - Volume and liquidity distributions
   - Ratio of YES-resolved vs NO-resolved markets

---

## What We Learned (First Analysis)

Ran `research/analysis/calibration.py` on 9,902 resolved markets. Key findings:

1. **Dataset is dominated by near-certain markets (~95%).** The 0-10% bin has 7,063 markets and the 90-100% bin has 2,367. These are markets where the outcome was already obvious by the time they had a final price — not useful for studying calibration.

2. **Ghost markets initialized at ~0.50 with no real trading.** Many markets in the 40-60% range show 0% or 100% resolution rates with tiny sample sizes (e.g. 43 markets in the 50-60% bin). These appear to be low-liquidity markets that never attracted real trading activity, so their "final price" is just the initialization value, not a crowd estimate.

3. **Only ~50 genuinely uncertain, high-volume markets in the entire 10k sample.** The middle of the probability spectrum (20-80%) contains fewer than 300 markets total, and most of those are ghost markets. After filtering for meaningful volume, we'd be left with a handful — far too few for a calibration curve.

**Bottom line:** The first 10k resolved markets from the Gamma API are almost entirely slam-dunk outcomes. The calibration curve is a step function (0% → 100%) rather than a smooth diagonal, because the dataset lacks genuinely uncertain markets.

---

## What We Learned (Pre-Resolution Calibration)

Shifted from final prices (which are mostly 0/1) to **pre-resolution snapshot prices** — what the market thought 24h, 6h, and 1h before resolution. Filtered to 0.05-0.95 to exclude near-certain markets.

### Pre-resolution calibration curves

- **24h before**: 2,847 markets. Reasonably well-calibrated overall, with slight overconfidence in the 60-80% range.
- **6h before**: 2,685 markets. Tighter to the diagonal — crowds correct as resolution approaches.
- **1h before**: 2,523 markets. Nearly perfect calibration. Markets are efficient in the final hour.

**Key finding:** Polymarket crowds are well-calibrated in aggregate, but the signal degrades as you move further from resolution. The 24h-before window is where exploitable miscalibration is most likely.

### Category-level calibration

Built per-category calibration curves using 24h-before prices. Categories with 50+ markets:

- **Crypto** — Systematic overconfidence. Markets priced at 60-80% resolve YES less often than implied. This is the strongest bias signal in the dataset.
- **Sports** — Well-calibrated across the board. Betting markets have decades of efficiency behind them.
- **Politics** — Slight overconfidence at the extremes, but sample sizes are smaller.

**Primary hypothesis:** Crypto markets on Polymarket attract participants with directional bias (bulls pricing YES too high), creating a persistent overconfidence pattern that may be exploitable.

### Next steps

1. **Deep-dive into Crypto overconfidence** — Is this robust across time periods? Does it survive volume-weighting? Is it driven by a few outlier markets or a broad pattern?
2. **Backtest against transaction costs** — Polymarket charges ~2% on winnings. The Crypto bias must exceed this threshold to be a real edge. Simulate a strategy that fades Crypto overconfidence at the 24h mark and measure net returns.
3. **Scale the dataset** — 50+ Crypto markets is a start, but 200+ would give much more statistical confidence. Continue fetching via Gamma API or consider Dune Analytics for faster access.

---

## 3. Building the Calibration Curve (Core Research Goal)

### What it is
Bucket markets by their final YES price (the crowd's last probability estimate before resolution). For each bucket, measure the actual resolution rate.

Example: Of all markets where the final YES price was ~0.70, did ~70% actually resolve YES?

### What to look for
- **Perfect calibration** = points on the diagonal (70% price → 70% resolve YES)
- **Deviation from diagonal** = systematic crowd bias = exploitable edge
- Overconfidence: high-priced markets resolve YES less often than the price implies
- Underconfidence: low-priced markets resolve YES more often than expected

### Break it down
- By **category** (politics, crypto, sports) — bias likely varies by domain
- By **volume** — high-volume markets may be better calibrated
- By **time period** — calibration may shift over time
- By **days to resolution** — short-term vs long-term markets

---

## 4. The ML Model (After Calibration Curve)

### Feature ideas
- Category (one-hot or embedding)
- Volume and liquidity
- Days to close
- Price trajectory (slope, volatility, momentum in final hours/days)
- Number of unique traders (if available)
- Market description embeddings (NLP features)

### Target variable
- Binary: did market resolve YES?
- Or regression: predict true probability, compare to crowd price

### Honest backtesting — non-negotiable
- **No lookahead bias**: train only on markets that resolved before the test period
- **Realistic fees**: Polymarket charges ~2% on winnings
- **Slippage**: large orders move the price, especially in thin markets
- **Time-series split**: walk-forward validation, never random split
- **Kelly criterion**: size bets proportional to edge, not fixed amounts

---

## 5. Commands Cheat Sheet

```bash
# Resume market fetch (checkpointed, safe to interrupt)
python -m research.pipeline.fetch_markets --max-markets 10000

# Fetch CLOB price histories for all markets in DB
python -m research.pipeline.fetch_prices

# Quick DB health check
sqlite3 research/data/markets.db "SELECT COUNT(*), AVG(final_yes_price) FROM markets WHERE final_yes_price IS NOT NULL"

# Count markets by category
sqlite3 research/data/markets.db "SELECT category, COUNT(*) FROM markets GROUP BY category ORDER BY COUNT(*) DESC"

# Check price history coverage
sqlite3 research/data/markets.db "SELECT COUNT(DISTINCT market_id) FROM price_history"
```

---

## 6. Key Technical Gotchas

- **Gamma API JSON strings**: `outcomes` and `outcomePrices` come back as JSON-encoded strings, not native lists. Must `json.loads()` before use.
- **Interpreting final prices**: `outcomePrices ["1","0"]` = YES won, `["0","1"]` = NO won, anything else = ambiguous/unresolved.
- **CLOB API uses token IDs**, not market IDs. The query parameter is `market`, not `token_id`.
- **Old markets (pre-2022)** have no CLOB price history — fetch newest markets first to maximize coverage.
- **Pipeline is checkpointed** — safe to Ctrl+C and resume anytime. It picks up where it left off.
- **Rate limiting**: both APIs have rate limits. The pipeline has built-in delays but watch for 429s.

---

## 7. Longer Term Vision

```
Calibration curve
  → Find systematic biases in crowd pricing
    → ML model to predict mispricings
      → Paper trade the strategy, prove the edge exists
        → Real capital (small, with strict risk limits)
          → 10-year: probability intelligence product/API
```

The end game isn't just trading. It's understanding where crowds systematically get probability wrong — and building tools around that insight. A calibration-as-a-service API, decision support for forecasters, or a hedge fund that trades on crowd bias.

But first: get the data, draw the curve, see if the edge is real.
