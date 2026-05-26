"""Streamlit dashboard: macro-financial risk flags from ECB SDW data.

Run with:
    uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st
from mlkit.proxies import proxy_env

from omi.data import COUNTRIES, SDW_SERIES
from omi.flags import latest_flags
from omi.pipeline import PipelineResult, run_pipeline

FLAG_COLOR = {"green": "#2ecc71", "amber": "#f39c12", "red": "#e74c3c"}
FLAG_EMOJI = {"green": "🟢", "amber": "🟠", "red": "🔴"}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Fetching ECB SDW data…", ttl=60 * 60)
def load() -> PipelineResult:
    with proxy_env():
        return run_pipeline()


# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Macro-financial risk flags",
    page_icon="🚦",
    layout="wide",
)
st.title("Macro-financial risk flags")
st.caption("ECB SDW data → percentile-based vulnerability flags by country.")

with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Refresh data"):
        load.clear()
    st.markdown(
        "**Flag rules**\n\n"
        "- 🟢 within normal historical range\n"
        "- 🟠 beyond 75th pct (or 25th if lower-is-riskier)\n"
        "- 🔴 beyond 90th pct (or 10th if lower-is-riskier)\n\n"
        "Score: green=0, amber=1, red=2."
    )

result = load()
latest = latest_flags(result.flags)

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
overview_tab, drill_tab, briefing_tab = st.tabs(["Country overview", "Indicator drill-down", "Briefing"])


# --------------------------------------------------------------------------- #
# 1. Country overview
# --------------------------------------------------------------------------- #
with overview_tab:
    st.subheader("Latest risk score by country")
    scores = result.country_scores.copy()
    scores["country_name"] = scores["country"].map(COUNTRIES)
    scores = scores[["country", "country_name", "as_of_period", "score", "n_red", "n_amber", "n_green"]]

    cols = st.columns(len(scores))
    for col, (_, row) in zip(cols, scores.iterrows(), strict=False):
        with col:
            st.metric(
                label=f"{row['country_name']} ({row['country']})",
                value=int(row["score"]),
                delta=f"{int(row['n_red'])}🔴 {int(row['n_amber'])}🟠 {int(row['n_green'])}🟢",
                delta_color="off",
            )

    st.divider()
    st.subheader("Latest flag per indicator")
    pivot = (
        latest.assign(cell=lambda d: d["flag"].map(FLAG_EMOJI) + " " + d["flag"])
        .pivot(index="country", columns="indicator_id", values="cell")
        .reindex(index=scores["country"])
    )
    st.dataframe(pivot, use_container_width=True)


# --------------------------------------------------------------------------- #
# 2. Indicator drill-down
# --------------------------------------------------------------------------- #
with drill_tab:
    left, right = st.columns([1, 3])
    with left:
        country = st.selectbox(
            "Country",
            options=list(COUNTRIES.keys()),
            format_func=lambda c: f"{COUNTRIES[c]} ({c})",
        )
        indicator_id = st.selectbox(
            "Indicator",
            options=list(SDW_SERIES.keys()),
            format_func=lambda i: SDW_SERIES[i].name,
        )
        meta = SDW_SERIES[indicator_id]
        st.caption(meta.description)
        st.caption(
            f"Frequency: **{meta.frequency}** · Unit: **{meta.unit}** · Higher is riskier: **{meta.higher_is_riskier}**"
        )

    with right:
        series = result.flags[
            (result.flags["indicator_id"] == indicator_id) & (result.flags["country"] == country)
        ].sort_values("period")

        if series.empty:
            st.warning("No data for this combination.")
        else:
            amber = float(series["threshold_amber"].iloc[-1])
            red = float(series["threshold_red"].iloc[-1])
            last_obs = series.iloc[[-1]]

            base = (
                alt.Chart(series)
                .mark_line(color="#1f77b4")
                .encode(
                    x=alt.X("period:T", title=""),
                    y=alt.Y("value:Q", title=meta.unit),
                    tooltip=["period:T", "value:Q", "flag:N"],
                )
            )
            amber_rule = (
                alt.Chart(pd.DataFrame({"y": [amber]}))
                .mark_rule(color=FLAG_COLOR["amber"], strokeDash=[4, 4])
                .encode(y="y:Q")
            )
            red_rule = (
                alt.Chart(pd.DataFrame({"y": [red]}))
                .mark_rule(color=FLAG_COLOR["red"], strokeDash=[4, 4])
                .encode(y="y:Q")
            )
            last_point = (
                alt.Chart(last_obs)
                .mark_point(size=160, filled=True)
                .encode(
                    x="period:T",
                    y="value:Q",
                    color=alt.Color(
                        "flag:N",
                        scale=alt.Scale(
                            domain=list(FLAG_COLOR.keys()),
                            range=list(FLAG_COLOR.values()),
                        ),
                        legend=None,
                    ),
                    tooltip=["period:T", "value:Q", "flag:N"],
                )
            )

            st.altair_chart(
                (base + amber_rule + red_rule + last_point).properties(height=400),
                use_container_width=True,
            )

            latest_row = last_obs.iloc[0]
            st.markdown(
                f"**Latest:** {latest_row['period'].date()} · "
                f"value = `{latest_row['value']:.2f}` · "
                f"flag = {FLAG_EMOJI[latest_row['flag']]} **{latest_row['flag']}**  \n"
                f"Thresholds — amber: `{amber:.2f}`, red: `{red:.2f}`"
            )


# --------------------------------------------------------------------------- #
# 3. Briefing
# --------------------------------------------------------------------------- #
with briefing_tab:
    st.subheader("Top countries by current risk score")
    ranked = result.country_scores.copy()
    ranked.insert(1, "country_name", ranked["country"].map(COUNTRIES))
    st.dataframe(ranked.head(5), use_container_width=True, hide_index=True)

    st.subheader("Indicators currently flagging amber or red")
    triggered = (
        latest[latest["flag"].isin(["amber", "red"])]
        .assign(
            country_name=lambda d: d["country"].map(COUNTRIES),
            indicator=lambda d: d["indicator_id"].map(lambda i: SDW_SERIES[i].name),
        )
        .sort_values(["flag", "country", "indicator_id"], ascending=[True, True, True])[
            ["country", "country_name", "indicator", "value", "threshold_amber", "threshold_red", "flag"]
        ]
        .reset_index(drop=True)
    )
    if triggered.empty:
        st.success("All indicators currently green.")
    else:
        st.dataframe(triggered, use_container_width=True, hide_index=True)

    st.subheader("Change versus previous period (per indicator)")
    flags_df = result.flags.sort_values(["indicator_id", "country", "period"])
    prev = (
        flags_df.groupby(["indicator_id", "country"])
        .tail(2)
        .groupby(["indicator_id", "country"])
        .agg(prev_flag=("flag", "first"), curr_flag=("flag", "last"))
        .reset_index()
    )
    changed = prev[prev["prev_flag"] != prev["curr_flag"]].assign(
        country_name=lambda d: d["country"].map(COUNTRIES),
        indicator=lambda d: d["indicator_id"].map(lambda i: SDW_SERIES[i].name),
        transition=lambda d: d["prev_flag"].map(FLAG_EMOJI) + " → " + d["curr_flag"].map(FLAG_EMOJI),
    )[["country", "country_name", "indicator", "prev_flag", "curr_flag", "transition"]]
    if changed.empty:
        st.info("No flag changes versus the previous observation.")
    else:
        st.dataframe(changed, use_container_width=True, hide_index=True)
