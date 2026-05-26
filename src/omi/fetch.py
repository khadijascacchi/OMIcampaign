"""Fetch full time series from the ECB Data Portal (SDW successor).

The ECB SDMX endpoint returns CSV with one row per observation. We parse it
into a tidy long DataFrame keyed by (indicator_id, country, period).
"""

from __future__ import annotations

import csv
import io
import urllib.error
import urllib.request

import pandas as pd

from omi.data import SDW_SERIES, Country, SDWSeries, iter_sdw_keys

BASE_URL = "https://data-api.ecb.europa.eu/service/data"
TIMEOUT_S = 60


class FetchError(RuntimeError):
    pass


def _request_csv(sdw_key: str) -> str:
    dataflow, _, key_path = sdw_key.partition(".")
    url = f"{BASE_URL}/{dataflow}/{key_path}?format=csvdata"
    req = urllib.request.Request(url, headers={"Accept": "text/csv"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code} for {sdw_key}") from e
    except urllib.error.URLError as e:
        raise FetchError(f"URL error for {sdw_key}: {e.reason}") from e
    except TimeoutError as e:
        raise FetchError(f"timeout for {sdw_key}") from e


def _parse_period(label: str, freq: str) -> pd.Timestamp:
    """Convert SDMX period label ("2024-04", "2024-Q1") to a period-start date."""
    if freq == "Q":
        return pd.Period(label, freq="Q").to_timestamp(how="start")
    if freq == "M":
        return pd.Period(label, freq="M").to_timestamp(how="start")
    raise ValueError(f"unsupported frequency: {freq}")


def fetch_series(indicator_id: str, country: Country, series: SDWSeries) -> pd.DataFrame:
    """Return a long DataFrame for one (indicator, country) series."""
    sdw_key = series.keys[country]
    body = _request_csv(sdw_key)
    rows = list(csv.DictReader(io.StringIO(body)))
    if not rows:
        raise FetchError(f"no rows returned for {sdw_key}")

    df = pd.DataFrame({
        "indicator_id": indicator_id,
        "country": country,
        "sdw_key": sdw_key,
        "period": [_parse_period(r["TIME_PERIOD"], series.frequency) for r in rows],
        "value": [float(r["OBS_VALUE"]) for r in rows if r["OBS_VALUE"] != ""],
    })
    return df.sort_values("period").reset_index(drop=True)


def fetch_all() -> pd.DataFrame:
    """Fetch every (indicator, country) declared in omi.data and concat them."""
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for meta in iter_sdw_keys():
        series = SDW_SERIES[meta["indicator_id"]]
        try:
            frames.append(fetch_series(meta["indicator_id"], meta["country"], series))
        except FetchError as e:
            errors.append(str(e))
    if errors:
        print(f"[fetch_all] {len(errors)} series failed:")
        for msg in errors:
            print(f"  - {msg}")
    if not frames:
        return pd.DataFrame(columns=["indicator_id", "country", "sdw_key", "period", "value"])
    return pd.concat(frames, ignore_index=True)
