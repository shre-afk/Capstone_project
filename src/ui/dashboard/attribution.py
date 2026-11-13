import streamlit as st


def render_attribution_footer():
    """Render the project institution and developer attribution."""
    st.markdown(
        """
        <footer class="institution-attribution">
            <span>Developed at Fachhochschule Dortmund</span>
            <span>Shreya Patil · Ourvish Lofur · Joywin Bennis</span>
        </footer>
        """,
        unsafe_allow_html=True,
    )
