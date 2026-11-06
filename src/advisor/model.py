from langchain_openai import ChatOpenAI

from advisor.settings import AdvisorSettings


def get_model():
    settings = AdvisorSettings.from_env()

    return ChatOpenAI(
        model=settings.model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout,
        max_retries=1,
        use_responses_api=False,
    )