"""Tests for loading HCRIS nmrc (numeric values) files, filtered by report set.

Same chunked-and-filtered contract as load_alpha; the value column is numeric.
Ground truth verified against the raw SNF CSV with awk/grep. Shared fixtures
(mi_nmrc, mi_snf_recs, snf_nmrc_path) live in conftest.py.
"""

import pandas as pd

from mihealth.hcris import load_nmrc


def one_cell(nmrc: pd.DataFrame, rec: int, wksht: str, line: str, clmn: str) -> float:
    return nmrc.loc[
        (nmrc["RPT_REC_NUM"] == rec)
        & (nmrc["WKSHT_CD"] == wksht)
        & (nmrc["LINE_NUM"] == line)
        & (nmrc["CLMN_NUM"] == clmn),
        "ITM_VAL_NUM",
    ].item()


def test_has_documented_columns_in_order(mi_nmrc):
    assert list(mi_nmrc.columns) == [
        "RPT_REC_NUM",
        "WKSHT_CD",
        "LINE_NUM",
        "CLMN_NUM",
        "ITM_VAL_NUM",
    ]


def test_keeps_exactly_the_requested_reports(mi_nmrc, mi_snf_recs):
    assert set(mi_nmrc["RPT_REC_NUM"]) == mi_snf_recs


def test_row_counts_match_raw_file(mi_nmrc):
    # awk join against the raw file: 11871 rows across the 13 reports
    assert len(mi_nmrc) == 11871
    # grep -c '^1434340,': 892 rows for this single report
    assert (mi_nmrc["RPT_REC_NUM"] == 1434340).sum() == 892


def test_values_are_numeric(mi_nmrc):
    assert pd.api.types.is_float_dtype(mi_nmrc["ITM_VAL_NUM"])


def test_known_g3_cells_including_negative(mi_nmrc):
    # The Orchards at Canterbury (1434340), Worksheet G-3, column 1:
    # line 3 = net patient revenue, line 5 = net income from patient care.
    assert one_cell(mi_nmrc, 1434340, "G300000", "00300", "00100") == 2_709_912
    assert one_cell(mi_nmrc, 1434340, "G300000", "00500", "00100") == -177_276


def test_empty_report_set_gives_empty_frame_with_columns(mi_nmrc, snf_nmrc_path):
    empty = load_nmrc(snf_nmrc_path, set())
    assert len(empty) == 0
    assert list(empty.columns) == list(mi_nmrc.columns)
