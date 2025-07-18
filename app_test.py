# app.py  – quick test for GCC-obesity dataset
import streamlit as st
import pandas as pd

# ---------- 1.  LOAD DATA ---------------------------------
@st.cache_data
def load_data():
    url = (
        "https://raw.githubusercontent.com/"
        "johnnymkh/obesity_dashboard/main/BEFA58B_ALL_LATEST.csv"  # ✅ clean URL
    )
    return pd.read_csv(url)

df = load_data()

# keep only rows with an obesity rate and the four GCC countries
gcc_countries = [
    "Bahrain", "Kuwait", "Oman", "Qatar",
    "Saudi Arabia", "United Arab Emirates"
]
df = df[df["GEO_NAME_SHORT"].isin(gcc_countries)]

# ---------- 2.  SIDEBAR FILTERS ---------------------------
st.sidebar.header("Choose a view")
country = st.sidebar.selectbox(
    "Country", sorted(df["GEO_NAME_SHORT"].unique())
)

gender_map = {
    "Both": "TOTAL",
    "Male": "MALE",
    "Female": "FEMALE"
}
gender_label = st.sidebar.radio(
    "Gender", list(gender_map.keys()), horizontal=True
)
gender_code = gender_map[gender_label]

# ---------- 3.  FILTERED SUBSET ---------------------------
sub = df[
    (df["GEO_NAME_SHORT"] == country) &
    (df["DIM_SEX"] == gender_code)
]

if sub.empty:
    st.warning(
        "No data for this gender in the country selected – "
        "try another option."
    )
    st.stop()

# pick the *latest* year with an estimate
latest_year = sub["DIM_TIME"].max()
latest_row  = sub[sub["DIM_TIME"] == latest_year].iloc[0]
rate        = latest_row["RATE_PER_100_N"]  # prevalence %

# ---------- 4.  DISPLAY -----------------------------------
st.metric(
    f"Obesity rate in {country} ({gender_label}) – {latest_year}",
    f"{rate:.1f} %"
)

# build a tiny DataFrame for the chart
chart_df = (
    sub.sort_values("DIM_TIME")
       .set_index("DIM_TIME")[["RATE_PER_100_N"]]   # brackets → DataFrame
)

st.line_chart(chart_df, height=250)


st.caption(
    "Source: BEFA58B_ALL_LATEST.csv – RATE_PER_100_N = prevalence "
    "of adults (18+) with BMI ≥ 30 kg/m²."
)
