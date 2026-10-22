"""Build the Michigan HHA extract and write it to output/mi_hha_extract.csv.

Usage: uv run python scripts/build_hha_extract.py
"""

from pathlib import Path

from mihealth.hha import build_mi_hha_extract

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "mi_hha_extract.csv"


def main() -> None:
    extract = build_mi_hha_extract(
        data_dir=ROOT / "data",
        pos_csv=ROOT / "data" / "POS" / "POS_iQIES_Q2_2026.csv",
    )
    OUT.parent.mkdir(exist_ok=True)
    extract.to_csv(OUT)

    active = extract["pos_terminated"].isna()
    print(f"wrote {OUT} ({len(extract)} agencies)")
    print(f"  active per POS:            {int(active.sum())}")
    print(f"  terminated per POS:        {int((~active).sum())}")
    print(f"  with cost report:          {int(extract['has_cost_report'].sum())}")
    print(
        f"  active with cost report:   "
        f"{int((active & extract['has_cost_report']).sum())}"
    )
    annual = extract["period_days"] >= 300
    print(f"  cost report is annual:     {int(annual.sum())}")
    has_rev = extract["net_patient_revenue"].notna()
    shared = extract["f1_shared_across_ccns"]
    solo_rev = extract.loc[has_rev & ~shared, "net_patient_revenue"].sum()
    print(f"  with revenue reported:     {int(has_rev.sum())}")
    print(f"  org-level (shared) F-1s:   {int(shared.sum())}")
    print(f"  net patient revenue, agency-level filers only: ${solo_rev:,.0f}")


if __name__ == "__main__":
    main()
