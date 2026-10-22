"""CBSA code -> name lookup.

Two sources: the Census delineation file (CBSA codes and metropolitan
division codes - cost reports use division codes where they exist, e.g.
19804 Detroit-Dearborn-Livonia inside CBSA 19820), and the HCRIS SSA state
code table for CMS's rural pseudo-codes (999xx = statewide rural, where xx
is the SSA state code: 99923 = rural Michigan).
"""

from pathlib import Path

import pandas as pd


def load_cbsa_names(delineation_xlsx: Path, state_codes_csv: Path) -> dict[str, str]:
    d = pd.read_excel(delineation_xlsx, skiprows=2, dtype=str)
    names: dict[str, str] = {}
    cbsa = d[["CBSA Code", "CBSA Title"]].dropna().drop_duplicates()
    names.update(zip(cbsa["CBSA Code"], cbsa["CBSA Title"]))
    div = (
        d[["Metropolitan Division Code", "Metropolitan Division Title"]]
        .dropna()
        .drop_duplicates()
    )
    names.update(zip(div["Metropolitan Division Code"], div["Metropolitan Division Title"]))

    states = pd.read_csv(state_codes_csv, dtype=str)
    for _, row in states.iterrows():
        names[f"999{row['Ssa_State_Cd']}"] = f"Rural {row['State_Name'].strip()}"
    return names


def name_cbsa_list(codes: str, names: dict[str, str], sep: str = "|") -> str:
    """'19804|99923' -> 'Detroit-Dearborn-Livonia, MI|Rural Michigan'.

    Unknown codes pass through unchanged rather than vanish.
    """
    return sep.join(names.get(c, c) for c in codes.split(sep))
