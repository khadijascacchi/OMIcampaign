# omi — Macro-financial risk flags using ECB SDW data

A small Python + Streamlit toy that pulls country-level time series from the
ECB Statistical Data Warehouse (now the [ECB Data Portal][edp]) and turns
them into simple **green / amber / red** risk flags for a handful of
macro-financial vulnerability indicators.


## Idea in one paragraph

For each of `{DE, FR, IT, ES}` we pull a few vulnerability-relevant series
(credit growth, residential property prices, unemployment, HICP inflation,
real GDP growth), normalise them to a comparable unit, and benchmark the
latest observation against the country's own history using simple
percentile thresholds:

- `higher_is_riskier=True`  → amber ≥ 75th pct, red ≥ 90th pct
- `higher_is_riskier=False` → amber ≤ 25th pct, red ≤ 10th pct

Each flag contributes `green=0, amber=1, red=2` to the country score.
The result is a small dashboard that prioritises **where to look**.

## Dashboard

**1. Country overview** — latest score per country and a flag matrix per
indicator.

![Country overview](https://github.com/khadijascacchi/OMIcampaign/blob/main/docs/fig1.png)

**2. Indicator drill-down** — full history of one (country, indicator) with
amber / red threshold lines and the latest observation highlighted.

![Indicator drill-down](https://github.com/khadijascacchi/OMIcampaign/blob/main/docs/fig2.png)

**3. Briefing** — top countries by current risk score, the indicators that
triggered amber/red, and flag changes versus the previous observation.

![Briefing](https://github.com/khadijascacchi/OMIcampaign/blob/main/docs/fig3.png)

## Project layout

```
src/omi/
  data.py        # indicator + series-key catalogue (SDW keys per country)
  fetch.py       # ECB Data Portal CSV client -> tidy DataFrame
  transform.py   # raw obs -> comparable indicator series (YoY where needed)
  flags.py       # percentile thresholds, flag, per-country score
  pipeline.py    # fetch -> transform -> flag, returns 4 DataFrames
app/
  streamlit_app.py
scripts/
  main.py        # CLI runner (prints the same tables to stdout)
```

Everything lives in pandas — no database. For ~6.5k rows that's plenty.

## Setup

Requires Python ≥ 3.12 and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Run

CLI smoke test (prints scores + flag matrix):

```bash
uv run python scripts/main.py
```

Streamlit dashboard:

```bash
uv run streamlit run app/streamlit_app.py
```
