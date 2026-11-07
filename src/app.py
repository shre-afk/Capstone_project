from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AI Smart Energy Management",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
css_file = BASE_DIR / "styles" / "style.css"

if css_file.exists():
    with open(css_file, encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )
else:
    st.warning(f"CSS file not found: {css_file}")

dashboard_dir = Path(__file__).parent / "ui" / "dashboard"
logo_file = dashboard_dir / "static" / "Capstone_Logo.png"

if logo_file.exists():
    st.logo(str(logo_file), size="large")


pages = st.navigation(
    [
        st.Page(dashboard_dir / "Overview.py", title="Overview", icon=":material/overview:"),
        st.Page(dashboard_dir / "Buildings.py", title="Buildings", icon=":material/apartment:"),
        st.Page(
            dashboard_dir / "EnergyAnalytics.py",
            title="Energy Analytics",
            icon=":material/energy_program_time_used:",
        ),
        st.Page(
            dashboard_dir / "Forecasting.py",
            title="Forecasting",
            icon=":material/robot_2:",
        ),
        st.Page(
            dashboard_dir / "Advisor.py",
            title="AI Advisor",
            icon=":material/support_agent:",
        ),
        st.Page(
            dashboard_dir / "Reports.py",
            title="Reports",
            icon=":material/description:",
        ),
        st.Page(
            dashboard_dir / "Properties.py",
            title="Properties",
            icon=":material/business_center:",
        ),
    ]
)

pages.run()
