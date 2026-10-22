"""Download the non-HCRIS inputs the pipeline depends on.

data/ is gitignored, so a fresh clone bootstraps with:
    uv run python scripts/fetch_reference_data.py

Already-downloaded files are skipped; delete a file to re-fetch it.

The HCRIS cost report files themselves are manual downloads (large, and
grouped by form/year) from:
    https://www.cms.gov/data-research/statistics-trends-reports/cost-reports
unzipped into data/<FORM>FY<YEAR>/ (e.g. data/HHA20FY2024/).
"""

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCES = {
    # Census CBSA/metro-division delineation (code -> name lookup)
    "data/reference/cbsa_delineation_2023.xlsx": (
        "https://www2.census.gov/programs-surveys/metro-micro/geographies/"
        "reference-files/2023/delineation-files/list1_2023.xlsx"
    ),
    # CMS Provider of Services file, iQIES (HHAs, hospices). Updated
    # quarterly - find the current release under "Provider of Services File -
    # Internet Quality Improvement and Evaluation System" at
    # https://data.cms.gov (and update this URL when refreshing).
    "data/POS/POS_iQIES_Q2_2026.csv": (
        "https://data.cms.gov/sites/default/files/2026-08/"
        "9f345e2d-5199-4630-a08b-9b45581a9a2a/POS_iQIES.DATA.Q2_2026.csv"
    ),
}


def main() -> None:
    for rel_path, url in SOURCES.items():
        dest = ROOT / rel_path
        if dest.exists():
            print(f"have    {rel_path}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetch   {rel_path}")
        urllib.request.urlretrieve(url, dest)
        print(f"  done  {dest.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
