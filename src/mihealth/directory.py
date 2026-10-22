"""Facility directory: one row per cost report, identity and ownership attached.

This is a report-level table by design — providers with multiple reports in a
year (e.g. a change of ownership) appear once per report. Collapsing to one
row per facility is an analysis-time decision, not made here.
"""

import pandas as pd

from mihealth.forms import CONTROL_CATEGORIES, CONTROL_TYPES
from mihealth.hcris import extract_cells

RPT_KEEP = [
    "RPT_REC_NUM",
    "PRVDR_NUM",
    "PRVDR_CTRL_TYPE_CD",
    "FY_BGN_DT",
    "FY_END_DT",
    "period_days",
    "is_partial_year",
]


def build_directory(
    rpt: pd.DataFrame,
    alpha: pd.DataFrame,
    identity_map: dict[str, tuple[str, str, str]],
) -> pd.DataFrame:
    """Join rpt-level facts with S-2 identity cells, indexed by RPT_REC_NUM."""
    identity = extract_cells(alpha, identity_map, values_from="ALPHNMRC_ITM_TXT")
    directory = rpt[RPT_KEEP].set_index("RPT_REC_NUM").join(identity)
    directory["ownership"] = directory["PRVDR_CTRL_TYPE_CD"].map(CONTROL_TYPES)
    directory["ownership_category"] = directory["PRVDR_CTRL_TYPE_CD"].map(
        CONTROL_CATEGORIES
    )
    return directory
