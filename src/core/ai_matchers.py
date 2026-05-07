import random


class AIMatcher:
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        raise NotImplementedError

    def _parse(self, response: str) -> str | None:
        text = response.strip()

        if not text or text.upper() in ("NONE", "NULL", "NO_MATCH", "NO MATCH", "N/A", "无", "无匹配"):
            return None

        text = text.strip('"').strip("'").strip()

        if text.startswith("```"):
            lines = text.split("\n")
            for line in lines:
                line = line.strip().strip("```").strip()
                if line and not line.startswith("json") and not line.startswith("text"):
                    text = line
                    break

        for action in getattr(self, '_last_actions', []):
            name_upper = action.name.upper()
            if text.upper() == name_upper:
                return action.name
            if name_upper in text.upper() and len(text) < len(action.name) + 10:
                return action.name

        if text and len(text) < 50:
            return text

        return None


class OpenAIMatcher(AIMatcher):
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        self._last_actions = actions
        prompt = engine._build_prompt(user_input, actions, runtime)
        response = engine._call_openai(prompt)
        return self._parse(response)


class DeepSeekMatcher(AIMatcher):
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        self._last_actions = actions
        prompt = engine._build_prompt(user_input, actions, runtime)
        response = engine._call_deepseek(prompt)
        return self._parse(response)


class CustomMatcher(AIMatcher):
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        self._last_actions = actions
        prompt = engine._build_prompt(user_input, actions, runtime)
        response = engine._call_custom(prompt)
        return self._parse(response)


class SimpleKeywordMatcher(AIMatcher):
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        user_lower = user_input.lower()
        for action in actions:
            keywords = action.desc.lower().split()
            if any(kw in user_lower for kw in keywords if len(kw) > 1):
                return action.name
        return None


_matchers = {
    "openai": OpenAIMatcher(),
    "deepseek": DeepSeekMatcher(),
    "custom": CustomMatcher(),
    "keyword": SimpleKeywordMatcher(),
}


def get_matcher(provider: str) -> AIMatcher:
    return _matchers.get(provider, SimpleKeywordMatcher())


def get_all_matcher_names() -> list:
    return list(_matchers.keys())
