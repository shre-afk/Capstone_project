import math
from collections.abc import Callable
from html import escape
from typing import TypeVar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.analysis import api
from backend import settings
from ui.dashboard.components import (
    DashboardHeader,
    MetricCard,
)
from ui.dashboard.attribution import render_attribution_footer
from ui.dashboard.anomalies import flag_daily_anomalies
from ui.dashboard.errors import DashboardErrorHandler, DashboardOperationError

Result = TypeVar("Result")


def _dashboard_call(
    operation: str,
    callback: Callable[..., Result],
    *args,
    fatal: bool = False,
    **kwargs,
) -> Result | None:
    try:
        return DashboardErrorHandler.execute(operation, callback, *args, **kwargs)
    except DashboardOperationError as error:
        if fatal:
            st.error(str(error))
            st.stop()
        st.warning(str(error))
        return None


def _finite_number(record: object, key: str) -> float:
    if not isinstance(record, dict) or key not in record:
        raise ValueError(f"Response is missing {key}")
    value = float(record[key])
    if not math.isfinite(value):
        raise ValueError(f"Response contains an invalid {key}")
    return value


def _reading_timestamp(record: object) -> pd.Timestamp | None:
    if not isinstance(record, dict):
        raise ValueError("Latest reading response must be an object")
    value = record.get("last_reading")
    if value is None:
        return None
    parsed_timestamp = pd.to_datetime(str(value), utc=True, errors="raise")
    if pd.isna(parsed_timestamp):
        raise ValueError("Latest reading timestamp is invalid")
    return parsed_timestamp


def _daily_energy_series(frame: object) -> pd.Series | None:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    values = frame.apply(pd.to_numeric, errors="coerce")
    values = values.replace([float("inf"), float("-inf")], float("nan"))
    energy_series = values.sum(axis=1, min_count=1).dropna()
    if energy_series.empty:
        return None
    energy_series.index = pd.to_datetime(energy_series.index, utc=True, errors="coerce")
    energy_series = energy_series[energy_series.index.notna()]
    if energy_series.empty:
        return None
    energy_series.index = energy_series.index.tz_convert(settings.LOCAL_TZ)
    return energy_series.groupby(level=0).sum(min_count=1)


buildings = _dashboard_call(
    "loading buildings",
    api.list_buildings,
    fatal=True,
)
if not isinstance(buildings, list):
    st.error("Could not load buildings because the response has an invalid format.")
    st.stop()
if not buildings:
    st.info("Your portfolio is empty. Import the OPSD dataset to get started.")
    st.stop()

title_col, header_filter = st.columns([3, 1], vertical_alignment="center")
with title_col:
    DashboardHeader(
        "Overview",
        "Real-time insights into your energy portfolio.",
    ).initialize()
with header_filter:
    period_label = st.selectbox("Reporting period", ["Last 30 days", "Last 6 months"])
period_days = 30 if period_label == "Last 30 days" else 180

valid_buildings = []
readings_with_times = []
for building in buildings:
    required_fields = {"id", "name", "type", "floor_area_m2"}
    if not isinstance(building, dict) or not required_fields.issubset(building):
        st.warning("Skipped a building with incomplete identifying information.")
        continue
    try:
        floor_area = float(building["floor_area_m2"])
    except (TypeError, ValueError):
        floor_area = 0.0
    if not building.get("name") or not math.isfinite(floor_area) or floor_area <= 0:
        st.warning("Skipped a building with invalid property details.")
        continue
    valid_buildings.append(building)
    latest = _dashboard_call(
        f"loading the latest reading for {building['name']}",
        api.get_latest,
        building["id"],
    )
    if latest is None:
        continue
    timestamp = _dashboard_call(
        f"checking the latest reading for {building['name']}",
        _reading_timestamp,
        latest,
    )
    if timestamp is not None:
        readings_with_times.append(timestamp)

buildings = valid_buildings
if not buildings:
    st.info("No buildings with valid identifying information are available.")
    st.stop()

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

energy_by_building = []
timeseries_by_building = {}
saved_co2_kg = 0.0
previous_energy_kwh = 0.0
previous_emissions_kg = 0.0
savings_reading_count = 0
for building in buildings:
    building_id = building["id"]
    co2 = None
    kpis = _dashboard_call(
        f"loading energy metrics for {building['name']}",
        api.get_kpis,
        building_id,
        period_start,
        period_end,
    )
    if kpis is not None:
        energy = _dashboard_call(
            f"checking energy metrics for {building['name']}",
            _finite_number,
            kpis,
            "energy_kwh",
        )
        co2 = _dashboard_call(
            f"checking emissions for {building['name']}",
            _finite_number,
            kpis,
            "co2_kg",
        )
        if energy is not None:
            energy_by_building.append((building["name"], energy))

    series = _dashboard_call(
        f"loading the consumption trend for {building['name']}",
        api.get_timeseries,
        building_id,
        period_start,
        period_end,
        freq="1D",
    )
    if series is not None:
        daily = _dashboard_call(
            f"preparing the consumption trend for {building['name']}",
            _daily_energy_series,
            series,
        )
        if daily is not None:
            timeseries_by_building[building["name"]] = daily

    savings = _dashboard_call(
        f"comparing energy use for {building['name']}",
        api.get_savings,
        building_id,
        period_start,
        period_end,
    )
    if savings is not None:
        saved = _dashboard_call(
            f"checking the emissions comparison for {building['name']}",
            _finite_number,
            savings,
            "saved_co2_kg",
        )
        previous = _dashboard_call(
            f"checking previous energy use for {building['name']}",
            _finite_number,
            savings,
            "previous_kwh",
        )
        if saved is not None:
            saved_co2_kg += saved
            savings_reading_count += 1
            if co2 is not None:
                previous_emissions_kg += co2 + saved
        if previous is not None:
            previous_energy_kwh += previous

total_energy_kwh = sum(energy for _, energy in energy_by_building)
consumption_label = "Total consumption"
if len(energy_by_building) < len(buildings):
    consumption_label = (
        f"Consumption ({len(energy_by_building)} of {len(buildings)} buildings)"
    )
saved_label = "CO₂ saved vs previous period"
saved_value = f"{saved_co2_kg / 1000:,.2f} t" if savings_reading_count else "Unavailable"
saved_delta = None
if savings_reading_count and saved_co2_kg < 0:
    saved_label = "CO₂ increase vs previous period"
    saved_value = f"{abs(saved_co2_kg) / 1000:,.2f} t"
if (
    savings_reading_count
    and previous_emissions_kg > 1e-9
    and math.isfinite(previous_emissions_kg)
):
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
        consumption_label,
        f"{total_energy_kwh:,.0f} kWh" if energy_by_building else "Unavailable",
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
with st.container(key="overview_analysis_row"):
    chart_col, insights_col = st.columns([2.2, 1], gap="large")
    with chart_col:
        with st.container(border=True, key="overview_trend"):
            st.subheader("Energy consumption trend")
            if timeseries_by_building:
                trend = pd.concat(timeseries_by_building, axis=1).sum(axis=1, min_count=1)
                anomaly_data = flag_daily_anomalies(trend)
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
                flagged = anomaly_data[anomaly_data["is_anomaly"]]
                if not flagged.empty:
                    chart.add_trace(
                        go.Scatter(
                            x=flagged.index,
                            y=flagged["consumption_kwh"],
                            mode="markers",
                            name="Unusual-use indicator",
                            marker={
                                "color": "#C45B38",
                                "size": 11,
                                "line": {"color": "#FFFCF7", "width": 2},
                            },
                            hovertemplate=(
                                "%{x|%b %d, %Y}<br>"
                                "Consumption: %{y:,.1f} kWh"
                                "<extra>Unusual-use indicator</extra>"
                            ),
                        )
                    )
                st.plotly_chart(chart, width="stretch", height=350)
                if flagged.empty:
                    st.caption(
                        "No unusual daily readings were flagged. Indicator only; "
                        "not a diagnosis."
                    )
                else:
                    st.caption(
                        f"{len(flagged)} unusual daily "
                        f"{'reading was' if len(flagged) == 1 else 'readings were'} "
                        "flagged (orange markers). Each reading is compared with "
                        "the prior 28 days for the same weekday (at least 3 readings), "
                        "using the median ± 3 × scaled median absolute deviation; "
                        "indicator only, not a diagnosis."
                    )
            else:
                st.info("There are no readings in this reporting period.")

    with insights_col:
        with st.container(border=True, key="overview_insights"):
            st.subheader("Key insights")
            insight_items = []
            if energy_by_building:
                top_building, top_energy = max(
                    energy_by_building, key=lambda item: item[1]
                )
                insight_items.append(
                    (
                        "Highest consumption",
                        f"{escape(top_building)}",
                        f"{top_energy:,.1f} kWh",
                    )
                )
            else:
                insight_items.append(
                    (
                        "Highest consumption",
                        "Unavailable",
                        "Building consumption data is unavailable",
                    )
                )
            if previous_energy_kwh > 0:
                change_pct = (total_energy_kwh - previous_energy_kwh) / previous_energy_kwh * 100
                direction = "higher" if change_pct > 0 else "lower"
                insight_items.append(
                    (
                        "Change vs previous period",
                        f"{abs(change_pct):.1f}% {direction}",
                        "Compared with the previous period",
                    )
                )
            else:
                insight_items.append(
                    (
                        "Comparison",
                        "Unavailable",
                        "No previous-period readings",
                    )
                )

            insight_cards = "".join(
                f'<div class="overview-insight-card">'
                f'<span class="overview-insight-label">{heading}</span>'
                f'<strong>{value}</strong>'
                f'<span class="overview-insight-detail">{detail}</span>'
                f"</div>"
                for heading, value, detail in insight_items
            )
            st.markdown(
                f'<div class="overview-insight-list">{insight_cards}</div>',
                unsafe_allow_html=True,
            )

render_attribution_footer()
