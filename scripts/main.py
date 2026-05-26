# %%
"""Run the full omi pipeline: fetch from ECB Data Portal -> SQLite."""

from mlkit.proxies import proxy_env

from omi.flags import latest_flags
from omi.pipeline import run_pipeline

# %% Fetch + transform + flag + persist, all behind the corporate proxy
with proxy_env():
    result = run_pipeline()

# %% Quick look at outputs
print(f"raw observations : {len(result.raw):>6}")
print(f"indicators       : {len(result.indicators):>6}")
print(f"risk flags       : {len(result.flags):>6}")
print()
print("Country risk scores (latest):")
print(result.country_scores.to_string(index=False))

# %% Latest per-indicator flags per country
latest = latest_flags(result.flags)
print("\nLatest flags by country / indicator:")
print(latest.pivot(index="country", columns="indicator_id", values="flag").to_string())
