"""Tests for build_directory across all three sectors.

Ground truth verified against raw CSVs:
- SNF 235555 (rec 1434340): The Orchards at Canterbury, Waterford, ctrl 3,
  11/01/2024-12/31/2024 (61 days).
- HOSP 234011 (recs 817596, 836485): Kingswood Hospital (Ferndale, ctrl 2)
  closes Feb 2025; the CCN re-emerges as Henry Ford Behavioral Health
  (zip 48322, ctrl 5) — a nonprofit-to-JV conversion visible in one join.
- HHA 239084 (rec 600997): Dream USA 2003 LLC, Saginaw, BLANK control type,
  final report (01/01/2025-03/19/2025, 78 days).
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.directory import build_directory
from mihealth.forms import HHA20_IDENTITY, HOSP10_IDENTITY, SNF10_IDENTITY
from mihealth.hcris import filter_state, load_alpha, load_rpt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def snf_directory(mi_alpha) -> pd.DataFrame:
    rpt = load_rpt(DATA_DIR / "SNF10FY2025" / "SNF10_2025_rpt.csv")
    return build_directory(filter_state(rpt, "23"), mi_alpha, SNF10_IDENTITY)


@pytest.fixture(scope="module")
def kingswood() -> pd.DataFrame:
    rpt = load_rpt(DATA_DIR / "HOSP10FY2025" / "HOSP10_2025_rpt.csv")
    rpt = rpt[rpt["PRVDR_NUM"] == "234011"]
    alpha = load_alpha(
        DATA_DIR / "HOSP10FY2025" / "HOSP10_2025_alpha.csv",
        rpt["RPT_REC_NUM"],
    )
    return build_directory(rpt, alpha, HOSP10_IDENTITY)


@pytest.fixture(scope="module")
def dream_usa() -> pd.DataFrame:
    rpt = load_rpt(DATA_DIR / "HHA20FY2025" / "HHA20_2025_rpt.csv")
    rpt = rpt[rpt["PRVDR_NUM"] == "239084"]
    alpha = load_alpha(DATA_DIR / "HHA20FY2025" / "HHA20_2025_alpha.csv", {600997})
    return build_directory(rpt, alpha, HHA20_IDENTITY)


def test_one_row_per_michigan_snf_report(snf_directory):
    assert len(snf_directory) == 13
    assert snf_directory.index.name == "RPT_REC_NUM"


def test_orchards_row_is_complete(snf_directory):
    orchards = snf_directory.loc[1434340]
    assert orchards["PRVDR_NUM"] == "235555"
    assert orchards["name"] == "THE ORCHARDS AT CANTERBURY ON THE LA"
    assert orchards["city"] == "WATERFORD"
    assert orchards["county"] == "OAKLAND"
    assert orchards["ownership"] == "Proprietary, Individual"
    assert orchards["ownership_category"] == "for-profit"
    assert orchards["period_days"] == 61
    assert orchards["is_partial_year"]


def test_kingswood_conversion_is_visible(kingswood):
    assert len(kingswood) == 2
    assert set(kingswood["name"]) == {
        "KINGSWOOD HOSPITAL",
        "HENRY FORD BEHAVIORAL HEALTH",
    }
    assert set(kingswood["ownership_category"]) == {"nonprofit", "for-profit"}
    assert set(kingswood["zip"]) == {"48220", "48322"}
    assert (kingswood["county"] == "OAKLAND").all()
    assert (kingswood["PRVDR_NUM"] == "234011").all()


def test_dream_usa_tolerates_blank_control_type(dream_usa):
    row = dream_usa.loc[600997]
    assert row["name"] == "DREAM USA 2003  LLC"
    assert row["city"] == "SAGINAW"
    assert row["zip"] == "48603-6825"
    assert pd.isna(row["ownership"])
    assert pd.isna(row["ownership_category"])
    assert row["period_days"] == 78
    assert row["is_partial_year"]


def test_hha_directory_has_no_county_column(dream_usa):
    assert "county" not in dream_usa.columns
