import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.tokens import TokenType
from core.lexer import Lexer
from core.errors import LexerError
import pytest


def _types(tokens):
    """Extract token types, filtering out NEWLINE and EOF."""
    return [t.type for t in tokens if t.type not in (TokenType.EOF, TokenType.NEWLINE)]


class TestBasicTokens:
    """测试基本词法单元"""

    def test_empty(self):
        assert _types(Lexer("").tokenize()) == []

    def test_define_character(self):
        src = 'define yuki = character(name="雪", avatar="", color="#87ceeb")\n'
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.DEFINE in types
        assert TokenType.ASSIGN in types
        assert TokenType.CHARACTER in types
        assert TokenType.STRING in types

    def test_dialogue(self):
        src = 'yuki "早上好！"\n'
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.IDENTIFIER in types
        assert TokenType.STRING in types

    def test_narrator(self):
        src = '"那是一个普通的早晨..."\n'
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert len(types) == 1
        assert types[0] == TokenType.STRING

    def test_variable_declaration(self):
        src = "var relationship = 0\n"
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.VAR in types
        assert TokenType.ASSIGN in types
        assert TokenType.NUMBER in types

    def test_set_statement(self):
        src = "set relationship += 10\n"
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.SET in types
        assert TokenType.PLUS_ASSIGN in types

    def test_if_statement(self):
        src = "if relationship >= 50:\n"
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.IF in types
        assert TokenType.GREATER_EQUAL in types
        assert TokenType.COLON in types

    def test_label(self):
        src = "label start:\n"
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.LABEL in types
        assert TokenType.COLON in types

    def test_interact(self):
        src = """interact:
    "打招呼" -> greet (desc="向她问候")
    fallback "不知道"
end
"""
        tokens = Lexer(src).tokenize()
        types = _types(tokens)
        assert TokenType.INTERACT in types
        assert TokenType.FALLBACK in types
        assert TokenType.END in types


class TestOperators:
    """测试运算符"""

    def test_comparison_ops(self):
        src = "if a == b:\nend\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.EQUAL in tokens

    def test_assignment_ops(self):
        for op, tok_type in [
            ("+=", TokenType.PLUS_ASSIGN),
            ("-=", TokenType.MINUS_ASSIGN),
            ("*=", TokenType.MULTIPLY_ASSIGN),
            ("/=", TokenType.DIVIDE_ASSIGN),
        ]:
            tokens = [
                t.type
                for t in Lexer(f"var x = 1\nset x {op} 2\n").tokenize()
                if t.type not in (TokenType.NEWLINE, TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)
            ]
            assert tok_type in tokens

    def test_arithmetic_ops(self):
        src = "var x = a + b - c * d / e\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.PLUS in tokens
        assert TokenType.MINUS in tokens
        assert TokenType.MULTIPLY in tokens
        assert TokenType.DIVIDE in tokens

    def test_arrow_operator(self):
        src = '"Go" -> start (desc="go")\n'
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.ARROW in tokens

    def test_modulo_and_power(self):
        src = "var x = a % b\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.MODULO in tokens

    def test_not_equal_operator(self):
        src = "if a != b:\nend\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.NOT_EQUAL in tokens

    def test_less_equal_operator(self):
        src = "if a <= b:\nend\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.LESS_EQUAL in tokens

    def test_greater_equal_operator(self):
        src = "if a >= b:\nend\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.GREATER_EQUAL in tokens


class TestBooleans:
    """测试布尔值"""

    def test_true_keyword(self):
        tokens = _types(Lexer("var x = true\n").tokenize())
        assert TokenType.TRUE in tokens

    def test_false_keyword(self):
        tokens = _types(Lexer("var x = false\n").tokenize())
        assert TokenType.FALSE in tokens

    def test_and_or_not(self):
        tokens = _types(Lexer("if a and b or not c:\nend\n").tokenize())
        assert TokenType.AND in tokens
        assert TokenType.OR in tokens
        assert TokenType.NOT in tokens


class TestIdentifiers:
    """测试标识符"""

    def test_dotted_label(self):
        tokens = _types(Lexer("jump chapter.start\n").tokenize())
        assert any(t.value == "chapter.start" for t in Lexer("jump chapter.start\n").tokenize())

    def test_dotted_call(self):
        tokens = _types(Lexer("call events.greeting\n").tokenize())
        assert any(t.value == "events.greeting" for t in Lexer("call events.greeting\n").tokenize())

    def test_underscore_identifier(self):
        tokens = Lexer("var _private = 1\n").tokenize()
        id_tok = next(t for t in tokens if t.type == TokenType.IDENTIFIER)
        assert id_tok.value == "_private"

    def test_mixed_alphanumeric_identifier(self):
        tokens = Lexer("var player1 = 1\n").tokenize()
        id_tok = next(t for t in tokens if t.type == TokenType.IDENTIFIER)
        assert id_tok.value == "player1"


class TestStrings:
    """测试字符串"""

    def test_string_with_escapes(self):
        src = '"hello\\nworld"\n'
        tokens = Lexer(src).tokenize()
        assert tokens[0].value == "hello\nworld"

    def test_single_quote_string(self):
        src = "'hello\\'world'\n"
        tokens = Lexer(src).tokenize()
        assert tokens[0].value == "hello'world"

    def test_empty_string(self):
        tokens = Lexer('""\n').tokenize()
        assert tokens[0].value == ""

    def test_string_with_newline(self):
        tokens = Lexer('"hello\\nworld"\n').tokenize()
        assert tokens[0].value == "hello\nworld"

    def test_string_with_tab(self):
        tokens = Lexer('"hello\\tworld"\n').tokenize()
        assert tokens[0].value == "hello\tworld"

    def test_string_with_backslash(self):
        tokens = Lexer('"hello\\\\world"\n').tokenize()
        assert tokens[0].value == "hello\\world"

    def test_string_with_escaped_quote(self):
        tokens = Lexer('"say \\"hi\\""\n').tokenize()
        assert tokens[0].value == 'say "hi"'

    def test_single_quoted_string(self):
        tokens = Lexer("'hello world'\n").tokenize()
        assert tokens[0].value == "hello world"

    def test_single_quoted_with_escaped_apostrophe(self):
        tokens = Lexer("'hello\\'s world'\n").tokenize()
        assert tokens[0].value == "hello's world"

    def test_interpolation_markers(self):
        tokens = Lexer('"Hello {name}, you are {age} years old"\n').tokenize()
        assert "{name}" in tokens[0].value
        assert "{age}" in tokens[0].value


class TestNumbers:
    """测试数字"""

    def test_integer(self):
        tokens = Lexer("var x = 42\n").tokenize()
        num_tok = next(t for t in tokens if t.type == TokenType.NUMBER)
        assert num_tok.value == 42

    def test_float(self):
        tokens = Lexer("var x = 3.14\n").tokenize()
        num_tok = next(t for t in tokens if t.type == TokenType.NUMBER)
        assert num_tok.value == 3.14

    def test_zero(self):
        tokens = Lexer("var x = 0\n").tokenize()
        num_tok = next(t for t in tokens if t.type == TokenType.NUMBER)
        assert num_tok.value == 0


class TestIndentation:
    """测试缩进"""

    def test_indent_dedent(self):
        src = "label start:\n    yuki \"hi\"\nend\n"
        tokens = Lexer(src).tokenize()
        types = [t.type for t in tokens]
        assert TokenType.INDENT in types
        assert TokenType.DEDENT in types

    def test_multiple_indent_levels(self):
        src = "if true:\n    if true:\n        yuki \"hi\"\n    end\nend\n"
        tokens = Lexer(src).tokenize()
        indent_count = sum(1 for t in tokens if t.type == TokenType.INDENT)
        assert indent_count == 2

    def test_tabs_converted_to_spaces(self):
        src = "label start:\n\tyuki \"hi\"\nend\n"
        tokens = Lexer(src).tokenize()
        indent_tok = next(t for t in tokens if t.type == TokenType.INDENT)
        assert indent_tok.value == 4


class TestComments:
    """测试注释"""

    def test_full_line_comment(self):
        tokens = Lexer("# this is a comment\n").tokenize()
        content_types = _types(tokens)
        assert len(content_types) == 0

    def test_inline_comment(self):
        src = 'yuki "hello" # comment\n'
        tokens = Lexer(src).tokenize()
        string_tok = next(t for t in tokens if t.type == TokenType.STRING)
        assert string_tok.value == "hello"

    def test_comment_after_string(self):
        src = '"hello # not a string terminator"\n'
        tokens = Lexer(src).tokenize()
        assert tokens[0].value == "hello # not a string terminator"

    def test_comment_in_python_block_not_stripped(self):
        src = 'python:\n    # this is python comment\n    x = 1\nend\n'
        tokens = Lexer(src).tokenize()
        py_tok = next(t for t in tokens if t.type == TokenType.PYTHON_CODE)
        assert "python comment" in py_tok.value


class TestPythonBlock:
    """测试Python块"""

    def test_python_block_code_capture(self):
        src = 'python:\n    import random\n    x = 1\nend\n'
        tokens = Lexer(src).tokenize()
        py_tok = next(t for t in tokens if t.type == TokenType.PYTHON_CODE)
        assert "import random" in py_tok.value
        assert "x = 1" in py_tok.value

    def test_python_block_with_empty_lines(self):
        src = 'python:\n    x = 1\n\n    y = 2\nend\n'
        tokens = Lexer(src).tokenize()
        py_tok = next(t for t in tokens if t.type == TokenType.PYTHON_CODE)
        assert "x = 1" in py_tok.value
        assert "y = 2" in py_tok.value


class TestAudioKeywords:
    """测试音频关键字"""

    def test_music_keyword(self):
        tokens = _types(Lexer('music "bgm.mp3"\n').tokenize())
        assert TokenType.MUSIC in tokens

    def test_sound_keyword(self):
        tokens = _types(Lexer('sound "sfx.wav"\n').tokenize())
        assert TokenType.SOUND in tokens

    def test_stop_keyword(self):
        tokens = _types(Lexer("stop music\n").tokenize())
        assert TokenType.STOP in tokens

    def test_volume_keyword(self):
        tokens = _types(Lexer("volume music = 0.7\n").tokenize())
        assert TokenType.VOLUME in tokens

    def test_fade_keyword(self):
        tokens = _types(Lexer('music "bgm.mp3" with fade 2.0\n').tokenize())
        assert TokenType.FADE in tokens

    def test_loop_keyword(self):
        tokens = _types(Lexer('music "bgm.mp3" loop false\n').tokenize())
        assert TokenType.LOOP in tokens


class TestSystemKeywords:
    """测试系统关键字"""

    def test_options_keyword(self):
        tokens = _types(Lexer("options:\nend\n").tokenize())
        assert TokenType.OPTIONS in tokens

    def test_save_keyword(self):
        tokens = _types(Lexer("save\n").tokenize())
        assert TokenType.SAVE in tokens

    def test_load_keyword(self):
        tokens = _types(Lexer("load\n").tokenize())
        assert TokenType.LOAD in tokens

    def test_quit_keyword(self):
        tokens = _types(Lexer("quit\n").tokenize())
        assert TokenType.QUIT in tokens

    def test_wait_keyword(self):
        tokens = _types(Lexer("wait 1.5\n").tokenize())
        assert TokenType.WAIT in tokens

    def test_wait_click(self):
        tokens = _types(Lexer("wait click\n").tokenize())
        assert TokenType.WAIT in tokens
        assert TokenType.CLICK in tokens


class TestLexerErrors:
    """测试词法错误"""

    def test_unknown_character_raises_error(self):
        with pytest.raises(LexerError):
            Lexer("@invalid\n").tokenize()

    def test_error_contains_line_info(self):
        try:
            Lexer("@bad\n").tokenize()
            assert False, "Should have raised"
        except LexerError as e:
            assert e.line == 1
            assert e.col >= 1


class TestEdgeCases:
    """测试边界情况"""

    def test_only_whitespace(self):
        tokens = Lexer("   \n  \n").tokenize()
        content_types = _types(tokens)
        assert len(content_types) == 0

    def test_boolean_not_keyword(self):
        src = "var x = not y\n"
        tokens = _types(Lexer(src).tokenize())
        assert TokenType.NOT in tokens

    def test_comment(self):
        src = "# this is a comment\n"
        tokens = Lexer(src).tokenize()
        assert _types(tokens) == []
