from pathlib import Path

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
    "FI_RCPT_DT": "date",
}

ALPH_COLUMNS = {
    "RPT_REC_NUM": "int64",
    "WKSHT_CD": "str",
    "LINE_NUM": "str",
    "CLMN_NUM": "str",
    "ALPHNMRC_ITM_TXT": "str",
}

def load_rpt(path: str | Path) -> pd.DataFrame:
    dates = [c for c, t in RPT_COLUMNS.items() if t == "date"]
    dtypes = {c: t for c, t in RPT_COLUMNS.items() if t != "date"}
    rpt = pd.read_csv(
        path,
        header=None,
        names=list(RPT_COLUMNS),
        dtype=dtypes,
        parse_dates=dates,
        date_format="%m/%d/%Y",
    )
    rpt["period_days"] = (rpt["FY_END_DT"] - rpt["FY_BGN_DT"]).dt.days + 1
    rpt["is_partial_year"] = rpt["period_days"] < 360
    return rpt


def filter_state(rpt: pd.DataFrame, state: str) -> pd.DataFrame:
    filtered = rpt[rpt["PRVDR_NUM"].str.startswith(state)]
    return filtered

def load_alpha(path: str | Path, rpt_rec_nums: list[str]) -> pd.DataFrame:
    rec_set = set(rpt_rec_nums)
    iter_csv = pd.read_csv(
            path,
            iterator=True,
            chunksize=500_000,
            header=None,
            names=list(ALPH_COLUMNS),
            dtype=ALPH_COLUMNS
            )
    chunks = [chunk[chunk['RPT_REC_NUM'].isin(rec_set)] for chunk in iter_csv]
    df = pd.concat(chunks, ignore_index=True)
    return df
