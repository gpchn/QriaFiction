import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.ai_matchers import (
    OpenAIMatcher, DeepSeekMatcher, CustomMatcher,
    SimpleKeywordMatcher, get_matcher, get_all_matcher_names,
)


class TestMatchers:
    """测试AI匹配器"""

    def test_parse_exact(self):
        matcher = OpenAIMatcher()
        matcher._last_actions = [type('A', (), {'name': 'greet'})()]
        assert matcher._parse("greet") == "greet"

    def test_parse_case_insensitive(self):
        matcher = OpenAIMatcher()
        matcher._last_actions = [type('A', (), {'name': 'greet'})()]
        assert matcher._parse("GREET") == "greet"

    def test_parse_quoted(self):
        matcher = OpenAIMatcher()
        matcher._last_actions = [type('A', (), {'name': 'greet'})()]
        assert matcher._parse('"greet"') == "greet"

    def test_parse_none_variants(self):
        matcher = OpenAIMatcher()
        assert matcher._parse("NONE") is None
        assert matcher._parse("null") is None
        assert matcher._parse("no match") is None
        assert matcher._parse("无") is None

    def test_parse_markdown_block(self):
        matcher = OpenAIMatcher()
        matcher._last_actions = [type('A', (), {'name': 'greet'})()]
        assert matcher._parse("```text\ngreet\n```") == "greet"

    def test_keyword_matcher(self):
        action = type('A', (), {'name': 'greet', 'desc': 'say hello'})()
        matcher = SimpleKeywordMatcher()
        result = matcher("hello there", [action], None, None)
        assert result == "greet"

    def test_keyword_no_match(self):
        action = type('A', (), {'name': 'greet', 'desc': 'say hello'})()
        matcher = SimpleKeywordMatcher()
        result = matcher("I want to leave", [action], None, None)
        assert result is None

    def test_get_matcher(self):
        assert isinstance(get_matcher("openai"), OpenAIMatcher)
        assert isinstance(get_matcher("deepseek"), DeepSeekMatcher)
        assert isinstance(get_matcher("custom"), CustomMatcher)
        assert isinstance(get_matcher("keyword"), SimpleKeywordMatcher)
        assert isinstance(get_matcher("unknown"), SimpleKeywordMatcher)

    def test_get_all_matcher_names(self):
        names = get_all_matcher_names()
        assert "openai" in names
        assert "deepseek" in names
        assert "custom" in names
        assert "keyword" in names
