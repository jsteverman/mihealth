"""Tests for loading HCRIS alpha (text values) files, filtered by report set.

Alpha files are large (79MB for hospitals), so load_alpha streams in chunks
and keeps only rows for the requested RPT_REC_NUMs. Ground-truth values below
were verified against the raw SNF CSV with awk/grep.
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.hcris import load_alpha

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SNF_ALPHA = DATA_DIR / "SNF10FY2025" / "SNF10_2025_alpha.csv"

# The 13 Michigan SNF reports in the FY2025 rpt file
MI_SNF_RECS = {
    1434340,
    1448178,
    1448231,
    1448306,
    1448307,
    1448482,
    1448483,
    1448793,
    1448794,
    1449670,
    1449835,
    1449836,
    1450326,
}


@pytest.fixture(scope="module")
def mi_alpha() -> pd.DataFrame:
    return load_alpha(SNF_ALPHA, MI_SNF_RECS)


def test_has_documented_columns_in_order(mi_alpha):
    assert list(mi_alpha.columns) == [
        "RPT_REC_NUM",
        "WKSHT_CD",
        "LINE_NUM",
        "CLMN_NUM",
        "ALPHNMRC_ITM_TXT",
    ]


def test_keeps_exactly_the_requested_reports(mi_alpha):
    assert set(mi_alpha["RPT_REC_NUM"]) == MI_SNF_RECS


def test_row_counts_match_raw_file(mi_alpha):
    # awk join against the raw file: 3713 rows across the 13 reports
    assert len(mi_alpha) == 3713
    # grep -c '^1434340,': 285 rows for this single report
    assert (mi_alpha["RPT_REC_NUM"] == 1434340).sum() == 285


def test_line_and_column_are_zero_padded_strings(mi_alpha):
    # If LINE_NUM/CLMN_NUM were parsed as integers, "00400" would become 400
    # and cell addressing would silently break. NOTE: the data dictionary
    # claims 4-char column numbers for non-hospital forms; the actual files
    # use 5 chars. Trust the data.
    name = mi_alpha.loc[
        (mi_alpha["RPT_REC_NUM"] == 1434340)
        & (mi_alpha["WKSHT_CD"] == "S200001")
        & (mi_alpha["LINE_NUM"] == "00400")
        & (mi_alpha["CLMN_NUM"] == "00100"),
        "ALPHNMRC_ITM_TXT",
    ].item()
    # 2540-10 puts the facility name on S-2 line 4 (line 3 is the county)
    assert name == "THE ORCHARDS AT CANTERBURY ON THE LA"


def test_empty_report_set_gives_empty_frame_with_columns(mi_alpha):
    empty = load_alpha(SNF_ALPHA, set())
    assert len(empty) == 0
    assert list(empty.columns) == list(mi_alpha.columns)
