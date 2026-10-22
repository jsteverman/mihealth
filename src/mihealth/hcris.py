from collections.abc import Iterable
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

NMRC_COLUMNS = {
    "RPT_REC_NUM": "int64",
    "WKSHT_CD": "str",
    "LINE_NUM": "str",
    "CLMN_NUM": "str",
    "ITM_VAL_NUM": "float64",
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


def _load_filtered(
    path: str | Path, columns: dict[str, str], rpt_rec_nums: Iterable[int]
) -> pd.DataFrame:
    rec_set = set(rpt_rec_nums)
    iter_csv = pd.read_csv(
        path,
        iterator=True,
        chunksize=500_000,
        header=None,
        names=list(columns),
        dtype=columns,
    )
    chunks = [chunk[chunk["RPT_REC_NUM"].isin(rec_set)] for chunk in iter_csv]
    df = pd.concat(chunks, ignore_index=True)
    return df


def extract_cells(
    df: pd.DataFrame, cellmap: dict[str, tuple[str, str, str]], values_from: str
) -> pd.DataFrame:
    """One row per RPT_REC_NUM, one column per cellmap key.

    Cells absent from df come back as NaN. Duplicate cells (same report,
    same address, more than once) mean our form assumptions are wrong:
    raise rather than silently pick one.
    """
    fields = []
    for field, (wksht, line, clmn) in cellmap.items():
        mask = (
            (df["WKSHT_CD"] == wksht)
            & (df["LINE_NUM"] == line)
            & (df["CLMN_NUM"] == clmn)
        )
        values = df.loc[mask].set_index("RPT_REC_NUM")[values_from]
        if values.index.has_duplicates:
            raise ValueError(f"duplicate cells for {field!r} at {(wksht, line, clmn)}")
        fields.append(values.rename(field))
    return pd.concat(fields, axis=1)


def load_alpha(path: str | Path, rpt_rec_nums: Iterable[int]) -> pd.DataFrame:
    return _load_filtered(path, ALPH_COLUMNS, rpt_rec_nums)


def load_nmrc(path: str | Path, rpt_rec_nums: Iterable[int]) -> pd.DataFrame:
    return _load_filtered(path, NMRC_COLUMNS, rpt_rec_nums)

