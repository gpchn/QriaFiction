import random


class AIMatcher:
    def __call__(self, user_input: str, actions: list, runtime, engine) -> str | None:
        raise NotImplementedError

    def _parse(self, response: str) -> str | None:
        text = response.strip().strip('"').strip("'").upper()
        if text == "NONE":
            return None
        for action in actions if hasattr(self, '_last_actions') else []:
            if action.name.upper() == text:
                return action.name
        return text if text else None


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
