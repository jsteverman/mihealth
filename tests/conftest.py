"""Shared fixtures for the test suite.

pytest auto-discovers this file; fixtures defined here are available to every
test module without imports. Session scope means each expensive load happens
once per pytest run, not once per file.
"""

from pathlib import Path

import pandas as pd
import pytest

from mihealth.hcris import load_alpha, load_nmrc

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# The 13 Michigan SNF reports in the FY2025 rpt file, verified with awk
_MI_SNF_RECS = {
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


@pytest.fixture(scope="session")
def mi_snf_recs() -> set[int]:
    return set(_MI_SNF_RECS)  # copy, so no test can mutate the original


@pytest.fixture(scope="session")
def snf_alpha_path() -> Path:
    return DATA_DIR / "SNF10FY2025" / "SNF10_2025_alpha.csv"


@pytest.fixture(scope="session")
def snf_nmrc_path() -> Path:
    return DATA_DIR / "SNF10FY2025" / "SNF10_2025_nmrc.csv"


@pytest.fixture(scope="session")
def mi_alpha(snf_alpha_path, mi_snf_recs) -> pd.DataFrame:
    return load_alpha(snf_alpha_path, mi_snf_recs)


@pytest.fixture(scope="session")
def mi_nmrc(snf_nmrc_path, mi_snf_recs) -> pd.DataFrame:
    return load_nmrc(snf_nmrc_path, mi_snf_recs)
