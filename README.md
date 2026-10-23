# mihealth — Michigan Healthcare Employer Data

A tested Python pipeline and interactive explorer for CMS cost report data on
Michigan healthcare facilities, currently focused on **home health agencies**:
who they are, who operates them, where they work, what they earn and spend.

**Live explorer:** _link added after deploy_ · built with
[Streamlit](https://streamlit.io), data committed at `output/mi_hha_extract.csv`.

## What's in the dataset

One row per Michigan home health CCN (962 agencies — the full certified
universe, active and terminated), combining:

- **CMS Provider of Services file** (iQIES, Q2 2026): name, address,
  certification/termination/ownership-change dates
- **CMS HCRIS cost reports** (form 1728-20, FY2024–FY2025 releases): each
  agency's most recent annual-coverage report — ownership type, FTEs by
  discipline, RN/LPN average hourly wages, visits, census, revenue, expenses,
  net income, home-office (chain) identity, and self-reported service-area
  CBSAs, named via the Census delineation file

## Findings so far

- **Two-thirds of Michigan's certified HHA licenses are terminated** (599 of
  962) — the live industry is 363 agencies.
- **Chains deliver ~47% of reported visits** while being only 47 of 335
  filers; the largest operators (Elara Caring, Alternate Solutions Health
  Network, Ascension-affiliated JVs) are headquartered out of state.
- **The nonprofit-brand / for-profit-operator joint venture is a recurring
  structure**: e.g. "Beaumont Home Health" is BEAUMONT ASHN LLC, a
  proprietary partnership whose home office is Alternate Solutions Health
  Network (Kettering, OH).
- **Corroborated loaded RN wages**: median $46.97/hr; nonprofit agencies'
  median runs ~$8/hr above for-profits ($53.19 vs $45.46).
- **A third of active filers are financially invisible**: low/no-Medicare
  utilization filers (largely Medicaid/private-duty businesses) file skeleton
  reports with no revenue statement — HCRIS systematically under-sees the
  Medicaid-heavy, low-wage end of home care.

## Methodology notes (read before quoting numbers)

- "Most recent annual revenue" prefers a report covering ≥300 days over a
  newer stub; partial periods are flagged (`is_partial_year`), never
  annualized silently.
- Chain organizations sometimes file one **org-level income statement on
  every component CCN's report** (all six McLaren CCNs show identical
  $121.3M revenue). Flagged as `f1_shared_across_ccns`; costs, salaries and
  visits remain agency-level.
- Filed RN average hourly wages are only trusted when **internally
  consistent** (paid hours ≈ FTEs × 2080) **and plausible** ($15–90/hr
  loaded): per-visit-paid workforces report fictional hours, and the form's
  FTE field is often derived from those same hours (`rn_wage_quality`).
- Service areas are as-filed (S-3 Part III) and occasionally reflect a parent
  chain's footprint rather than the CCN's.
- All data is as filed with CMS, mostly as-submitted (pre-audit).

## Repo tour

    src/mihealth/
      hcris.py      generic HCRIS loaders (chunked, report-set-filtered) and
                    the cell-map extraction engine
      forms.py      verified worksheet cell addresses per CMS form (domain
                    knowledge as data, checked against the official forms)
      directory.py  facility directory with ownership decoding
      cbsa.py       CBSA/metro-division/rural-code -> name lookup
      hha.py        the Michigan HHA extract build
    scripts/        build_hha_extract.py, fetch_reference_data.py
    tests/          76 pytest tests: ground truth verified against raw CSVs
                    and CMS form PDFs; Streamlit smoke tests via AppTest
    app.py          the explorer

## Running locally

```bash
uv sync
uv run streamlit run app.py          # uses the committed extract CSV
uv run pytest                        # full-data tests need the raw files:
uv run python scripts/fetch_reference_data.py   # POS + Census inputs
# HCRIS raw files (manual, ~600MB): see scripts/fetch_reference_data.py
uv run python scripts/build_hha_extract.py      # rebuild the extract
```

## Data sources

- [CMS HCRIS cost reports](https://www.cms.gov/data-research/statistics-trends-reports/cost-reports) (HHA form 1728-20; FY2024/FY2025 files, July 2025 release)
- [CMS Provider of Services file](https://data.cms.gov) (iQIES, Q2 2026)
- [Census CBSA delineation files](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html) (2023)

All source data is public-domain U.S. federal data about Medicare-certified
facilities; no individual-level data is present.
