from dataclasses import dataclass
from typing import Literal

Country = Literal["DE", "FR", "IT", "ES"]
Frequency = Literal["M", "Q"]


@dataclass(frozen=True)
class SDWSeries:
    name: str
    description: str
    dataset: str
    frequency: Frequency
    unit: str
    higher_is_riskier: bool
    keys: dict[Country, str]


SDW_SERIES: dict[str, SDWSeries] = {
    "nfc_loan_growth": SDWSeries(
        name="NFC loan growth",
        description="Adjusted loans to non-financial corporations, annual growth rate",
        dataset="BSI",
        frequency="M",
        unit="percent_yoy",
        higher_is_riskier=True,
        keys={
            "DE": "BSI.M.DE.N.A.A20T.A.I.U2.2240.Z01.A",
            "FR": "BSI.M.FR.N.A.A20T.A.I.U2.2240.Z01.A",
            "IT": "BSI.M.IT.N.A.A20T.A.I.U2.2240.Z01.A",
            "ES": "BSI.M.ES.N.A.A20T.A.I.U2.2240.Z01.A",
        },
    ),
    "hh_loan_growth": SDWSeries(
        name="Household loan growth",
        description="Adjusted loans to households, annual growth rate",
        dataset="BSI",
        frequency="M",
        unit="percent_yoy",
        higher_is_riskier=True,
        keys={
            "DE": "BSI.M.DE.N.A.A20T.A.I.U2.2250.Z01.A",
            "FR": "BSI.M.FR.N.A.A20T.A.I.U2.2250.Z01.A",
            "IT": "BSI.M.IT.N.A.A20T.A.I.U2.2250.Z01.A",
            "ES": "BSI.M.ES.N.A.A20T.A.I.U2.2250.Z01.A",
        },
    ),
    "house_price_index": SDWSeries(
        name="Residential property prices",
        description="Residential property price index, all dwellings; compute YoY growth in Python",
        dataset="RESR",
        frequency="Q",
        unit="index",
        higher_is_riskier=True,
        keys={
            "DE": "RESR.Q.DE._T.N._TR.TVAL.4D0.TB.N.IX",
            "FR": "RESR.Q.FR._T.N._TR.TVAL.4D0.TB.N.IX",
            "IT": "RESR.Q.IT._T.N._TR.TVAL.4D0.TB.N.IX",
            "ES": "RESR.Q.ES._T.N._TR.TVAL.4D0.TB.N.IX",
        },
    ),
    "unemployment_rate": SDWSeries(
        name="Unemployment rate",
        description="Unemployment rate, total, age 15-74, seasonally adjusted",
        dataset="LFSI",
        frequency="M",
        unit="percent",
        higher_is_riskier=True,
        keys={
            "DE": "LFSI.M.DE.S.UNEHRT.TOTAL0.15_74.T",
            "FR": "LFSI.M.FR.S.UNEHRT.TOTAL0.15_74.T",
            "IT": "LFSI.M.IT.S.UNEHRT.TOTAL0.15_74.T",
            "ES": "LFSI.M.ES.S.UNEHRT.TOTAL0.15_74.T",
        },
    ),
    "hicp_inflation": SDWSeries(
        name="HICP inflation",
        description="HICP all-items inflation, annual rate of change",
        dataset="ICP",
        frequency="M",
        unit="percent_yoy",
        higher_is_riskier=True,
        keys={
            "DE": "ICP.M.DE.N.000000.4.ANR",
            "FR": "ICP.M.FR.N.000000.4.ANR",
            "IT": "ICP.M.IT.N.000000.4.ANR",
            "ES": "ICP.M.ES.N.000000.4.ANR",
        },
    ),
    "real_gdp_growth": SDWSeries(
        name="Real GDP growth",
        description="Real GDP volume, annual growth rate",
        dataset="MNA",
        frequency="Q",
        unit="percent_yoy",
        higher_is_riskier=False,
        keys={
            "DE": "MNA.Q.Y.DE.W2.S1.S1.B.B1GQ._Z._Z._Z.XDC.LR.GY",
            "FR": "MNA.Q.Y.FR.W2.S1.S1.B.B1GQ._Z._Z._Z.XDC.LR.GY",
            "IT": "MNA.Q.Y.IT.W2.S1.S1.B.B1GQ._Z._Z._Z.XDC.LR.GY",
            "ES": "MNA.Q.Y.ES.W2.S1.S1.B.B1GQ._Z._Z._Z.XDC.LR.GY",
        },
    ),
}


COUNTRIES: dict[Country, str] = {
    "DE": "Germany",
    "FR": "France",
    "IT": "Italy",
    "ES": "Spain",
}


RISK_FLAG_RULES = {
    "higher_is_riskier": {
        "red": 0.90,
        "amber": 0.75,
        "green": None,
    },
    "lower_is_riskier": {
        "red": 0.10,
        "amber": 0.25,
        "green": None,
    },
}


def iter_sdw_keys():
    """Yield flattened SDW series metadata, useful for fetching/storing."""
    for indicator_id, series in SDW_SERIES.items():
        for country, key in series.keys.items():
            yield {
                "indicator_id": indicator_id,
                "indicator_name": series.name,
                "country": country,
                "country_name": COUNTRIES[country],
                "dataset": series.dataset,
                "frequency": series.frequency,
                "unit": series.unit,
                "higher_is_riskier": series.higher_is_riskier,
                "sdw_key": key,
            }


# Example:
# for item in iter_sdw_keys():
#     print(item["country"], item["indicator_id"], item["sdw_key"])
