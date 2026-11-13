import math

import pandas as pd
import streamlit as st

from backend.analysis import api
from ui.dashboard.components import (
    DashboardHeader,
    MetricCard,
    PropertyCard,
    TYPE_LABELS,
)
from ui.dashboard.attribution import render_attribution_footer


def styled_table(rows):
    frame = pd.DataFrame(rows)

    def row_colors(row):
        background = "#F7F1E8" if row.name % 2 == 0 else "#FFFFFF"
        return [f"background-color: {background}; color: #1A214F;" for _ in row]

    return frame.style.apply(row_colors, axis=1)


DashboardHeader(
    "Building portfolio",
    "Manage and monitor your properties.",
).initialize()

buildings = api.list_buildings()
if not buildings:
    st.info("No buildings are available yet. Import the OPSD dataset to populate your portfolio.")
    st.stop()

metric_cols = st.columns(3, gap="medium")
with metric_cols[0]:
    MetricCard(
        "Total buildings",
        len(buildings),
        key="total_buildings",
        icon=":material/apartment:",
    ).initialize()
with metric_cols[1]:
    MetricCard(
        "Total area",
        f"{sum(building['floor_area_m2'] for building in buildings):,.0f} m²",
        key="total_area",
        icon=":material/expand_content:",
    ).initialize()
with metric_cols[2]:
    MetricCard(
        "Building types",
        len({building["type"] for building in buildings}),
        key="number_of_types",
        icon=":material/analytics:",
    ).initialize()

st.subheader("Your properties")
building_types = sorted({building["type"] for building in buildings})
with st.container(border=True, key="buildings_filter_panel"):
    st.markdown("#### Find a property")
    st.caption("Filter by building type or search by name.")
    filter_col, search_col = st.columns([1, 2], gap="medium")
    with filter_col:
        selected_type = st.selectbox(
            "Building type",
            ["all", *building_types],
            format_func=lambda kind: (
                "All types" if kind == "all"
                else TYPE_LABELS.get(kind, kind.title())
            ),
            key="buildings_type_filter",
        )
    with search_col:
        search_text = st.text_input(
            "Search buildings",
            placeholder="Search by building name",
            key="buildings_search",
        ) or ""
        search_text = search_text.strip()

filtered_buildings = [
    building
    for building in buildings
    if (
        selected_type == "all"
        or building["type"] == selected_type
    )
    and search_text.strip().casefold() in building["name"].casefold()
]

st.caption(
    f"Showing {len(filtered_buildings)} of {len(buildings)} "
    f"{'building' if len(buildings) == 1 else 'buildings'}."
)

if not filtered_buildings:
    st.info("No buildings match those filters.")
    st.stop()

selected_id = st.session_state.get("selected_building_id")
visible_ids = {building["id"] for building in filtered_buildings}
if selected_id not in visible_ids:
    selected_id = filtered_buildings[0]["id"]
    st.session_state["selected_building_id"] = selected_id

cards_per_row = 3
for row_start in range(0, len(filtered_buildings), cards_per_row):
    row_buildings = filtered_buildings[row_start:row_start + cards_per_row]
    card_cols = st.columns(cards_per_row, gap="medium")
    for column, building in zip(card_cols, row_buildings):
        is_selected = building["id"] == selected_id
        with column:
            if PropertyCard(building, selected=is_selected).initialize():
                selected_id = building["id"]
                st.session_state["selected_building_id"] = selected_id

selected_building = next(
    building for building in filtered_buildings if building["id"] == selected_id
)
st.subheader("Property details")
with st.container(border=True, key="building_detail"):
    st.markdown(f"### {selected_building['name']}")
    st.caption("Building information and the latest available meter data.")
    latest = api.get_latest(selected_building["id"])
    sustainability_score: dict[str, float | str] | None = None
    score_unavailable = False
    if isinstance(latest, dict) and latest.get("last_reading") is not None:
        latest_timestamp = pd.to_datetime(
            latest["last_reading"], utc=True, errors="coerce"
        )
        if pd.isna(latest_timestamp):
            st.warning("The latest reading timestamp is invalid; score unavailable.")
        else:
            score_end = latest_timestamp + pd.Timedelta(minutes=15)
            score_start = score_end - pd.Timedelta(days=30)
            try:
                sustainability_score = api.get_score(
                    selected_building["id"],
                    score_start,
                    score_end,
                )
            except ValueError:
                score_unavailable = True

    detail_cols = st.columns(4, gap="medium")
    detail_cols[0].metric(
        "Category",
        TYPE_LABELS.get(selected_building["type"], selected_building["type"].title()),
    )
    detail_cols[1].metric("Floor area", f"{selected_building['floor_area_m2']:,.0f} m²")
    if sustainability_score is not None:
        score_value = float(sustainability_score["score"])
        if not math.isfinite(score_value):
            raise ValueError("Sustainability score must be a finite number.")
        detail_cols[2].metric(
            "Sustainability score · 30 days",
            f"{score_value:.1f} / 100",
            delta=f"Grade {sustainability_score['grade']}",
            delta_color="off",
        )
    else:
        detail_cols[2].metric("Sustainability score · 30 days", "Unavailable")
    detail_cols[3].metric("Building ID", selected_building["id"])
    st.caption(
        "Score combines energy intensity and after-hours use; configured benchmarks "
        "are assumptions, not official ratings."
    )
    if score_unavailable:
        st.caption("A score could not be calculated from readings in this period.")

    st.markdown("#### Latest electricity reading")
    if not isinstance(latest, dict):
        st.warning("Latest meter data is unavailable for this building.")
    else:
        latest_cols = st.columns(3, gap="medium")
        power_kw = latest.get("power_kw")
        power_display = "Unavailable"
        if power_kw is not None:
            try:
                power_value = float(str(power_kw))
            except (TypeError, ValueError):
                pass
            else:
                if math.isfinite(power_value):
                    power_display = f"{power_value:,.2f} kW"
        latest_cols[0].metric(
            "Estimated power",
            power_display,
        )
        last_reading = latest.get("last_reading")
        with latest_cols[1]:
            st.caption("Last reading")
            st.write(
                str(last_reading) if last_reading is not None else "No readings"
            )

        zones = latest.get("zones") or []
        latest_cols[2].metric("Meter zones", len(zones))
        if last_reading is None:
            st.info("No meter readings have been recorded for this property yet.")
        elif zones:
            st.markdown("#### Power by meter zone")
            st.dataframe(
                styled_table(zones),
                hide_index=True,
                width="stretch",
                column_config={
                    "zone": st.column_config.TextColumn("Zone"),
                    "power_kw": st.column_config.NumberColumn("Power (kW)", format="%.2f"),
                },
            )
        else:
            st.caption("No meter-zone breakdown is available for this reading.")

render_attribution_footer()
