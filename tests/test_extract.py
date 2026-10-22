"""Tests for extract_cells: cell maps in, wide per-report frame out.

A cell map is a dict of friendly name -> (WKSHT_CD, LINE_NUM, CLMN_NUM).
extract_cells(df, cellmap, values_from) returns one row per RPT_REC_NUM
(as the index), one column per map key. Missing cells become NaN; duplicate
cells (same report, same address, twice) raise ValueError.

Form-specific maps are domain data and live in mihealth.forms.
"""

import pandas as pd
import pytest

from mihealth.forms import SNF10_IDENTITY
from mihealth.hcris import extract_cells

# Worksheet G-3 income statement cells on form 2540-10, verified vs raw CSV
SNF10_FINANCE = {
    "net_patient_revenue": ("G300000", "00300", "00100"),
    "net_patient_income": ("G300000", "00500", "00100"),
}


@pytest.fixture(scope="module")
def identity(mi_alpha) -> pd.DataFrame:
    return extract_cells(mi_alpha, SNF10_IDENTITY, values_from="ALPHNMRC_ITM_TXT")


def test_one_row_per_report(identity, mi_snf_recs):
    assert len(identity) == len(mi_snf_recs)
    assert set(identity.index) == mi_snf_recs


def test_index_is_named_rpt_rec_num(identity):
    assert identity.index.name == "RPT_REC_NUM"


def test_columns_are_map_keys_in_map_order(identity):
    assert list(identity.columns) == list(SNF10_IDENTITY)


def test_orchards_identity_row(identity):
    orchards = identity.loc[1434340]
    assert orchards["name"] == "THE ORCHARDS AT CANTERBURY ON THE LA"
    assert orchards["street"] == "5601 HATCHERY ROAD"
    assert orchards["city"] == "WATERFORD"
    assert orchards["state"] == "MI"
    assert orchards["zip"] == "48329"
    assert orchards["county"] == "OAKLAND"


def test_extracts_numeric_values_from_nmrc(mi_nmrc):
    finance = extract_cells(mi_nmrc, SNF10_FINANCE, values_from="ITM_VAL_NUM")
    orchards = finance.loc[1434340]
    assert orchards["net_patient_revenue"] == 2_709_912
    assert orchards["net_patient_income"] == -177_276


# --- Edge cases, on hand-built micro-frames ---------------------------------

TINY_MAP = {
    "name": ("S200001", "00400", "00100"),
    "city": ("S200001", "00200", "00100"),
}


def micro_frame(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["RPT_REC_NUM", "WKSHT_CD", "LINE_NUM", "CLMN_NUM", "ALPHNMRC_ITM_TXT"],
    )


def test_missing_cell_becomes_nan_not_error():
    # Report 2 has a name but no city row at all.
    df = micro_frame(
        [
            (1, "S200001", "00400", "00100", "ALPHA HOUSE"),
            (1, "S200001", "00200", "00100", "DETROIT"),
            (2, "S200001", "00400", "00100", "BETA MANOR"),
        ]
    )
    wide = extract_cells(df, TINY_MAP, values_from="ALPHNMRC_ITM_TXT")
    assert len(wide) == 2
    assert wide.loc[2, "name"] == "BETA MANOR"
    assert pd.isna(wide.loc[2, "city"])


def test_duplicate_cell_raises():
    # Same report, same cell address, two values: our form assumptions are
    # wrong and the engine must say so, not pick one silently.
    df = micro_frame(
        [
            (1, "S200001", "00400", "00100", "ALPHA HOUSE"),
            (1, "S200001", "00400", "00100", "ALPHA HOUSE ANNEX"),
        ]
    )
    with pytest.raises(ValueError):
        extract_cells(df, TINY_MAP, values_from="ALPHNMRC_ITM_TXT")
