import streamlit as st
from pathlib import Path

import pandas as pd


# Page Configuration
st.set_page_config(
    page_title="AI Smart Energy Management",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Path for logo
current_directory = Path(__file__).parent if "__file__" in locals() else Path.cwd()

# Local path \Capstone_project\src\energy_management\dashboard\static\Capstone_Logo.png
css_file = current_directory / "static" / "style.css"
logo_file = current_directory / "static" / "Capstone_Logo.png"

# inject CSS
if css_file.exists():
    with open(css_file,"r", encoding="utf-8") as f:
        st.html(f"<style>{f.read()}</style>")

# set logo
if logo_file.exists():
    st.logo(str(logo_file), size="large")

# Page Functions
def overview_page():
    st.title("Overview")
    st.write("Monitor and analyze electricity consumption across German properties.")

def buildings_page():
    st.title("Buildings")
    st.write("Overview of individual facilities and meter metadata.")

# Navigation Definition
pages=st.navigation([
    st.Page(overview_page, title="Overview", icon=":material/overview:"),
    st.Page(buildings_page, title="Buildings", icon=":material/apartment:"),
    st.Page("EnergyAnalytics.py", title="Energy Analytics", icon=":material/energy_program_time_used:"),
    st.Page("Forecasting.py", title="Forecasting", icon=":material/robot_2:"),
    st.Page("Advisor.py", title="AI Advisor", icon=":material/support_agent:"),
    st.Page("Reports.py", title="Reports", icon=":material/description:"),
    st.Page("Properties.py", title="Properties", icon=":material/business_center:"),
])


# Bottom Footer Profile badge
with st.sidebar:
    st.html(
        """
        <div class="sidebar-bottom-container">
            <div class="sidebar-bottom-nav">
                <a href="#settings" class="sidebar-bottom-link">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    <span>Settings</span>
                </a>
                <a href="#help" class="sidebar-bottom-link">
                    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    <span>Help</span>
                </a>
            </div>
            <div class="sidebar-profile">
                <div class="profile-avatar">SP</div>
                <div class="profile-details">
                    <span class="profile-name">Shreya Patil</span>
                    <span class="profile-sub">Team Member</span>
                </div>
            </div>
        </div>
        """
    )

pages.run()