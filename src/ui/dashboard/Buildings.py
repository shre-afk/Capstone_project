from backend.analysis import api
import streamlit as st

st.set_page_config(page_title="Electricity consumption of buildings",layout="wide")

st.title("Building Portfolio", text_alignment="left")
st.caption("Manage and monitor your properties")
buildings = api.list_buildings()


col1, col2, col3 = st.columns(3, gap="medium")

total_buildings = len(buildings)
total_area = sum(b["floor_area_m2"] for b in buildings)
number_of_types = len({b["type"] for b in buildings})

with col1:
    with st.container(border=True,key="total_buildings"):
        st.metric("Total Buildings", total_buildings, icon=":material/apartment:")

with col2:
    with st.container(border=True,key="total_area"):
        st.metric("Total Area (m²)", total_area, icon=":material/expand_content:")

with col3:
    with st.container(border=True,key="number_of_types"):
        st.metric("Building Types", number_of_types, icon=":material/analytics:")


if not buildings:
    st.warning("No buildings found")
    st.stop()

building_options = {b["name"]: b["id"] for b in buildings}
selected_name = st.selectbox("Select Building", list(building_options.keys()))
selected_id = building_options[selected_name]


print(buildings)
# st.write(building)

st.dataframe(buildings)