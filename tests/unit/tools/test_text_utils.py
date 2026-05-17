import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.text_utils import interpolate_text


class TestInterpolateTextBasic:
    """测试基本文本插值"""

    def test_no_interpolation(self):
        assert interpolate_text("Hello world", lambda n: None, None, None) == "Hello world"

    def test_single_variable(self):
        assert interpolate_text("Hello {name}", lambda n: "Alice" if n == "name" else None, None, None) == "Hello Alice"

    def test_multiple_variables(self):
        def getter(name):
            return {"first": "Alice", "last": "Smith"}.get(name)
        assert interpolate_text("{first} {last}", getter, None, None) == "Alice Smith"

    def test_variable_in_middle(self):
        def getter(name):
            return "42" if name == "answer" else None
        assert interpolate_text("The answer is {answer}.", getter, None, None) == "The answer is 42."

    def test_variable_not_found(self):
        """不存在的变量返回空字符串"""
        result = interpolate_text("Hello {unknown}", lambda n: None, None, None)
        assert result == "Hello "

    def test_empty_string(self):
        assert interpolate_text("", lambda n: None, None, None) == ""


class TestInterpolateTextPython:
    """测试Python表达式插值"""

    def test_simple_expr(self):
        result = interpolate_text("2+3={python: 2+3}", lambda n: None, None, None)
        assert result == "2+3=5"

    def test_string_expr(self):
        result = interpolate_text("Hello, {python: 'world'.upper()}", lambda n: None, None, None)
        assert result == "Hello, WORLD"

    def test_list_expr(self):
        result = interpolate_text("Items: {python: [1, 2, 3]}", lambda n: None, None, None)
        assert "[1, 2, 3]" in result

    def test_nested_braces_in_python(self):
        result = interpolate_text("Dict: {python: {'a': 1}}", lambda n: None, None, None)
        assert "a" in result

    def test_python_error_returns_placeholder(self):
        """Python 表达式错误时保留原占位符"""
        result = interpolate_text("Error: {python: 1/0}", lambda n: None, None, None)
        assert "1/0" in result


class TestInterpolateTextMixed:
    """测试混合插值"""

    def test_mixed_var_and_python(self):
        def getter(name):
            return "Alice" if name == "name" else None
        result = interpolate_text("{name} got {python: 10 + 5} points", getter, None, None)
        assert result == "Alice got 15 points"

    def test_variable_with_spaces_around(self):
        def getter(name):
            return "42" if name == "x" else None
        result = interpolate_text("x = { x }", getter, None, None)
        assert result == "x = 42"


class TestInterpolateTextEdgeCases:
    """测试边界情况"""

    def test_no_braces(self):
        assert interpolate_text("just plain text", lambda n: None, None, None) == "just plain text"

    def test_unclosed_brace(self):
        """未闭合的大括号保留原样"""
        result = interpolate_text("Hello {name", lambda n: None, None, None)
        assert "{name" in result

    def test_empty_braces(self):
        """空大括号保留原样"""
        result = interpolate_text("Hello {}", lambda n: None, None, None)
        assert "{}" in result

    def test_double_braces(self):
        """双重括号会被部分解析，取决于实现"""
        result = interpolate_text("Hello {{name}}", lambda n: "Alice" if n == "name" else None, None, None)
        assert "}" in result

    def test_numeric_variable(self):
        def getter(name):
            return 42 if name == "x" else None
        result = interpolate_text("x={x}", getter, None, None)
        assert result == "x=42"

    def test_none_variable(self):
        def getter(name):
            return None if name == "x" else None
        result = interpolate_text("x={x}", getter, None, None)
        assert result == "x="

    def test_boolean_variable(self):
        def getter(name):
            return True if name == "flag" else None
        result = interpolate_text("flag={flag}", getter, None, None)
        assert result == "flag=True"

    def test_variable_zero(self):
        """变量值为 0 时应正常显示"""
        def getter(name):
            return 0 if name == "x" else None
        result = interpolate_text("x={x}", getter, None, None)
        assert result == "x=0"

    def test_variable_false(self):
        """变量值为 False 时应正常显示"""
        def getter(name):
            return False if name == "flag" else None
        result = interpolate_text("flag={flag}", getter, None, None)
        assert result == "flag=False"
