"""Tests for loading HCRIS rpt (report index) files.

Column names and order come from HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt in
data/documentation/ — the raw CSVs have no header row.
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.hcris import load_rpt

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FILES = {
        "SNF": DATA_DIR / "SNF10FY2025" / "SNF10_2025_rpt.csv",
        "HHA": DATA_DIR / "HHA20FY2025" / "HHA20_2025_rpt.csv",
        "HOSP": DATA_DIR / "HOSP10FY2025" / "HOSP10_2025_rpt.csv"
        }
ROW_CNTS = { "SNF": 531, "HOSP": 3279, "HHA": 9058 }

@pytest.fixture(scope="module", params=["SNF", "HHA", "HOSP"])
def subsystem(request) -> str:
    return request.param

@pytest.fixture(scope="module")
def rpt(subsystem) -> pd.DataFrame:
    return load_rpt(FILES[subsystem])


def test_loads_all_rows(rpt, subsystem):
    # wc -l on the raw file: 531 lines, no header
    assert len(rpt) == ROW_CNTS[subsystem] #531


def test_has_documented_columns_in_order(rpt):
    assert list(rpt.columns) == [
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


def test_provider_number_is_six_char_string(rpt):
    # CCNs are CHAR(6): first two digits are the state code (Michigan = 23).
    # Read as integers, leading zeros vanish and prefix filters break.
    assert rpt["PRVDR_NUM"].str.len().eq(6).all()


def test_fiscal_year_dates_are_datetimes(rpt):
    assert pd.api.types.is_datetime64_any_dtype(rpt["FY_BGN_DT"])
    assert pd.api.types.is_datetime64_any_dtype(rpt["FY_END_DT"])
