"""Tests for the HHA cell maps and annual-report selection.

Cell-map ground truth: report 573443 (provider 239113, Reliable Home Health,
Farmington Hills, CY2024 full year, full Medicare utilization) in the FY2024
file, verified against the raw CSV and the CMS-1728-20 form. Cross-checks:
Worksheet A line 100 col 6 total ($211,476) ties to F-1 line 17, and
F-1 line 3 - line 17 = line 18 ($238,627 - $211,476 = $27,151).
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.forms import HHA20_FINANCE, HHA20_STAFFING
from mihealth.hcris import extract_cells, load_nmrc
from mihealth.hha import pick_annual_report

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RELIABLE = 573443


@pytest.fixture(scope="module")
def reliable_nmrc() -> pd.DataFrame:
    return load_nmrc(DATA_DIR / "HHA20FY2024" / "HHA20_2024_nmrc.csv", {RELIABLE})


def test_finance_cells(reliable_nmrc):
    fin = extract_cells(reliable_nmrc, HHA20_FINANCE, values_from="ITM_VAL_NUM")
    row = fin.loc[RELIABLE]
    assert row["net_patient_revenue"] == 238_627
    assert row["total_operating_expenses"] == 211_476
    assert row["net_patient_income"] == 27_151
    assert row["net_income"] == 27_156
    assert row["total_salaries"] == 115_970
    assert row["employee_benefits"] == 9_042
    assert row["contracted_services"] == 27_536
    assert row["total_costs"] == 211_476


def test_staffing_cells(reliable_nmrc):
    staff = extract_cells(reliable_nmrc, HHA20_STAFFING, values_from="ITM_VAL_NUM")
    row = staff.loc[RELIABLE]
    assert row["total_visits"] == 1_169
    assert row["unduplicated_census"] == 58
    assert row["aide_hours"] == 11
    assert row["rn_ftes"] == 0.06
    assert row["rn_avg_hourly_wage"] == pytest.approx(48.52)
    assert row["nursing_paid_hours"] == pytest.approx(114.53)


def test_home_office_cells():
    from mihealth.forms import HHA20_HOME_OFFICE
    from mihealth.hcris import load_alpha

    # Beaumont ASHN LLC (237112), FY2025 file: chain-managed JV
    alpha = load_alpha(DATA_DIR / "HHA20FY2025" / "HHA20_2025_alpha.csv", {609199})
    ho = extract_cells(alpha, HHA20_HOME_OFFICE, values_from="ALPHNMRC_ITM_TXT")
    row = ho.loc[609199]
    assert row["in_chain"] == "Y"
    assert row["home_office_name"] == "ALTERNATE SOLUTIONS HEALTH NETWORK"
    assert row["home_office_chain_id"] == "HB0110"
    assert row["home_office_state"] == "OH"


def test_service_area_cbsas():
    from mihealth.hcris import extract_line_values, load_alpha

    alpha = load_alpha(DATA_DIR / "HHA20FY2024" / "HHA20_2024_alpha.csv", {RELIABLE})
    areas = extract_line_values(
        alpha, "S300000", "035", "00100", values_from="ALPHNMRC_ITM_TXT"
    )
    # Farmington Hills office; served Detroit-Dearborn-Livonia (19804) and
    # Warren-Troy-Farmington Hills (47664) metro divisions, in line order.
    assert areas.loc[RELIABLE] == "19804|47664"


# --- pick_annual_report, on a micro-frame ------------------------------------


def micro_rpt(rows: list[tuple]) -> pd.DataFrame:
    df = pd.DataFrame(
        rows, columns=["RPT_REC_NUM", "PRVDR_NUM", "FY_END_DT", "PROC_DT", "period_days"]
    )
    df["FY_END_DT"] = pd.to_datetime(df["FY_END_DT"])
    df["PROC_DT"] = pd.to_datetime(df["PROC_DT"])
    return df


def test_annual_report_beats_more_recent_stub():
    rpt = micro_rpt(
        [
            (1, "237001", "2024-12-31", "2025-03-01", 366),  # full CY2024
            (2, "237001", "2025-03-31", "2025-06-01", 90),  # newer stub
        ]
    )
    picked = pick_annual_report(rpt)
    assert picked["RPT_REC_NUM"].tolist() == [1]


def test_latest_annual_wins_among_annuals():
    rpt = micro_rpt(
        [
            (1, "237001", "2023-12-31", "2024-03-01", 365),
            (2, "237001", "2024-12-31", "2025-03-01", 366),
        ]
    )
    picked = pick_annual_report(rpt)
    assert picked["RPT_REC_NUM"].tolist() == [2]


def test_only_stubs_returns_latest_stub():
    rpt = micro_rpt(
        [
            (1, "237001", "2024-06-30", "2024-09-01", 120),
            (2, "237001", "2024-12-31", "2025-03-01", 150),
            (3, "237002", "2024-12-31", "2025-03-01", 365),
        ]
    )
    picked = pick_annual_report(rpt).set_index("PRVDR_NUM")
    assert picked.loc["237001", "RPT_REC_NUM"] == 2
    assert picked.loc["237002", "RPT_REC_NUM"] == 3


def test_one_row_per_provider():
    rpt = micro_rpt(
        [
            (1, "237001", "2024-12-31", "2025-03-01", 366),
            (2, "237001", "2025-03-31", "2025-06-01", 90),
            (3, "237002", "2024-12-31", "2025-03-01", 365),
        ]
    )
    assert pick_annual_report(rpt)["PRVDR_NUM"].is_unique
