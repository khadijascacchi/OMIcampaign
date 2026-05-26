"""Transform raw SDW observations into comparable indicator series.

Most series in omi.data already arrive in a comparable unit (percent or
percent_yoy). The one exception is the residential property price *index*,
for which we compute year-on-year % change so it can be compared to the
other risk indicators.
"""

from __future__ import annotations

import pandas as pd

from omi.data import SDW_SERIES, Frequency

# Lag (in periods) used to compute year-on-year change for each frequency.
_YOY_LAG: dict[Frequency, int] = {"M": 12, "Q": 4}


def _yoy_pct_change(values: pd.Series, freq: Frequency) -> pd.Series:
    """Year-on-year percent change for a regularly-spaced series."""
    return values.pct_change(periods=_YOY_LAG[freq]) * 100.0


def to_indicators(raw: pd.DataFrame) -> pd.DataFrame:
    """Return a long DataFrame of comparable indicator values.

    Columns: indicator_id, country, period, value, unit.
    For series with unit='index' we replace `value` by its YoY % change
    and set unit='percent_yoy'. Everything else passes through unchanged.
    """
    if raw.empty:
        return raw.assign(unit=pd.Series(dtype=str))

    out_frames: list[pd.DataFrame] = []
    for (indicator_id, country), grp in raw.sort_values("period").groupby(["indicator_id", "country"], sort=False):
        series_meta = SDW_SERIES[indicator_id]
        grp = grp.copy()
        if series_meta.unit == "index":
            grp["value"] = _yoy_pct_change(grp["value"], series_meta.frequency)
            grp["unit"] = "percent_yoy"
        else:
            grp["unit"] = series_meta.unit
        out_frames.append(grp[["indicator_id", "country", "period", "value", "unit"]])

    out = pd.concat(out_frames, ignore_index=True)
    # Drop leading NaNs produced by YoY transformation.
    return out.dropna(subset=["value"]).reset_index(drop=True)
