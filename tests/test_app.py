"""Smoke test: the Streamlit explorer renders without raising.

AppTest executes app.py top-to-bottom headlessly (no browser), so any
exception in the script - bad column name, NaN formatting crash - fails here
instead of on first click. Requires output/mi_hha_extract.csv to exist.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    not (ROOT / "output" / "mi_hha_extract.csv").exists(),
    reason="run scripts/build_hha_extract.py first",
)


def test_app_renders_without_exception():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert not at.exception
    # the four headline metrics rendered
    assert len(at.metric) >= 4


def test_app_filters_rerun_cleanly():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    at.sidebar.radio[0].set_value("All").run()
    assert not at.exception
    at.sidebar.text_input[0].set_value("Detroit").run()
    assert not at.exception
