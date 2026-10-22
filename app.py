"""Michigan Home Health explorer.

Run with: uv run streamlit run app.py
Data: output/mi_hha_extract.csv (build with scripts/build_hha_extract.py).
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Michigan Home Health Explorer", layout="wide")

MONEY = st.column_config.NumberColumn(format="dollar")


@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv("output/mi_hha_extract.csv", dtype={"PRVDR_NUM": str})
    df["agency"] = df["pos_name"].fillna(df["name"])
    df["active"] = df["pos_terminated"].isna()
    df["operator"] = df["home_office_name"].where(
        df["in_chain"] == "Y", other="(independent)"
    )
    df.loc[df["in_chain"].isna(), "operator"] = pd.NA
    return df


df = load()

# --- sidebar filters ---------------------------------------------------------

st.sidebar.title("Filters")
status = st.sidebar.radio("Status", ["Active", "Terminated", "All"], index=0)
own = st.sidebar.multiselect(
    "Ownership", sorted(df["ownership_category"].dropna().unique())
)
operators = st.sidebar.multiselect(
    "Operator (chain home office)", sorted(df["operator"].dropna().unique())
)
markets = sorted(
    df["service_area_names"].dropna().str.split("|").explode().unique()
)
market = st.sidebar.selectbox("Serves market", ["(any)", *markets])
needs_report = st.sidebar.checkbox("Has cost report", value=False)
search = st.sidebar.text_input("Name / city search")

view = df.copy()
if status != "All":
    view = view[view["active"] == (status == "Active")]
if own:
    view = view[view["ownership_category"].isin(own)]
if operators:
    view = view[view["operator"].isin(operators)]
if market != "(any)":
    view = view[view["service_area_names"].str.contains(market, regex=False, na=False)]
if needs_report:
    view = view[view["has_cost_report"]]
if search:
    hay = view["agency"].fillna("") + " " + view["pos_city"].fillna("")
    view = view[hay.str.contains(search, case=False)]

# --- headline ----------------------------------------------------------------

st.title("Michigan Home Health Explorer")
st.caption(
    "CMS HCRIS cost reports (1728-20, FY2024-25) joined to the CMS Provider of "
    "Services file. Revenue reflects each agency's most recent annual-coverage "
    "report; agencies with low/no Medicare utilization file no financials."
)

agency_rev = view.loc[~view["f1_shared_across_ccns"].fillna(False), "net_patient_revenue"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Agencies", len(view))
c2.metric("With cost report", int(view["has_cost_report"].sum()))
c3.metric("Visits (reported)", f"{view['total_visits'].sum():,.0f}")
c4.metric("Net patient revenue*", f"${agency_rev.sum() / 1e6:,.0f}M")
st.caption("*agency-level filers only; excludes org-level F-1s shared across CCNs")

# --- tabs --------------------------------------------------------------------

agencies_tab, chains_tab, markets_tab, wages_tab, detail_tab = st.tabs(
    ["Agencies", "Operators", "Markets", "Wages", "Agency detail"]
)

with agencies_tab:
    cols = {
        "PRVDR_NUM": "CCN",
        "agency": "Agency",
        "pos_city": "City",
        "ownership_category": "Ownership",
        "operator": "Operator",
        "total_visits": "Visits",
        "net_patient_revenue": "Net patient revenue",
        "rn_avg_hourly_wage": "RN avg hourly wage",
        "period_days": "Period (days)",
        "hcris_year": "HCRIS file",
    }
    table = view[list(cols)].rename(columns=cols).sort_values(
        "Visits", ascending=False, na_position="last"
    )
    st.dataframe(
        table,
        hide_index=True,
        height=520,
        column_config={"Net patient revenue": MONEY},
    )
    st.download_button(
        "Download filtered rows (CSV)",
        view.to_csv(index=False),
        file_name="mi_hha_filtered.csv",
    )

with chains_tab:
    filers = view[view["has_cost_report"] & view["operator"].notna()]
    grp = (
        filers.groupby("operator")
        .agg(
            agencies=("PRVDR_NUM", "count"),
            home_office_state=("home_office_state", "first"),
            visits=("total_visits", "sum"),
            total_costs=("total_costs", "sum"),
            median_rn_wage=("rn_avg_hourly_wage", "median"),
        )
        .sort_values("visits", ascending=False)
    )
    st.dataframe(grp, column_config={"total_costs": MONEY}, height=420)
    st.bar_chart(grp["visits"].drop("(independent)", errors="ignore").head(12))

with markets_tab:
    served = (
        view.dropna(subset=["service_area_names"])
        .assign(market=lambda d: d["service_area_names"].str.split("|"))
        .explode("market")
    )
    per_market = (
        served.groupby("market")
        .agg(
            agencies=("PRVDR_NUM", "nunique"),
            chains=("operator", lambda s: (s != "(independent)").sum()),
            visits=("total_visits", "sum"),
            median_rn_wage=("rn_avg_hourly_wage", "median"),
        )
        .sort_values("agencies", ascending=False)
    )
    st.caption("Markets = CBSAs where agencies report delivering Medicare services (S-3 Part III).")
    st.dataframe(per_market, height=420)
    st.bar_chart(per_market["agencies"].head(12))

with wages_tab:
    wages = view.dropna(subset=["rn_avg_hourly_wage"])
    clean = wages[wages["rn_wage_quality"] == "ok"]
    st.caption(
        "Average hourly wage = (salaries + fringes) / paid hours, employee RNs, "
        "per Worksheet S-3 Part V. Charts use only wages that are internally "
        "consistent (paid hours ≈ FTEs × 2080) AND plausible as a loaded "
        "Michigan RN wage ($15–90/hr); per-visit-paid workforces report "
        "fictional hours and show as 'suspect'."
    )
    q = wages["rn_wage_quality"].value_counts()
    st.caption(
        f"Quality: {q.get('ok', 0)} ok · {q.get('suspect', 0)} suspect · "
        f"{q.get('unverifiable', 0)} unverifiable"
    )
    left, right = st.columns(2)
    with left:
        st.subheader("RN wage distribution (corroborated)")
        bins = pd.cut(clean["rn_avg_hourly_wage"], bins=range(0, 130, 10))
        hist = bins.value_counts().sort_index()
        hist.index = hist.index.map(lambda i: f"${i.left}-{i.right}")
        st.bar_chart(hist)
    with right:
        st.subheader("Median RN wage by ownership (corroborated)")
        st.bar_chart(clean.groupby("ownership_category")["rn_avg_hourly_wage"].median())
    flagged = wages[wages["rn_wage_quality"] != "ok"]
    if len(flagged):
        st.subheader("Uncorroborated wages (verify before citing)")
        st.dataframe(
            flagged[
                [
                    "PRVDR_NUM",
                    "agency",
                    "pos_city",
                    "rn_avg_hourly_wage",
                    "rn_paid_hours",
                    "rn_ftes",
                    "rn_wage_quality",
                    "operator",
                ]
            ].sort_values("rn_avg_hourly_wage", ascending=False),
            hide_index=True,
        )

with detail_tab:
    choices = view.dropna(subset=["agency"]).sort_values("agency")
    label = choices["agency"] + " — " + choices["pos_city"].fillna("?") + " (" + choices["PRVDR_NUM"] + ")"
    pick = st.selectbox("Agency", label)
    if pick:
        row = choices.iloc[label.tolist().index(pick)]
        a, b, c = st.columns(3)
        a.metric("Net patient revenue", f"${row['net_patient_revenue']:,.0f}" if pd.notna(row["net_patient_revenue"]) else "—")
        b.metric("Total visits", f"{row['total_visits']:,.0f}" if pd.notna(row["total_visits"]) else "—")
        c.metric("RN avg hourly wage", f"${row['rn_avg_hourly_wage']:,.2f}" if pd.notna(row["rn_avg_hourly_wage"]) else "—")
        if pd.notna(row.get("service_area_names")):
            st.write("**Service area:**", row["service_area_names"].replace("|", " · "))
        if pd.notna(row.get("operator")) and row["operator"] != "(independent)":
            st.write(
                "**Operated by:**",
                f"{row['operator']} ({row['home_office_city']}, {row['home_office_state']})",
            )
        if row["f1_shared_across_ccns"]:
            st.warning("Revenue is an org-level F-1 shared across multiple CCNs, not agency-level.")
        with st.expander("Full record"):
            st.dataframe(row.to_frame("value"))
