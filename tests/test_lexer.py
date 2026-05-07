import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.tokens import TokenType
from core.lexer import Lexer


def _types(tokens):
    return [t.type for t in tokens if t.type != TokenType.EOF and t.type != TokenType.NEWLINE]


class TestLexer:
    def test_empty(self):
        tokens = Lexer("").tokenize()
        assert _types(tokens) == []

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

    def test_string_with_escapes(self):
        src = '"hello\\nworld"\n'
        tokens = Lexer(src).tokenize()
        assert tokens[0].value == "hello\nworld"

    def test_single_quote_string(self):
        src = "'hello\\'world'\n"
        tokens = Lexer(src).tokenize()
        assert tokens[0].value == "hello'world"

    def test_comment(self):
        src = "# this is a comment\n"
        tokens = Lexer(src).tokenize()
        assert _types(tokens) == []

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
