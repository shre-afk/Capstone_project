"""Configuration object for the advisor's language, style, and instructions."""


class AdvisorSettings:
    def __init__(self, language="en", response_style="concise", system_prompt=None):
        self.configure(language, response_style)
        self.set_system_prompt(
            system_prompt if system_prompt is not None else
            "You are an energy advisor for German buildings. Explain the supplied "
            "analytical results using their units. Distinguish observations from "
            "possible causes. Do not invent readings or guarantee energy savings."
        )

    def configure(self, language, response_style):
        """Validate both configuration values before changing existing state."""
        if language not in ("en", "de"):
            raise ValueError("language must be 'en' or 'de'")
        if response_style not in ("concise", "detailed"):
            raise ValueError("response style must be 'concise' or 'detailed'")
        self._language = language
        self._response_style = response_style

    def get_language(self):
        return self._language

    def get_response_style(self):
        return self._response_style

    def get_system_prompt(self):
        return self._system_prompt

    def set_language(self, language):
        self.configure(language, self._response_style)

    def set_response_style(self, response_style):
        self.configure(self._language, response_style)

    def set_system_prompt(self, system_prompt):
        if not isinstance(system_prompt, str) or not system_prompt.strip():
            raise ValueError("the advisor needs a nonempty system prompt")
        self._system_prompt = system_prompt.strip()

    def build_system_message(self):
        language = "English" if self._language == "en" else "German"
        return (f"{self._system_prompt}\n"
                f"Respond in {language}. Use a {self._response_style} explanation.")
