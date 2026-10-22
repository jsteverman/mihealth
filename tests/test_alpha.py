"""Tests for loading HCRIS alpha (text values) files, filtered by report set.

Alpha files are large (79MB for hospitals), so load_alpha streams in chunks
and keeps only rows for the requested RPT_REC_NUMs. Ground-truth values below
were verified against the raw SNF CSV with awk/grep. Shared fixtures
(mi_alpha, mi_snf_recs, snf_alpha_path) live in conftest.py.
"""

from mihealth.hcris import load_alpha


def test_has_documented_columns_in_order(mi_alpha):
    assert list(mi_alpha.columns) == [
        "RPT_REC_NUM",
        "WKSHT_CD",
        "LINE_NUM",
        "CLMN_NUM",
        "ALPHNMRC_ITM_TXT",
    ]


def test_keeps_exactly_the_requested_reports(mi_alpha, mi_snf_recs):
    assert set(mi_alpha["RPT_REC_NUM"]) == mi_snf_recs


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


def test_empty_report_set_gives_empty_frame_with_columns(mi_alpha, snf_alpha_path):
    empty = load_alpha(snf_alpha_path, set())
    assert len(empty) == 0
    assert list(empty.columns) == list(mi_alpha.columns)
