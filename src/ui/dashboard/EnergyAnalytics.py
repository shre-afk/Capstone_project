import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.analysis import api
from ui.dashboard.components import DashboardHeader, TYPE_LABELS
from ui.dashboard.attribution import render_attribution_footer


DashboardHeader(
    "Energy Analytics",
    "Explore consumption across your buildings and property types.",
).initialize()

buildings = api.list_buildings()
if not buildings:
    st.info("No buildings are available for energy analysis.")
    st.stop()

period_lengths = {
    "Last 30 days": pd.Timedelta(days=30),
    "Last 6 months": pd.DateOffset(months=6),
    "Last 12 months": pd.DateOffset(months=12),
}

with st.container(border=True, key="energy_analytics_filters"):
    building_col, period_col = st.columns([1, 1], gap="medium")
    with building_col:
        selected_building_id = st.selectbox(
            "Building",
            options=[None, *[building["id"] for building in buildings]],
            format_func=lambda building_id: (
                "All buildings"
                if building_id is None
                else next(
                    building["name"]
                    for building in buildings
                    if building["id"] == building_id
                )
            ),
            key="energy_analytics_building",
        )
    with period_col:
        period_label = st.selectbox(
            "Reporting period",
            list(period_lengths),
            index=1,
            key="energy_analytics_period",
        )

if selected_building_id is None:
    selected_buildings = buildings
else:
    selected_buildings = [
        building
        for building in buildings
        if building["id"] == selected_building_id
    ]

buildings_with_readings = []
latest_times = []
for building in selected_buildings:
    latest = api.get_latest(building["id"])
    if not isinstance(latest, dict) or latest.get("last_reading") is None:
        continue

    timestamp = pd.to_datetime(
        latest["last_reading"], utc=True, errors="coerce"
    )
    if isinstance(timestamp, pd.Timestamp) and not pd.isna(timestamp):
        latest_times.append(timestamp)
        buildings_with_readings.append(building)

if not buildings_with_readings:
    st.info("No meter readings are available for this selection.")
    st.stop()

period_end = max(latest_times) + pd.Timedelta(minutes=15)
period_start = period_end - period_lengths[period_label]

type_colors = {
    "Commercial": "#173B63",
    "Residential": "#6B9AA8",
    "Public": "#D9A441",
}
building_rows = []
energy_by_type = {}
previous_energy = 0.0
comparison_available = True

for building in buildings_with_readings:
    kpis = api.get_kpis(
        building["id"],
        period_start,
        period_end,
    )
    energy = float(kpis["energy_kwh"])
    building_type = TYPE_LABELS.get(
        building["type"], building["type"].title()
    )
    building_rows.append(
        {
            "Building": building["name"],
            "Consumption (kWh)": energy,
            "Type": building_type,
        }
    )
    energy_by_type[building_type] = (
        energy_by_type.get(building_type, 0.0) + energy
    )

    savings = api.get_savings(
        building["id"],
        period_start,
        period_end,
    )
    if isinstance(savings, dict) and "previous_kwh" in savings:
        previous_energy += float(savings["previous_kwh"])
    else:
        comparison_available = False

building_data = pd.DataFrame(building_rows).sort_values(
    "Consumption (kWh)", ascending=False
)
total_energy = float(building_data["Consumption (kWh)"].sum())
top_buildings = building_data.nlargest(3, "Consumption (kWh)").iloc[::-1]
top_building = building_data.loc[
    building_data["Consumption (kWh)"].idxmax(), "Building"
]

metric_cols = st.columns(3, gap="medium")
metric_cols[0].metric("Total consumption", f"{total_energy:,.0f} kWh")
metric_cols[1].metric("Buildings with readings", len(buildings_with_readings))
metric_cols[2].metric("Highest consumer", top_building)

st.divider()
chart_col, type_col = st.columns([1, 1.2], gap="medium")

max_consumption = float(building_data["Consumption (kWh)"].max())
chart_height = min(380, max(300, 34 * len(building_data) + 100))

building_chart = go.Figure(
    go.Bar(
        x=building_data["Building"],
        y=building_data["Consumption (kWh)"],
        marker_color=[
            type_colors.get(building_type, "#173B63")
            for building_type in building_data["Type"]
        ],
        marker_line_width=0,
        text=[
            f"{consumption:,.0f}"
            for consumption in building_data["Consumption (kWh)"]
        ],
        textposition="outside",
        textfont=dict(color="#1A214F", size=12),
        cliponaxis=False,
        hovertemplate=(
            "<b>%{x}</b><br>Consumption: %{y:,.1f} kWh"
            "<extra></extra>"
        ),
    )
)
building_chart.update_layout(
    height=chart_height,
    margin=dict(l=12, r=28, t=12, b=78),
    bargap=0.34,
    showlegend=False,
    xaxis=dict(
        title=None,
        type="category",
        categoryorder="array",
        categoryarray=building_data["Building"].tolist(),
        tickangle=-30,
        automargin=True,
        tickfont=dict(size=12),
    ),
    yaxis=dict(
        title=dict(text="Consumption (kWh)", standoff=14),
        rangemode="tozero",
        range=[0, max(max_consumption, 1) * 1.18],
        tickformat=",.0f",
        nticks=8,
        showgrid=True,
        gridcolor="#E5D9C8",
        zeroline=False,
        automargin=True,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#1A214F",
)

type_data = pd.DataFrame(
    energy_by_type.items(),
    columns=["Building type", "Consumption (kWh)"],
)
type_chart = px.pie(
    type_data,
    names="Building type",
    values="Consumption (kWh)",
    hole=0.62,
    color="Building type",
    color_discrete_map=type_colors,
)
type_chart.update_traces(
    textinfo="percent",
    textposition="inside",
    insidetextorientation="horizontal",
    hovertemplate=(
        "%{label}<br>%{value:,.1f} kWh (%{percent})<extra></extra>"
    ),
    marker_line_color="#FFFCF7",
    marker_line_width=2,
)
type_chart.update_layout(
    height=chart_height,
    margin=dict(l=8, r=8, t=8, b=54),
    uniformtext_minsize=11,
    uniformtext_mode="hide",
    legend=dict(
        orientation="h",
        x=0.5,
        xanchor="center",
        y=-0.08,
        yanchor="top",
        title_text="",
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
type_chart.add_annotation(
    text=f"<b>{total_energy / 1000:,.1f}</b><br>MWh total",
    x=0.5,
    y=0.5,
    showarrow=False,
    font=dict(size=18, color="#1A214F"),
)

with chart_col:
    with st.container(border=True, key="energy_analytics_buildings"):
        st.subheader("Consumption by building")
        st.caption(
            f"{period_label} · {period_start.strftime('%d %b %Y')} – "
            f"{period_end.strftime('%d %b %Y')}"
        )
        st.plotly_chart(
            building_chart,
            width="stretch",
            height=chart_height,
            config={"displayModeBar": False},
        )

with type_col:
    with st.container(border=True, key="energy_analytics_types"):
        st.subheader("By building type")
        st.caption("Share of total energy use.")
        st.plotly_chart(
            type_chart,
            width="stretch",
            height=chart_height,
            config={"displayModeBar": False},
        )

st.divider()
consumers_col, comparison_col = st.columns([1.25, 1], gap="medium")

with consumers_col:
    with st.container(border=True, key="energy_analytics_consumers"):
        st.subheader("Top consumers")
        st.caption("Highest energy use in the selected period.")
        max_consumption = float(top_buildings["Consumption (kWh)"].max())
        for _, row in top_buildings.iterrows():
            label_col, bar_col, value_col = st.columns(
                [1.1, 2.5, 0.9],
                vertical_alignment="center",
                gap="small",
            )
            label_col.write(row["Building"])
            bar_col.progress(
                float(row["Consumption (kWh)"] / max_consumption)
                if max_consumption > 0
                else 0.0
            )
            value_col.caption(f"{row['Consumption (kWh)']:,.0f} kWh")

with comparison_col:
    with st.container(border=True, key="energy_analytics_comparison"):
        st.subheader("Compared with previous period")
        if comparison_available and previous_energy > 0:
            change_pct = (total_energy - previous_energy) / previous_energy * 100
            direction = (
                "higher" if change_pct > 0
                else "lower" if change_pct < 0
                else "unchanged"
            )
            st.metric(
                "Energy consumption",
                f"{total_energy:,.0f} kWh",
                delta=f"{change_pct:+.1f}% · {direction}",
                delta_color="inverse",
            )
            st.caption(
                f"Previous period: {previous_energy:,.0f} kWh"
            )
        else:
            st.info("Previous-period readings are unavailable for comparison.")

render_attribution_footer()
