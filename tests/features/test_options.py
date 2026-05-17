import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.ast import OptionsStmt, OptionItem
from core.interpreter import Interpreter
from core.runtime import Runtime


def parse(src):
    tokens = Lexer(src).tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestOptionsLexer:
    """测试选项词法"""

    def test_options_keyword(self):
        src = "options:\nend\n"
        tokens = Lexer(src).tokenize()
        types = [t.type.name for t in tokens]
        assert types == ["OPTIONS", "COLON", "NEWLINE", "END", "NEWLINE", "EOF"]

    def test_options_with_items(self):
        src = '''options:
    "Go" -> go (desc="Go to the city")
    "Stay" -> stay (desc="Stay at home")
end
'''
        tokens = Lexer(src).tokenize()
        types = [t.type.name for t in tokens]
        assert "OPTIONS" in types
        assert "COLON" in types
        assert "END" in types


class TestOptionsParser:
    """测试选项语法解析"""

    def test_options_basic(self):
        src = '''options:
    "Go" -> go (desc="Go to the city")
    "Stay" -> stay (desc="Stay at home")
end
'''
        program = parse(src)
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, OptionsStmt)
        assert len(stmt.items) == 2
        assert stmt.items[0].text == "Go"
        assert stmt.items[0].label == "go"
        assert stmt.items[0].desc == "Go to the city"
        assert stmt.items[1].text == "Stay"
        assert stmt.items[1].label == "stay"
        assert stmt.items[1].desc == "Stay at home"

    def test_options_with_condition(self):
        src = '''options:
    "Enter" -> enter (desc="Enter the door", condition=has_key)
    "Leave" -> leave (desc="Leave")
end
'''
        program = parse(src)
        stmt = program.statements[0]
        assert isinstance(stmt, OptionsStmt)
        assert len(stmt.items) == 2
        assert stmt.items[0].condition is not None
        assert stmt.items[1].condition is None

    def test_options_in_label(self):
        src = '''label start:
    options:
        "A" -> a (desc="Choice A")
        "B" -> b (desc="Choice B")
    end
end
'''
        program = parse(src)
        label_stmt = program.statements[0]
        assert len(label_stmt.body) == 1
        assert isinstance(label_stmt.body[0], OptionsStmt)

    def test_options_empty_raises(self):
        src = "options:\nend\n"
        tokens = Lexer(src).tokenize()
        parser = Parser(tokens)
        try:
            parser.parse()
            assert False, "Should raise exception"
        except Exception:
            pass

    def test_options_three_items(self):
        src = '''options:
    "School" -> school (desc="Go to school")
    "Home" -> home (desc="Stay home")
    "Park" -> park (desc="Go to park")
end
'''
        program = parse(src)
        stmt = program.statements[0]
        assert len(stmt.items) == 3


class TestOptionsInterpreter:
    """测试选项解释器"""

    def test_options_sets_pending(self):
        src = '''options:
    "Go" -> go (desc="Go to the city")
    "Stay" -> stay (desc="Stay at home")
end
'''
        interp = Interpreter(runtime=Runtime())
        interp.run(parse(src))
        assert interp.runtime.pending_options is not None
        assert len(interp.runtime.pending_options["items"]) == 2
        assert interp.runtime.pending_options["items"][0].text == "Go"
