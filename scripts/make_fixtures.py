"""Build tests/fixtures/ from the full raw files in data/.

The test suite reads from tests/fixtures/ (committed) rather than data/
(gitignored, ~2.6GB), so a fresh clone can run pytest with no downloads.
Small files are copied whole because tests assert their full-file row counts;
the large alpha/nmrc files are trimmed to just the report record numbers the
tests use. Re-run this script after replacing data/ with a newer CMS release,
then update any count/value assertions that the new data invalidates.

Usage: python scripts/make_fixtures.py
"""

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from mihealth.hcris import filter_state, load_rpt  # noqa: E402

DATA = ROOT / "data"
FIXTURES = ROOT / "tests" / "fixtures"

COPY_WHOLE = [
    "SNF10FY2025/SNF10_2025_rpt.csv",
    "HHA20FY2025/HHA20_2025_rpt.csv",
    "HOSP10FY2025/HOSP10_2025_rpt.csv",
    "reference/cbsa_delineation_2023.xlsx",
    "documentation/HOSPITAL2010-DOCUMENTATION/HCRIS_STATE_CODES.csv",
]


def trim(rel_path: str, keep_recs: set[int]) -> None:
    """Write only the rows of a headerless alpha/nmrc file whose first
    column (RPT_REC_NUM) is in keep_recs."""
    src = DATA / rel_path
    dst = FIXTURES / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    with src.open(newline="") as fin, dst.open("w", newline="") as fout:
        writer = csv.writer(fout)
        for row in csv.reader(fin):
            if int(row[0]) in keep_recs:
                writer.writerow(row)
                kept += 1
    print(f"{rel_path}: kept {kept} rows ({dst.stat().st_size:,} bytes)")


def main() -> None:
    for rel in COPY_WHOLE:
        dst = FIXTURES / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DATA / rel, dst)
        print(f"{rel}: copied whole ({dst.stat().st_size:,} bytes)")

    # All Michigan SNF reports — conftest.py hardcodes these 13 rec nums.
    snf_rpt = load_rpt(DATA / "SNF10FY2025" / "SNF10_2025_rpt.csv")
    mi_snf = set(filter_state(snf_rpt, "23")["RPT_REC_NUM"])
    trim("SNF10FY2025/SNF10_2025_alpha.csv", mi_snf)
    trim("SNF10FY2025/SNF10_2025_nmrc.csv", mi_snf)

    # Kingswood -> Henry Ford Behavioral Health (CCN 234011), test_directory.py
    hosp_rpt = load_rpt(DATA / "HOSP10FY2025" / "HOSP10_2025_rpt.csv")
    kingswood = set(hosp_rpt.loc[hosp_rpt["PRVDR_NUM"] == "234011", "RPT_REC_NUM"])
    trim("HOSP10FY2025/HOSP10_2025_alpha.csv", kingswood)

    # Dream USA (600997, test_directory.py) and 609199 (test_hha.py)
    trim("HHA20FY2025/HHA20_2025_alpha.csv", {600997, 609199})

    # Reliable Home Health, the cell-map ground-truth report (test_hha.py)
    trim("HHA20FY2024/HHA20_2024_alpha.csv", {573443})
    trim("HHA20FY2024/HHA20_2024_nmrc.csv", {573443})


if __name__ == "__main__":
    main()
