
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def apply_chart_style(fig, height=400):
    fig.update_layout(height=height)
    return fig

st.set_page_config(
    page_title="GCC Obesity Dashboard",
    layout="wide"
)

# LOAD DATA
@st.cache_data
def load_data():
    url = (
        "https://raw.githubusercontent.com/"
        "johnnymkh/obesity_dashboard/main/BEFA58B_ALL_LATEST.csv"
    )
    return pd.read_csv(url)

def load_diabetes_data():
    diabetes_df = pd.read_csv("https://raw.githubusercontent.com/"
        "johnnymkh/obesity_dashboard/main/diabetes-prevalence.csv")
    # Keep only 2021 data
    diabetes_2021 = diabetes_df[diabetes_df['Year'] == 2021].copy()
    # Rename columns for clarity
    diabetes_2021 = diabetes_2021.rename(columns={
        'Entity': 'GEO_NAME_SHORT',
        'Diabetes prevalence (% of population ages 20 to 79)': 'DIABETES_RATE'
    })
    return diabetes_2021[['GEO_NAME_SHORT', 'DIABETES_RATE']]


df = load_data()
diabetes_df = load_diabetes_data()

df_merged = df.merge(
    diabetes_df, 
    on='GEO_NAME_SHORT', 
    how='left'  # keeps all obesity records, adds diabetes where available
)



# keep only rows with an obesity rate and the four GCC countries
gcc_countries = [
    "Bahrain", "Kuwait", "Oman", "Qatar",
    "Saudi Arabia", "United Arab Emirates"
]
df_gcc = df[df["GEO_NAME_SHORT"].isin(gcc_countries)]



# SIDEBAR FILTERS
st.sidebar.header("Choose a view")

gcc_country = st.sidebar.selectbox(
    "GCC Country", gcc_countries
)

view_level = st.sidebar.radio(
    "Compare Data to …",
    ("Country", "Region", "World"),
    horizontal=True
)

if view_level == "Country":
    country_options = sorted(
        df.loc[df["DIM_GEO_CODE_TYPE"] == "COUNTRY", "GEO_NAME_SHORT"].dropna().unique()
    )
    comparison_location = st.sidebar.selectbox("Country", country_options)
    df_comparison = df[df["GEO_NAME_SHORT"] == comparison_location]
elif view_level == "Region":
    region_options = sorted(
        df.loc[df["DIM_GEO_CODE_TYPE"] == "WHOREGION", "GEO_NAME_SHORT"].dropna().unique()
    )
    comparison_location = st.sidebar.selectbox("Region", region_options)
    df_comparison = df[df["GEO_NAME_SHORT"] == comparison_location]
else:
    comparison_location = "World"
    df_comparison = df[df["GEO_NAME_SHORT"] == "World"]

gender_map = {
    "Both": "TOTAL",
    "Male": "MALE", 
    "Female": "FEMALE"
}
gender_label = st.sidebar.selectbox("Gender", list(gender_map.keys()))
gender_code = gender_map[gender_label]

# ORGANIZE DATASETS

# Get the selected GCC country data
df_gcc_selected = df_gcc[df_gcc["GEO_NAME_SHORT"] == gcc_country]

# Apply gender filter to both datasets
df_gcc_filtered = df_gcc_selected[df_gcc_selected["DIM_SEX"] == gender_code]
df_gcc_filtered = df_gcc_filtered.sort_values("DIM_TIME")
df_comparison_filtered = df_comparison[df_comparison["DIM_SEX"] == gender_code]
df_comparison_filtered = df_comparison_filtered.sort_values("DIM_TIME")

# Create a combined dataset for side-by-side comparisons
df_combined = pd.concat([
    df_gcc_filtered.assign(comparison_type="GCC Country"),
    df_comparison_filtered.assign(comparison_type=view_level)
], ignore_index=True)

# For time series comparisons, ensure we have year data
if "DIM_TIME" in df.columns:
    df_combined_timeseries = df_combined.sort_values("DIM_TIME")
else:
    df_combined_timeseries = df_combined

latest_year = df_combined['DIM_TIME'].max()
df_combined_latest = df_combined[df_combined['DIM_TIME'] == latest_year]

# VISUALIZATIONS

if "DIM_TIME" in df.columns:
    fig_timeseries = apply_chart_style(px.line(
        df_combined_timeseries,
        x="DIM_TIME",
        y="RATE_PER_100_N",
        color="GEO_NAME_SHORT",
        title=f"Obesity Trends: {gcc_country} vs {comparison_location}",
        labels={"RATE_PER_100_N": "Obesity Rate (%)", "YEAR": "Year"}
    ))

# All GCC countries vs the comparison location
df_all_gcc_comparison = pd.concat([
    df_gcc[df_gcc["DIM_SEX"] == gender_code].assign(region_type="GCC Countries"),
    df_comparison_filtered.assign(region_type=f"Comparison {view_level}")
], ignore_index=True)

fig_gcc_overview = apply_chart_style(px.box(
    df_all_gcc_comparison,
    x="region_type",
    y="RATE_PER_100_N",
    title=f"GCC Countries vs {comparison_location} - Obesity Rate Distribution",
    labels={"RATE_PER_100_N": "Obesity Rate (%)"}
))

# DISPLAY METRICS
st.header("Obesity Dashboard")

# KPIs
col1, col2, col3 = st.columns(3)

with col1:
    gcc_rate = df_gcc_filtered["RATE_PER_100_N"].iloc[-1] if not df_gcc_filtered.empty else 0
    st.metric(
        label=f"{gcc_country} Obesity Rate",
        value=f"{gcc_rate:.1f}%"
    )

with col2:
    comparison_rate = df_comparison_filtered["RATE_PER_100_N"].iloc[-1] if not df_comparison_filtered.empty else 0
    st.metric(
        label=f"{comparison_location} Obesity Rate",
        value=f"{comparison_rate:.1f}%"
    )

with col3:
    if not df_gcc_filtered.empty and not df_comparison_filtered.empty:
        difference = gcc_rate - comparison_rate
        st.metric(
            label="Difference",
            value=f"{difference:+.1f}%",
            delta=f"{difference:.1f}%"
        )

# Display charts

col11, col12 = st.columns(2)

with col11:
    st.plotly_chart(fig_timeseries, use_container_width=True)

with col12:
    st.plotly_chart(fig_gcc_overview, use_container_width=True)



# Filter data for both genders across all GCC countries
df_dumbbell = df[df['GEO_NAME_SHORT'].isin(gcc_countries + ['World']) & df['DIM_SEX'].isin(['MALE', 'FEMALE'])]

# Get most recent year
latest_year = df_dumbbell['DIM_TIME'].max()
df_dumbbell_latest = df_dumbbell[df_dumbbell['DIM_TIME'] == latest_year]

# Pivot to get male and female rates in separate columns
df_pivot = df_dumbbell_latest.pivot_table(
    index='GEO_NAME_SHORT', 
    columns='DIM_SEX', 
    values='RATE_PER_100_N', 
    aggfunc='mean'
).reset_index()

df_pivot = df_pivot.sort_values('FEMALE', ascending=False)
# Create dumbbell plot
fig_dumbbell = go.Figure()

# Add lines connecting male and female rates
for i, row in df_pivot.iterrows():
    fig_dumbbell.add_trace(go.Scatter(
        x=[row['MALE'], row['FEMALE']],
        y=[row['GEO_NAME_SHORT'], row['GEO_NAME_SHORT']],
        mode='lines',
        line=dict(color='lightgray', width=3),
        showlegend=False
    ))

# Add male points
fig_dumbbell.add_trace(go.Scatter(
    x=df_pivot['MALE'],
    y=df_pivot['GEO_NAME_SHORT'],
    mode='markers',
    marker=dict(color='blue', size=15),
    name='Male'
))

# Add female points
fig_dumbbell.add_trace(go.Scatter(
    x=df_pivot['FEMALE'],
    y=df_pivot['GEO_NAME_SHORT'],
    mode='markers',
    marker=dict(color='red', size=15),
    name='Female'
))

fig_dumbbell.update_layout(
    title="Gender Gap in Obesity Rates - GCC Countries",
    xaxis_title="Obesity Rate (%)",
    height=400
)

st.plotly_chart(fig_dumbbell, use_container_width=True)




df_merged_2021 = df_merged[df_merged['DIM_TIME'] == 2021]
df_merged_2021 = df_merged[df_merged['DIM_SEX'] == "TOTAL"]

# Create correlation matrix
correlation_data = df_merged_2021[['RATE_PER_100_N', 'DIABETES_RATE']].dropna()

# Calculate correlation matrix
correlation_matrix = correlation_data.corr()

# Create heatmap
fig_corr = px.imshow(
    correlation_matrix,
    text_auto=True,
    color_continuous_scale='RdBu',
    title="Correlation Matrix: Obesity vs Diabetes Rates",
    labels={'x': 'Variables', 'y': 'Variables'}
)

fig_corr.update_layout(height=400)
