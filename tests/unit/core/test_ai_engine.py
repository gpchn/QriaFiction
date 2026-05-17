import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.ai_engine import AIEngine


class TestAIEngine:
    """测试AI引擎"""

    def test_init_default(self):
        engine = AIEngine()
        assert engine.provider == "openai"
        assert engine.model == "gpt-4o-mini"
        assert engine.api_key == ""

    def test_init_with_config(self):
        config = {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": "test-key",
        }
        engine = AIEngine(config)
        assert engine.provider == "deepseek"
        assert engine.model == "deepseek-chat"
        assert engine.api_key == "test-key"

    def test_match_action_uses_keyword_matcher(self):
        """测试 match_action 使用关键字匹配器"""
        engine = AIEngine({"provider": "keyword"})
        action = type('A', (), {'name': 'greet', 'desc': 'say hello'})()
        result = engine.match_action("hello there", [action], None)
        assert result == "greet"

    def test_match_action_no_match(self):
        """测试 match_action 无匹配"""
        engine = AIEngine({"provider": "keyword"})
        action = type('A', (), {'name': 'greet', 'desc': 'say hello'})()
        result = engine.match_action("goodbye", [action], None)
        assert result is None


class TestBuildPrompt:
    """测试构建提示"""

    def test_build_prompt_basic(self):
        engine = AIEngine()
        from core.runtime import Runtime, Character
        runtime = Runtime()
        runtime.add_character("yuki", Character(name="雪", avatar="", color="#87ceeb"))
        runtime.current_label = "start"
        
        action = type('A', (), {'name': 'greet', 'desc': 'say hello'})()
        prompt = engine._build_prompt("你好", [action], runtime)
        
        assert "互动小说" in prompt
        assert "雪" in prompt
        assert "start" in prompt
        assert "greet" in prompt
        assert "say hello" in prompt
        assert "你好" in prompt
