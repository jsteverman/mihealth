import pandas as pd

RPT_COLUMNS = {
    "RPT_REC_NUM": "int64",
    "PRVDR_CTRL_TYPE_CD": "str",
    "PRVDR_NUM": "str",
    "NPI": "Int64",
    "RPT_STUS_CD": "str",
    "FY_BGN_DT": "date",
    "FY_END_DT": "date",
    "PROC_DT": "date",
    "INITL_RPT_SW": "str",
    "LAST_RPT_SW": "str",
    "TRNSMTL_NUM": "str",
    "FI_NUM": "str",
    "ADR_VNDR_CD": "str",
    "FI_CREAT_DT": "date",
    "UTIL_CD": "str",
    "NPR_DT": "date",
    "SPEC_IND": "str",
    "FI_RCPT_DT": "date"
    }

def load_rpt(rpt_full_path: str) -> pd.DataFrame:
    dates = [c for c, t in RPT_COLUMNS.items() if t == "date"]
    dtypes = {c: t for c, t in RPT_COLUMNS.items() if t != "date"}
    return pd.read_csv(
            rpt_full_path, 
            header=None,
            names=list(RPT_COLUMNS),
            dtype=dtypes,
            parse_dates=dates)


