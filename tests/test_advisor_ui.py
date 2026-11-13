"""Exercise advisor clicks across reruns without contacting the model provider."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.runtime.scriptrunner_utils.script_run_context import ScriptRunContext


PAGE = Path(__file__).parents[1] / "src/ui/dashboard/Advisor.py"
SEND = "FormSubmitter:advisor_question_form-Send"


@pytest.fixture
def chat(monkeypatch):
    agent = Mock()
    agent.invoke.return_value = {"messages": [SimpleNamespace(content="An answer.")]}
    factory = Mock(return_value=agent)
    monkeypatch.setattr("advisor.agent.get_agent", factory)
    app = AppTest.from_file(str(PAGE)).run()
    assert not app.exception
    return app, agent, factory


@pytest.mark.parametrize("index, expected", [
    (0, "Which buildings are available?"),
    (1, "How much electricity did Business 1 import"),
    (2, "Show Business 1's top 3"),
])
def test_suggestion_sends_once_without_needing_send(chat, index, expected):
    app, agent, _ = chat

    app.button(key=f"advisor_prompt_{index}").click().run()

    assert not app.exception
    agent.invoke.assert_called_once()
    message = agent.invoke.call_args.args[0]["messages"][0]
    assert message["role"] == "user"
    assert message["content"].startswith(expected)
    assert len(app.session_state["advisor_messages"]) == 2
    assert app.text_input(key="advisor_question").value == ""
    assert not any(button.key.startswith("advisor_prompt_") for button in app.button)
    assert "Try asking:" not in [caption.value for caption in app.caption]
    app.run()
    agent.invoke.assert_called_once()


def test_typed_followups_keep_working_after_suggestion_disappears(chat):
    app, agent, factory = chat
    thread = app.session_state["advisor_thread_id"]

    app.button(key="advisor_prompt_0").click().run()
    for question in ("What about October?", "And November?", "And November?", "List buildings again"):
        app.text_input(key="advisor_question").set_value(question)
        app.button(key=SEND).click().run()
        assert not app.exception
        assert app.text_input(key="advisor_question").value == ""
        assert agent.invoke.call_args.args[0] == {
            "messages": [{"role": "user", "content": question}],
        }

    assert agent.invoke.call_count == 5
    assert len(app.session_state["advisor_messages"]) == 10
    factory.assert_called_once()
    assert all(
        call.kwargs["config"]["configurable"]["thread_id"] == thread
        for call in agent.invoke.call_args_list
    )


def test_send_trims_question_and_ignores_empty_submissions(chat):
    app, agent, _ = chat
    app.text_input(key="advisor_question").set_value("  Explain kWh  ")
    app.button(key=SEND).click().run()
    assert agent.invoke.call_args.args[0]["messages"][0]["content"] == "Explain kWh"
    assert not any(button.key.startswith("advisor_prompt_") for button in app.button)
    assert "Try asking:" not in [caption.value for caption in app.caption]

    for blank in ("", "   "):
        app.text_input(key="advisor_question").set_value(blank)
        app.button(key=SEND).click().run()
    assert not app.exception
    agent.invoke.assert_called_once()
    assert len(app.session_state["advisor_messages"]) == 2


def test_new_conversation_clears_draft_history_and_agent(chat):
    app, agent, factory = chat
    app.button(key="advisor_prompt_0").click().run()
    thread = app.session_state["advisor_thread_id"]
    app.text_input(key="advisor_question").set_value("An unsent draft")
    app.button(key="advisor_reset").click().run()

    assert not app.exception
    assert app.session_state["advisor_messages"] == []
    assert app.session_state["advisor_thread_id"] != thread
    assert "advisor_agent" not in app.session_state
    assert app.text_input(key="advisor_question").value == ""
    agent.invoke.assert_called_once()
    assert sum(button.key.startswith("advisor_prompt_") for button in app.button) == 3
    assert "Try asking:" in [caption.value for caption in app.caption]

    app.button(key="advisor_prompt_0").click().run()
    assert agent.invoke.call_count == 2
    assert factory.call_count == 2


def test_failed_request_can_be_reset_and_submitted_again(chat):
    app, agent, _ = chat
    agent.invoke.side_effect = RuntimeError("private provider details")
    app.button(key="advisor_prompt_0").click().run()

    assert not app.exception
    assert app.session_state["advisor_failed"]
    assert app.text_input(key="advisor_question").disabled
    assert app.button(key=SEND).disabled
    assert not any(button.key.startswith("advisor_prompt_") for button in app.button)
    assert "private provider details" not in str(app.session_state["advisor_messages"])

    app.button(key="advisor_reset").click().run()
    agent.invoke.side_effect = None
    app.button(key="advisor_prompt_0").click().run()

    assert not app.exception
    assert not app.session_state["advisor_failed"]
    assert not app.text_input(key="advisor_question").disabled
    assert agent.invoke.call_count == 2


def test_blank_question_keeps_initial_suggestions(chat):
    app, agent, _ = chat
    app.text_input(key="advisor_question").set_value("   ")
    app.button(key=SEND).click().run()

    assert not app.exception
    agent.invoke.assert_not_called()
    assert sum(button.key.startswith("advisor_prompt_") for button in app.button) == 3
    assert "Try asking:" in [caption.value for caption in app.caption]


def test_composer_stays_in_same_slot_when_suggestions_disappear(chat):
    app, _, _ = chat
    conversation = next(
        block for block in app.main if getattr(block, "key", None) == "advisor_conversation"
    )
    assert len(conversation.button) == 3
    assert not conversation.text_input

    def form_path(block):
        for index, child in block.children.items():
            if child.type == "form":
                return (index,)
            if hasattr(child, "children"):
                nested = form_path(child)
                if nested is not None:
                    return (index, *nested)
        return None

    original_path = form_path(app.main)
    assert original_path is not None
    app.button(key="advisor_prompt_0").click().run()
    assert not app.exception
    assert form_path(app.main) == original_path
    assert len(app.get("form")) == 1
    assert len(app.text_input) == 1

    app.text_input(key="advisor_question").set_value("A follow-up question")
    app.button(key=SEND).click().run()
    assert not app.exception
    assert form_path(app.main) == original_path

    app.button(key="advisor_reset").click().run()
    assert form_path(app.main) == original_path


@pytest.mark.parametrize("suggestion", [0, 1, 2, None])
def test_suggestions_are_explicitly_cleared_before_model_starts(chat, monkeypatch, suggestion):
    app, agent, _ = chat
    events = []
    original_enqueue = ScriptRunContext.enqueue

    def record_delta(context, message):
        if message.HasField("delta"):
            delta = message.delta
            kind = delta.WhichOneof("type")
            if kind == "new_element":
                kind = delta.new_element.WhichOneof("type")
            events.append((tuple(message.metadata.delta_path), kind))
        original_enqueue(context, message)

    monkeypatch.setattr(ScriptRunContext, "enqueue", record_delta)
    app.run()
    welcome_path = next(path for path, kind in events if kind == "empty")
    events.clear()
    checked_during_generation = []

    def check_before_reply(*args, **kwargs):
        # Check updates already sent to the browser, before returning any answer.
        welcome_updates = [kind for path, kind in events if path == welcome_path]
        assert welcome_updates and welcome_updates[-1] == "empty"
        checked_during_generation.append(True)
        return {"messages": [SimpleNamespace(content="An answer.")]}

    agent.invoke.side_effect = check_before_reply
    if suggestion is None:
        app.text_input(key="advisor_question").set_value("List the buildings")
        app.button(key=SEND).click().run()
    else:
        app.button(key=f"advisor_prompt_{suggestion}").click().run()

    assert checked_during_generation == [True]
    assert not app.exception
    assert not app.session_state["advisor_failed"]
