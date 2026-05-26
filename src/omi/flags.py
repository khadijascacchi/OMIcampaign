"""Compute percentile-based risk flags and per-country risk scores.

Conventions (see RISK_FLAG_RULES in omi.data):

* higher_is_riskier=True  -> amber if value >= 75th pct, red if >= 90th pct
* higher_is_riskier=False -> amber if value <= 25th pct, red if <= 10th pct

Score per indicator: green=0, amber=1, red=2.
Country score is the sum across indicators (latest observation per indicator).
"""

from __future__ import annotations

import pandas as pd

from omi.data import SDW_SERIES

_SCORE = {"green": 0, "amber": 1, "red": 2}


def _classify(value: float, amber: float, red: float, higher_is_riskier: bool) -> str:
    if higher_is_riskier:
        if value >= red:
            return "red"
        if value >= amber:
            return "amber"
        return "green"
    if value <= red:
        return "red"
    if value <= amber:
        return "amber"
    return "green"


def compute_flags(indicators: pd.DataFrame) -> pd.DataFrame:
    """Attach percentile thresholds, flag, and score to every observation.

    Thresholds are estimated from the (indicator, country) historical sample
    so each country is benchmarked against its own past.
    """
    if indicators.empty:
        return indicators.assign(
            threshold_amber=pd.Series(dtype=float),
            threshold_red=pd.Series(dtype=float),
            flag=pd.Series(dtype=str),
            score=pd.Series(dtype=int),
        )

    out_frames: list[pd.DataFrame] = []
    for (indicator_id, country), grp in indicators.groupby(["indicator_id", "country"], sort=False):
        meta = SDW_SERIES[indicator_id]
        higher = meta.higher_is_riskier
        if higher:
            amber = grp["value"].quantile(0.75)
            red = grp["value"].quantile(0.90)
        else:
            amber = grp["value"].quantile(0.25)
            red = grp["value"].quantile(0.10)

        g = grp.copy()
        g["threshold_amber"] = amber
        g["threshold_red"] = red
        g["flag"] = g["value"].apply(lambda v: _classify(v, amber, red, higher_is_riskier=higher))
        g["score"] = g["flag"].map(_SCORE).astype(int)
        out_frames.append(g)

    cols = [
        "indicator_id",
        "country",
        "period",
        "value",
        "unit",
        "threshold_amber",
        "threshold_red",
        "flag",
        "score",
    ]
    return pd.concat(out_frames, ignore_index=True)[cols]


def latest_flags(flags: pd.DataFrame) -> pd.DataFrame:
    """Keep only the most recent observation per (indicator, country)."""
    if flags.empty:
        return flags
    idx = flags.groupby(["indicator_id", "country"])["period"].idxmax()
    return flags.loc[idx].reset_index(drop=True)


def country_risk_scores(flags: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the latest per-indicator flags into a per-country score."""
    latest = latest_flags(flags)
    if latest.empty:
        return pd.DataFrame(columns=["country", "as_of_period", "n_green", "n_amber", "n_red", "score"])

    def _agg(g: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "as_of_period": g["period"].max(),
            "n_green": int((g["flag"] == "green").sum()),
            "n_amber": int((g["flag"] == "amber").sum()),
            "n_red": int((g["flag"] == "red").sum()),
            "score": int(g["score"].sum()),
        })

    return (
        latest.groupby("country", as_index=False)
        .apply(_agg, include_groups=False)
        .sort_values("score", ascending=False)
        .reset_index(drop=True)
    )
