import streamlit as st

from ui.dashboard.components import DashboardHeader
from ui.dashboard.attribution import render_attribution_footer


def _use_suggested_prompt(suggested_prompt):
    st.session_state["advisor_question"] = suggested_prompt

if "advisor_messages" not in st.session_state:
    st.session_state["advisor_messages"] = [
        {
            "role": "assistant",
            "content": (
                "Hello! 👋 How can I help you today? You can ask about "
                "energy usage, savings, or building performance."
            ),
        }
    ]


DashboardHeader(
    "AI Advisor",
    "Your smart assistant for energy insights",
).initialize()

with st.container(border=True, key="advisor_chat"):
    st.subheader("Ask about your energy use")

    with st.container(key="advisor_conversation"):
        for message in st.session_state["advisor_messages"]:
            avatar = (
                ":material/robot:"
                if message["role"] == "assistant"
                else None
            )
            with st.chat_message(message["role"], avatar=avatar):
                st.write(message["content"])

    st.caption("Try asking:")

    prompts = [
        ("Top user", "Which building uses the most energy?"),
        ("Save energy", "How can I save more energy?"),
        ("Monthly report", "Show me last month's report"),
    ]

    prompt_cols = st.columns(3, gap="small")
    for index, (column, (label, prompt)) in enumerate(
        zip(prompt_cols, prompts)
    ):
        with column:
            st.button(
                label,
                key=f"advisor_prompt_{index}",
                on_click=_use_suggested_prompt,
                args=(prompt,),
                help=prompt,
                width="stretch",
            )

    with st.form("advisor_question_form", clear_on_submit=True):
        input_col, send_col = st.columns(
            [1, 0.22],
            gap="small",
            vertical_alignment="bottom",
        )

        with input_col:
            st.text_input(
                "Your question",
                key="advisor_question",
                label_visibility="collapsed",
                placeholder="Type your question...",
            )

        with send_col:
            st.form_submit_button(
                "Send",
                type="primary",
                width="stretch",
            )

render_attribution_footer()