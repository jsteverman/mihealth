"""Michigan home health agency extract.

Combines HCRIS 1728-20 cost reports (identity, staffing, finance) across
release years with the CMS POS file (the certified-agency universe), one
row per agency, using the most recent annual-ish cost report per provider.
"""

from pathlib import Path

import pandas as pd

from mihealth.directory import build_directory
from mihealth.forms import (
    HHA20_FINANCE,
    HHA20_HOME_OFFICE,
    HHA20_IDENTITY,
    HHA20_STAFFING,
)
from mihealth.hcris import extract_cells, filter_state, load_alpha, load_nmrc, load_rpt

# A report covering at least this many days counts as "annual" for the
# most-recent-annual-revenue selection.
ANNUAL_MIN_DAYS = 300

POS_KEEP = {
    "prvdr_num": "PRVDR_NUM",
    "fac_name": "pos_name",
    "st_adr": "pos_street",
    "city_name": "pos_city",
    "zip_cd": "pos_zip",
    "orgnl_prtcptn_dt": "pos_first_certified",
    "trmntn_exprtn_dt": "pos_terminated",
    "chow_dt": "pos_ownership_change",
    "rn_cnt": "pos_rn_count",
    "lpn_lvn_cnt": "pos_lpn_count",
}


def pick_annual_report(rpt: pd.DataFrame, min_days: int = ANNUAL_MIN_DAYS) -> pd.DataFrame:
    """One report per provider: prefer annual coverage, then latest FY end.

    A full(ish)-year report from an earlier file beats a more recent stub,
    so 'most recent annual revenue' means what it says. Providers with only
    stubs still surface (latest stub), flagged by is_partial_year.
    """
    ranked = rpt.assign(_annual=rpt["period_days"] >= min_days).sort_values(
        ["_annual", "FY_END_DT", "PROC_DT"]
    )
    return ranked.drop_duplicates("PRVDR_NUM", keep="last").drop(columns="_annual")


def load_mi_hha_reports(data_dir: Path, years: tuple[int, ...] = (2024, 2025)) -> dict:
    """Load Michigan HHA rpt/alpha/nmrc slices for each HCRIS release year."""
    parts = []
    for year in years:
        d = data_dir / f"HHA20FY{year}"
        rpt = filter_state(load_rpt(d / f"HHA20_{year}_rpt.csv"), "23")
        recs = set(rpt["RPT_REC_NUM"])
        parts.append(
            {
                "year": year,
                "rpt": rpt.assign(hcris_year=year),
                "alpha": load_alpha(d / f"HHA20_{year}_alpha.csv", recs),
                "nmrc": load_nmrc(d / f"HHA20_{year}_nmrc.csv", recs),
            }
        )
    return {
        "rpt": pd.concat([p["rpt"] for p in parts], ignore_index=True),
        "alpha": pd.concat([p["alpha"] for p in parts], ignore_index=True),
        "nmrc": pd.concat([p["nmrc"] for p in parts], ignore_index=True),
    }


def load_pos_universe(pos_csv: Path, state: str = "MI") -> pd.DataFrame:
    """All POS-certified HHAs for a state (prvdr_type_id 3 = home health)."""
    pos = pd.read_csv(pos_csv, dtype=str, usecols=["state_cd", "prvdr_type_id", *POS_KEEP])
    pos = pos[(pos["state_cd"] == state) & (pos["prvdr_type_id"] == "3")]
    pos = pos[list(POS_KEEP)].rename(columns=POS_KEEP)
    pos = pos.replace("Not Available", pd.NA)
    return pos.set_index("PRVDR_NUM")


def build_mi_hha_extract(data_dir: Path, pos_csv: Path) -> pd.DataFrame:
    """One row per Michigan HHA: POS identity + latest annual cost report."""
    hcris = load_mi_hha_reports(data_dir)

    picked = pick_annual_report(hcris["rpt"])
    directory = build_directory(picked, hcris["alpha"], HHA20_IDENTITY)
    staffing = extract_cells(hcris["nmrc"], HHA20_STAFFING, values_from="ITM_VAL_NUM")
    finance = extract_cells(hcris["nmrc"], HHA20_FINANCE, values_from="ITM_VAL_NUM")
    home_office = extract_cells(
        hcris["alpha"], HHA20_HOME_OFFICE, values_from="ALPHNMRC_ITM_TXT"
    )
    report = directory.join([staffing, finance, home_office]).join(
        picked.set_index("RPT_REC_NUM")[["hcris_year", "RPT_STUS_CD", "UTIL_CD"]]
    )

    pos = load_pos_universe(pos_csv)
    merged = pos.join(report.reset_index().set_index("PRVDR_NUM"), how="outer")
    merged["has_cost_report"] = merged["RPT_REC_NUM"].notna()
    # Chain organizations file one org-level F-1 on every component's report
    # (e.g. six McLaren CCNs each showing $121.3M). Flag them: revenue for
    # these rows is the filing entity's, NOT the individual agency's.
    merged["f1_shared_across_ccns"] = merged["net_patient_revenue"].notna() & (
        merged.duplicated(
            ["net_patient_revenue", "gross_patient_revenue", "net_income"], keep=False
        )
    )
    merged.index.name = "PRVDR_NUM"
    return merged.sort_index()
