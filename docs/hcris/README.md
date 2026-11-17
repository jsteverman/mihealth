# HCRIS reference documentation

Public-domain CMS reference material for the cost report data in this repo.
The per-form directories are the extracted `*-DOCUMENTATION.zip` files that
ship alongside each HCRIS release on
[cms.gov](https://www.cms.gov/data-research/statistics-trends-reports/cost-reports):

- `HCRIS_DataDictionary.csv` — column layouts for the headerless rpt/alpha/nmrc
  CSVs (the source of the column names in `src/mihealth/hcris.py`)
- `HCRIS_TABLE_DESCRIPTIONS _AND_SQL.txt` — table-level descriptions
- `*_README.txt`, `HCRIS_Data_model.pdf` — how the files relate
- crosswalk files (SNF, hospital) — every worksheet/line/column field on the form

The `form-CMS-*` subdirectories hold the official form instructions from the
Medicare Provider Reimbursement Manual, Part 2 (Pub. 15-2) — the ground truth
for what each worksheet cell means, used to verify the cell maps in
`src/mihealth/forms.py`:

- `HHA20/form-CMS-1728-20/` — [Chapter 47, Transmittal 7](https://www.cms.gov/files/zip/chapter-47-t-7-home-health-agency-cost-report-form-cms-1728-20.zip):
  instructions (`R7P247i.pdf`) and form worksheets (`R7P247f.pdf`)
- `SNF10/form-CMS-2540-10/` — [Chapter 41, Transmittal 11](https://www.cms.gov/regulations-and-guidance/guidance/manuals/downloads/p152_41.zip),
  March 2025: instructions (`R11P241i.docx`) and form worksheets
  (`R11P241f.xlsx`, one tab per worksheet)

Downloaded November 2026 from the
[Pub. 15-2 manual page](https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Paper-Based-Manuals-Items/CMS021935).
