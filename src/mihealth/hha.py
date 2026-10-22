"""Michigan home health agency extract.

Combines HCRIS 1728-20 cost reports (identity, staffing, finance) across
release years with the CMS POS file (the certified-agency universe), one
row per agency, using the most recent annual-ish cost report per provider.
"""

from pathlib import Path

import pandas as pd

from mihealth.cbsa import load_cbsa_names, name_cbsa_list
from mihealth.directory import build_directory
from mihealth.forms import (
    HHA20_FINANCE,
    HHA20_HOME_OFFICE,
    HHA20_IDENTITY,
    HHA20_STAFFING,
)
from mihealth.hcris import (
    extract_cells,
    extract_line_values,
    filter_state,
    load_alpha,
    load_nmrc,
    load_rpt,
)

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


def assess_rn_wage_quality(
    staff: pd.DataFrame,
    ratio_band: tuple[float, float] = (0.7, 1.3),
    wage_band: tuple[float, float] = (15.0, 90.0),
) -> pd.Series:
    """Flag filed RN average hourly wages that can't be trusted.

    Per-visit-paid workforces have no real payroll hours, so the S-3 Part V
    paid-hours denominator is often fiction and the computed wage inflates
    (observed: $198/hr). Two checks, both required for 'ok':

    1. Internal: rn_paid_hours / (rn_ftes * 2080) within ratio_band. This is
       necessary but NOT sufficient - the form derives FTEs as hours/2080, so
       many filers' two numbers agree because they share the same fiction
       (observed: a 'consistent' $281/hr).
    2. External: the wage itself within wage_band. Loaded cost (salary +
       fringes) per hour for Michigan employee RNs plausibly spans ~$15-90
       (BLS MI RN mean is ~$39 unloaded); outside that is per-visit math or
       misfiled dollars, not a wage.

    Wage present but no usable FTEs/hours -> 'unverifiable'; no wage -> NA.
    """
    expected_hours = (staff["rn_ftes"] * 2080).where(staff["rn_ftes"] > 0)
    ratio = staff["rn_paid_hours"] / expected_hours
    has_wage = staff["rn_avg_hourly_wage"].notna()
    plausible = staff["rn_avg_hourly_wage"].between(*wage_band)

    quality = pd.Series(pd.NA, index=staff.index, dtype="object")
    quality[has_wage] = "unverifiable"
    quality[has_wage & ~plausible] = "suspect"
    quality[has_wage & ratio.notna() & ~ratio.between(*ratio_band)] = "suspect"
    quality[has_wage & plausible & ratio.between(*ratio_band)] = "ok"
    return quality.rename("rn_wage_quality")


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
    staffing["rn_wage_quality"] = assess_rn_wage_quality(staffing)
    finance = extract_cells(hcris["nmrc"], HHA20_FINANCE, values_from="ITM_VAL_NUM")
    home_office = extract_cells(
        hcris["alpha"], HHA20_HOME_OFFICE, values_from="ALPHNMRC_ITM_TXT"
    )
    # S-3 Part III line 35 (subscripted): CBSAs where Medicare services were
    # actually delivered - the operating footprint, vs the office address.
    service_area = extract_line_values(
        hcris["alpha"], "S300000", "035", "00100", values_from="ALPHNMRC_ITM_TXT"
    ).rename("service_area_cbsas")
    report = directory.join([staffing, finance, home_office, service_area]).join(
        picked.set_index("RPT_REC_NUM")[["hcris_year", "RPT_STUS_CD", "UTIL_CD"]]
    )

    cbsa_names = load_cbsa_names(
        data_dir / "reference" / "cbsa_delineation_2023.xlsx",
        data_dir / "documentation" / "HOSPITAL2010-DOCUMENTATION" / "HCRIS_STATE_CODES.csv",
    )
    report["service_area_names"] = report["service_area_cbsas"].map(
        lambda codes: name_cbsa_list(codes, cbsa_names), na_action="ignore"
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
