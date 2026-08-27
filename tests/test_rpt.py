"""Tests for loading HCRIS rpt (report index) files.

Column names and order come from HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt in
data/documentation/ — the raw CSVs have no header row.
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.hcris import filter_state, load_rpt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FILES = {
    "SNF": DATA_DIR / "SNF10FY2025" / "SNF10_2025_rpt.csv",
    "HHA": DATA_DIR / "HHA20FY2025" / "HHA20_2025_rpt.csv",
    "HOSP": DATA_DIR / "HOSP10FY2025" / "HOSP10_2025_rpt.csv",
}
ROW_CNTS = {"SNF": 531, "HOSP": 3279, "HHA": 9058}
# Michigan report counts, verified against the raw files with awk
MI_CNTS = {"SNF": 13, "HOSP": 80, "HHA": 215}
MICHIGAN = "23"


@pytest.fixture(scope="module", params=["SNF", "HHA", "HOSP"])
def subsystem(request) -> str:
    return request.param


@pytest.fixture(scope="module")
def rpt(subsystem) -> pd.DataFrame:
    return load_rpt(FILES[subsystem])


def test_loads_all_rows(rpt, subsystem):
    # wc -l on the raw file: 531 lines, no header
    assert len(rpt) == ROW_CNTS[subsystem]  # 531


def test_has_documented_columns_in_order(rpt):
    assert list(rpt.columns)[0:18] == [
        "RPT_REC_NUM",
        "PRVDR_CTRL_TYPE_CD",
        "PRVDR_NUM",
        "NPI",
        "RPT_STUS_CD",
        "FY_BGN_DT",
        "FY_END_DT",
        "PROC_DT",
        "INITL_RPT_SW",
        "LAST_RPT_SW",
        "TRNSMTL_NUM",
        "FI_NUM",
        "ADR_VNDR_CD",
        "FI_CREAT_DT",
        "UTIL_CD",
        "NPR_DT",
        "SPEC_IND",
        "FI_RCPT_DT",
    ]


def test_has_derived_columns_in_order(rpt):
    assert list(rpt.columns)[18:20] == ["period_days", "is_partial_year"]


def test_provider_number_is_six_char_string(rpt):
    # CCNs are CHAR(6): first two digits are the state code (Michigan = 23).
    # Read as integers, leading zeros vanish and prefix filters break.
    assert rpt["PRVDR_NUM"].str.len().eq(6).all()


def test_fiscal_year_dates_are_datetimes(rpt):
    assert pd.api.types.is_datetime64_any_dtype(rpt["FY_BGN_DT"])
    assert pd.api.types.is_datetime64_any_dtype(rpt["FY_END_DT"])


def test_filter_state_michigan_counts(rpt, subsystem):
    assert len(filter_state(rpt, MICHIGAN)) == MI_CNTS[subsystem]


def test_filter_state_keeps_only_matching_providers(rpt):
    filtered = filter_state(rpt, MICHIGAN)
    assert filtered["PRVDR_NUM"].str.startswith(MICHIGAN).all()


def test_filter_state_preserves_columns(rpt):
    assert list(filter_state(rpt, MICHIGAN).columns) == list(rpt.columns)


def test_filter_state_unknown_state_is_empty_not_error(rpt):
    filtered = filter_state(rpt, "99")
    assert len(filtered) == 0


# Known report periods in the HOSP file, verified against the raw CSV:
#   817596 / 234011  01/01/2025-02/22/2025  53-day stub (pre-sale Kingswood)
#   836485 / 234011  02/23/2025-12/31/2025  312 days (post-sale Kingswood)
#   827702 / 230080  10/01/2024-09/30/2025  full federal fiscal year
@pytest.fixture(scope="module")
def hosp_rpt() -> pd.DataFrame:
    return load_rpt(FILES["HOSP"])


def one_row(rpt: pd.DataFrame, rpt_rec_num: int, column: str):
    """The value of `column` for exactly one report; raises if 0 or 2+ match."""
    return rpt.loc[rpt["RPT_REC_NUM"] == rpt_rec_num, column].item()


def test_period_columns_exist_with_expected_dtypes(rpt):
    assert pd.api.types.is_integer_dtype(rpt["period_days"])
    assert pd.api.types.is_bool_dtype(rpt["is_partial_year"])


def test_period_days_inclusive_of_both_endpoints(hosp_rpt):
    assert one_row(hosp_rpt, 817596, "period_days") == 53
    assert one_row(hosp_rpt, 836485, "period_days") == 312
    assert one_row(hosp_rpt, 827702, "period_days") == 365


def test_partial_year_means_under_360_days(hosp_rpt):
    assert one_row(hosp_rpt, 817596, "is_partial_year")
    assert one_row(hosp_rpt, 836485, "is_partial_year")
    assert not one_row(hosp_rpt, 827702, "is_partial_year")


def test_partial_year_flag_agrees_with_period_days_everywhere(rpt):
    assert (rpt["is_partial_year"] == (rpt["period_days"] < 360)).all()


def test_filter_state_does_not_mutate_input(rpt):
    before = len(rpt)
    filter_state(rpt, MICHIGAN)
    assert len(rpt) == before
