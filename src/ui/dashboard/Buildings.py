import pandas as pd
import streamlit as st

from backend.analysis import api
from ui.dashboard.components import DashboardHeader, MetricCard, PropertyCard, TYPE_LABELS


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
filter_col, search_col = st.columns([1, 2], gap="medium")
building_types = sorted({building["type"] for building in buildings})
with filter_col:
    selected_type = st.selectbox(
        "Building type",
        ["All types", *[TYPE_LABELS.get(kind, kind.title()) for kind in building_types]],
    )
with search_col:
    search_text = st.text_input("Search buildings", placeholder="Search by building name") or ""

filtered_buildings = [
    building
    for building in buildings
    if (
        selected_type == "All types"
        or TYPE_LABELS.get(building["type"], building["type"].title()) == selected_type
    )
    and search_text.strip().casefold() in building["name"].casefold()
]

if not filtered_buildings:
    st.info("No buildings match those filters.")
    st.stop()

selected_id = st.session_state.get("selected_building_id")
visible_ids = {building["id"] for building in filtered_buildings}
if selected_id not in visible_ids:
    selected_id = filtered_buildings[0]["id"]
    st.session_state["selected_building_id"] = selected_id

card_cols = st.columns(3, gap="medium")
for index, building in enumerate(filtered_buildings):
    with card_cols[index % len(card_cols)]:
        if PropertyCard(building).initialize():
            selected_id = building["id"]
            st.session_state["selected_building_id"] = selected_id

selected_building = next(
    building for building in filtered_buildings if building["id"] == selected_id
)
st.subheader("Property details")
with st.container(border=True, key="building_detail"):
    st.markdown(f"### {selected_building['name']}")
    detail_cols = st.columns(3, gap="medium")
    detail_cols[0].metric(
        "Category",
        TYPE_LABELS.get(selected_building["type"], selected_building["type"].title()),
    )
    detail_cols[1].metric("Floor area", f"{selected_building['floor_area_m2']:,.0f} m²")
    detail_cols[2].metric("Building ID", selected_building["id"])

    latest = api.get_latest(selected_building["id"])
    st.markdown("#### Latest electricity reading")
    latest_cols = st.columns([1, 2], gap="medium")
    latest_cols[0].metric("Estimated power", f"{latest['power_kw']:,.2f} kW")
    if latest["last_reading"] is None:
        latest_cols[1].info("No meter readings have been recorded for this property yet.")
    else:
        latest_cols[1].write(f"**Last updated:** {latest['last_reading']}")
        if latest["zones"]:
            st.dataframe(
                styled_table(latest["zones"]),
                hide_index=True,
                width="stretch",
                column_config={
                    "zone": st.column_config.TextColumn("Zone"),
                    "power_kw": st.column_config.NumberColumn("Power (kW)", format="%.2f"),
                },
            )
