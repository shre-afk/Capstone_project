"""Dashboard-themed chat connected to the portfolio energy advisor."""

from uuid import uuid4

import streamlit as st

from advisor.agent import get_agent
from ui.dashboard.attribution import render_attribution_footer
from ui.dashboard.components import DashboardHeader


def new_conversation():
    for key in (
        "advisor_agent", "advisor_thread_id", "advisor_messages",
        "advisor_failed", "advisor_question", "advisor_pending_question",
    ):
        st.session_state.pop(key, None)


def use_suggested_prompt(prompt):
    st.session_state["advisor_pending_question"] = prompt
    st.session_state["advisor_question"] = ""


def submit_question():
    question = st.session_state.get("advisor_question", "").strip()
    if question:
        st.session_state["advisor_pending_question"] = question
    st.session_state["advisor_question"] = ""


st.session_state.setdefault("advisor_messages", [])
st.session_state.setdefault("advisor_thread_id", uuid4().hex)
st.session_state.setdefault("advisor_failed", False)
question = st.session_state.pop("advisor_pending_question", None)
busy = question is not None

DashboardHeader(
    "AI Advisor",
    "Your smart assistant for energy insights",
).initialize()

with st.container(border=True, key="advisor_chat", width="stretch"):
    with st.container(
        horizontal=True,
        horizontal_alignment="distribute",
        vertical_alignment="center",
        key="advisor_toolbar",
    ):
        st.subheader("Ask about your energy use", width="content")
        st.button(
            "New conversation",
            key="advisor_reset",
            icon=":material/restart_alt:",
            on_click=new_conversation,
        )

    conversation = st.container(
        key="advisor_conversation", height=520, width="stretch", border=False, autoscroll=True,
    )
    with conversation:
        welcome = st.empty()
        if not st.session_state.advisor_messages and not busy:
            with welcome.container():
                with st.chat_message("assistant", avatar=":material/robot:"):
                    st.markdown(
                        "Hello! I can help you explore your buildings, electricity "
                        "usage, estimated costs and peak periods. Choose a suggestion "
                        "below or ask a question about a building and date range."
                    )
                st.caption("Try asking:")
                prompts = [
                    ("Buildings", "Which buildings are available? List their IDs and names."),
                    ("Consumption", "How much electricity did Business 1 import in November 2016? Include estimated cost and data completeness."),
                    ("Peak usage", "Show Business 1's top 3 electricity-import hours and days in November 2016. Include data coverage."),
                ]
                for index, (column, (label, prompt)) in enumerate(zip(st.columns(3, gap="small"), prompts)):
                    with column:
                        st.button(
                            label,
                            key=f"advisor_prompt_{index}",
                            on_click=use_suggested_prompt,
                            args=(prompt,),
                            width="stretch",
                        )

        for message in st.session_state.advisor_messages:
            avatar = ":material/robot:" if message["role"] == "assistant" else None
            with st.chat_message(message["role"], avatar=avatar):
                if message.get("error"):
                    st.error(message["content"])
                else:
                    st.markdown(message["content"])

    with st.form("advisor_question_form", width="stretch"):
        with st.container(
            horizontal=True, gap="small", vertical_alignment="bottom",
            key="advisor_composer", width="stretch",
        ):
            st.text_input(
                "Your question",
                key="advisor_question",
                label_visibility="collapsed",
                placeholder="Ask about a building or historical period…",
                max_chars=4000,
                width="stretch",
                disabled=busy or st.session_state.advisor_failed,
            )
            st.form_submit_button(
                "Send",
                type="primary",
                width="content",
                on_click=submit_question,
                disabled=busy or st.session_state.advisor_failed,
            )

    st.caption(
        "Historical grid-import data · Berlin time · Estimated costs use an assumed tariff. "
        "Stored readings may include reconstructed intervals."
    )
    if st.session_state.advisor_failed:
        st.info("Select New conversation to start again.")

if question and not st.session_state.advisor_failed:
    st.session_state.advisor_messages.append({"role": "user", "content": question})
    with conversation:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar=":material/robot:"):
            try:
                with st.spinner("Checking your question…"):
                    if "advisor_agent" not in st.session_state:
                        st.session_state.advisor_agent = get_agent()
                    result = st.session_state.advisor_agent.invoke(
                        {"messages": [{"role": "user", "content": question}]},
                        config={
                            "configurable": {"thread_id": st.session_state.advisor_thread_id},
                            "recursion_limit": 20,
                        },
                    )
                    response = result["messages"][-1]
                    answer = response.content if isinstance(response.content, str) else response.text
                    if not answer.strip():
                        raise ValueError("The model returned no answer.")
            except Exception:
                # Provider errors can expose request details. Restart failed checkpoints safely.
                st.session_state.advisor_failed = True
                st.session_state.advisor_messages.append({
                    "role": "assistant",
                    "content": (
                        "The request could not be completed. Check your connection, "
                        "KI Connect configuration and imported data, then start a new conversation."
                    ),
                    "error": True,
                })
            else:
                st.session_state.advisor_messages.append({"role": "assistant", "content": answer})
    st.rerun()

render_attribution_footer()
