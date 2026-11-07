import pandas as pd
import plotly.express as px
import streamlit as st

from backend.analysis import api
from ui.dashboard.components import DashboardHeader, MetricCard, TYPE_LABELS


def styled_table(frame):
    def row_colors(row):
        background = "#F7F1E8" if row.name % 2 == 0 else "#FFFFFF"
        return [f"background-color: {background}; color: #1A214F;" for _ in row]

    return frame.style.apply(row_colors, axis=1)


DashboardHeader(
    "Overview",
    "Real-time insights into your energy portfolio.",
).initialize()

buildings = api.list_buildings()
if not buildings:
    st.info("Your portfolio is empty. Import the OPSD dataset to get started.")
    st.stop()

header_filter, _ = st.columns([1, 3])
with header_filter:
    period_label = st.selectbox("Reporting period", ["Last 30 days", "Last 6 months"])
period_days = 30 if period_label == "Last 30 days" else 180

latest_readings = [
    (building, api.get_latest(building["id"]))
    for building in buildings
]
readings_with_times = [
    pd.Timestamp(latest["last_reading"])
    for _, latest in latest_readings
    if latest["last_reading"] is not None
]

if not readings_with_times:
    st.info("No meter readings are available yet. Import the OPSD dataset to see consumption insights.")
    MetricCard(
        "Total buildings",
        len(buildings),
        key="overview_buildings",
        icon=":material/apartment:",
    ).initialize()
    st.stop()

period_end = max(readings_with_times) + pd.Timedelta(minutes=15)
period_start = period_end - pd.Timedelta(days=period_days)

energy_by_building = {}
timeseries_by_building = {}
emissions_kg = 0.0
saved_co2_kg = 0.0
previous_energy_kwh = 0.0
previous_emissions_kg = 0.0
for building in buildings:
    building_id = building["id"]
    kpis = api.get_kpis(building_id, period_start, period_end)
    energy_by_building[building["name"]] = kpis["energy_kwh"]
    emissions_kg += kpis["co2_kg"]

    series = api.get_timeseries(building_id, period_start, period_end, freq="1D")
    if not series.empty:
        timeseries_by_building[building["name"]] = series.sum(axis=1, min_count=1)

    savings = api.get_savings(building_id, period_start, period_end)
    saved_co2_kg += savings["saved_co2_kg"]
    previous_energy_kwh += savings["previous_kwh"]
    previous_emissions_kg += kpis["co2_kg"] + savings["saved_co2_kg"]

total_energy_kwh = sum(energy_by_building.values())
saved_label = "CO₂ saved vs previous period"
saved_value = f"{saved_co2_kg / 1000:,.2f} t"
saved_delta = None
if saved_co2_kg < 0:
    saved_label = "CO₂ increase vs previous period"
    saved_value = f"{abs(saved_co2_kg) / 1000:,.2f} t"
if previous_emissions_kg > 0:
    saved_delta = f"{saved_co2_kg / previous_emissions_kg * 100:+.1f}% vs previous period"

metric_cols = st.columns(3, gap="medium")
with metric_cols[0]:
    MetricCard(
        "Total buildings",
        len(buildings),
        key="overview_buildings",
        icon=":material/apartment:",
    ).initialize()
with metric_cols[1]:
    MetricCard(
        "Total consumption",
        f"{total_energy_kwh:,.0f} kWh",
        key="overview_consumption",
        icon=":material/bolt:",
    ).initialize()
with metric_cols[2]:
    MetricCard(
        saved_label,
        saved_value,
        key="overview_emissions",
        delta=saved_delta,
    ).initialize()

st.divider()
chart_col, insights_col = st.columns([2.2, 1], gap="large")
with chart_col:
    with st.container(border=True, key="overview_trend"):
        st.subheader("Energy consumption trend")
        if timeseries_by_building:
            trend = pd.concat(timeseries_by_building, axis=1).sum(axis=1, min_count=1)
            chart_data = trend.rename("Consumption (kWh)").rename_axis("Date").reset_index()
            chart = px.line(
                chart_data,
                x="Date",
                y="Consumption (kWh)",
                markers=True,
                color_discrete_sequence=["#173B63"],
            )
            chart.update_traces(line={"width": 3}, marker={"size": 6})
            chart.update_layout(
                margin=dict(l=12, r=12, t=16, b=12),
                xaxis_title=None,
                yaxis_title="Consumption (kWh)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
            )
            st.plotly_chart(chart, width="stretch")
        else:
            st.info("There are no readings in this reporting period.")

with insights_col:
    with st.container(border=True, key="overview_insights"):
        st.subheader("Key insights")
        if energy_by_building:
            top_building = max(energy_by_building, key=lambda name: energy_by_building[name])
            st.markdown(
                f"**Highest consumption**  \n{top_building} used "
                f"{energy_by_building[top_building]:,.1f} kWh during {period_label.lower()}."
            )
        if previous_energy_kwh > 0:
            change_pct = (total_energy_kwh - previous_energy_kwh) / previous_energy_kwh * 100
            direction = "higher" if change_pct > 0 else "lower"
            st.markdown(
                f"**Compared with the previous period**  \nConsumption was "
                f"{abs(change_pct):.1f}% {direction}."
            )
        else:
            st.markdown("**Comparison**  \nNo previous-period readings are available.")

st.subheader("Your properties")
property_data = pd.DataFrame(buildings)
property_data["Category"] = property_data["type"].map(TYPE_LABELS).fillna(
    property_data["type"].str.title()
)
directory = property_data[["name", "Category", "floor_area_m2"]].rename(
    columns={"name": "Building", "floor_area_m2": "Floor area (m²)"}
)
st.dataframe(
    styled_table(directory),
    hide_index=True,
    width="stretch",
    column_config={
        "Building": st.column_config.TextColumn("Building"),
        "Category": st.column_config.TextColumn("Category"),
        "Floor area (m²)": st.column_config.NumberColumn("Floor area (m²)", format="%.0f"),
    },
)
