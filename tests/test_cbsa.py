"""Tests for the CBSA code -> name lookup."""

from pathlib import Path

import pytest

from mihealth.cbsa import load_cbsa_names, name_cbsa_list

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def names() -> dict[str, str]:
    return load_cbsa_names(
        DATA_DIR / "reference" / "cbsa_delineation_2023.xlsx",
        DATA_DIR
        / "documentation"
        / "HOSPITAL2010-DOCUMENTATION"
        / "HCRIS_STATE_CODES.csv",
    )


def test_metro_division_codes_resolve(names):
    assert names["19804"] == "Detroit-Dearborn-Livonia, MI"
    assert names["47664"] == "Warren-Troy-Farmington Hills, MI"


def test_parent_cbsa_codes_resolve(names):
    assert names["19820"] == "Detroit-Warren-Dearborn, MI"
    assert names["24340"] == "Grand Rapids-Wyoming-Kentwood, MI"


def test_cms_rural_pseudocodes_resolve(names):
    assert names["99923"] == "Rural Michigan"
    assert names["99936"] == "Rural Ohio"


def test_name_cbsa_list_joins_and_passes_unknowns_through(names):
    assert (
        name_cbsa_list("19804|99923|00000", names)
        == "Detroit-Dearborn-Livonia, MI|Rural Michigan|00000"
    )
