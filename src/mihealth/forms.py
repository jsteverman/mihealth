SNF10_IDENTITY = {
  "name":   ("S200001", "00400", "00100"),
  "street": ("S200001", "00100", "00100"),
  "city":   ("S200001", "00200", "00100"),
  "state":  ("S200001", "00200", "00200"),
  "zip":    ("S200001", "00200", "00300"),
  "county": ("S200001", "00300", "00100"),
}

HOSP10_IDENTITY = {
    "name": ("S200001", "00300", "00100"),
    "street": ("S200001", "00100", "00100"),
    "city": ("S200001", "00200", "00100"),
    "state": ("S200001", "00200", "00200"),
    "zip": ("S200001", "00200", "00300"),
    "county": ("S200001", "00200", "00400"),
}

# The 1728-20 reports no county on Worksheet S-2
HHA20_IDENTITY = {
    "name": ("S200001", "00300", "00100"),
    "street": ("S200001", "00100", "00100"),
    "city": ("S200001", "00200", "00100"),
    "state": ("S200001", "00200", "00200"),
    "zip": ("S200001", "00200", "00300"),
}

# 1728-20 S-2 home office / chain organization fields (lines 16-17),
# verified against report 609199 (Beaumont ASHN LLC -> Alternate Solutions
# Health Network, Kettering OH, chain id HB0110).
HHA20_HOME_OFFICE = {
    "in_chain": ("S200001", "01600", "00100"),
    "home_office_name": ("S200001", "01700", "00100"),
    "home_office_chain_id": ("S200001", "01700", "00200"),
    "home_office_city": ("S200001", "01700", "00500"),
    "home_office_state": ("S200001", "01700", "00600"),
}

# 1728-20 statistics, verified against the form (PRM Part II ch. 47, 4795)
# and against report 573443 in the FY2024 file.
# S-3 Part I: visits data. Cols: 1 Medicare, 3 Medicaid, 7 total visits,
#   8 total patient census. Line 11 = total visits, 12 = aide hours,
#   13 = unduplicated census.
# S-3 Part II: FTEs. Cols: 1 staff, 2 contract, 3 total. Lines 19 RN,
#   20 LPN, 32 home health aide.
# S-3 Part V: direct care expenditures. Cols: 1 salaries, 2 fringes,
#   3 adjusted salaries, 4 paid hours, 5 average hourly wage. Employee
#   lines: 2 RN, 3 LPN, 4 total nursing; contract lines: 15 RN, 17 total.
HHA20_STAFFING = {
    "total_visits": ("S300000", "01100", "00700"),
    "medicare_visits": ("S300000", "01100", "00100"),
    "unduplicated_census": ("S300000", "01300", "00800"),
    "aide_hours": ("S300000", "01200", "00700"),
    "rn_ftes": ("S300000", "01900", "00300"),
    "lpn_ftes": ("S300000", "02000", "00300"),
    "aide_ftes": ("S300000", "03200", "00300"),
    "rn_avg_hourly_wage": ("S300005", "00200", "00500"),
    "rn_paid_hours": ("S300005", "00200", "00400"),
    "lpn_avg_hourly_wage": ("S300005", "00300", "00500"),
    "nursing_paid_hours": ("S300005", "00400", "00400"),
    "contract_rn_avg_hourly_wage": ("S300005", "01500", "00500"),
    "contract_nursing_paid_hours": ("S300005", "01700", "00400"),
}

# 1728-20 financials.
# F-1: statement of revenues & expenses. Revenue lines 1-3 use cols
#   1 Medicare / 2 Medicaid / 3 other / 4 total; expense and income lines
#   use a 2-column layout (detail in col 1, totals in col 2).
# Worksheet A line 100: expense totals by type. Cols: 1 salaries,
#   2 benefits, 4 contracted services, 6 total.
HHA20_FINANCE = {
    "gross_patient_revenue": ("F100000", "00100", "00400"),
    "net_patient_revenue": ("F100000", "00300", "00400"),
    "medicare_net_revenue": ("F100000", "00300", "00100"),
    "medicaid_net_revenue": ("F100000", "00300", "00200"),
    "total_operating_expenses": ("F100000", "01700", "00200"),
    "net_patient_income": ("F100000", "01800", "00200"),
    "net_income": ("F100000", "03300", "00200"),
    "total_salaries": ("A000000", "10000", "00100"),
    "employee_benefits": ("A000000", "10000", "00200"),
    "contracted_services": ("A000000", "10000", "00400"),
    "total_costs": ("A000000", "10000", "00600"),
}

# PRVDR_CTRL_TYPE_CD, per Table 3A of the cost report specifications.
# Blank/unreported codes exist in the data (e.g. HHA 239084) and map to NaN.
CONTROL_TYPES = {
    "1": "Voluntary Nonprofit, Church",
    "2": "Voluntary Nonprofit, Other",
    "3": "Proprietary, Individual",
    "4": "Proprietary, Corporation",
    "5": "Proprietary, Partnership",
    "6": "Proprietary, Other",
    "7": "Governmental, Federal",
    "8": "Governmental, City-County",
    "9": "Governmental, County",
    "10": "Governmental, State",
    "11": "Governmental, Hospital District",
    "12": "Governmental, City",
    "13": "Governmental, Other",
}

CONTROL_CATEGORIES = (
    dict.fromkeys(["1", "2"], "nonprofit")
    | dict.fromkeys(["3", "4", "5", "6"], "for-profit")
    | dict.fromkeys(["7", "8", "9", "10", "11", "12", "13"], "government")
)


