"""End-to-end pipeline: fetch -> transform -> flag."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from omi import fetch, flags, transform


@dataclass
class PipelineResult:
    raw: pd.DataFrame
    indicators: pd.DataFrame
    flags: pd.DataFrame
    country_scores: pd.DataFrame


def run_pipeline() -> PipelineResult:
    """Fetch every series, derive comparable indicators, compute flags."""
    raw = fetch.fetch_all()
    indicators = transform.to_indicators(raw)
    flag_df = flags.compute_flags(indicators)
    scores = flags.country_risk_scores(flag_df)
    return PipelineResult(raw=raw, indicators=indicators, flags=flag_df, country_scores=scores)
