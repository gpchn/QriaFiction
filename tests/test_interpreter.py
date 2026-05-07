import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime


def run(src: str, runtime=None):
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    interp = Interpreter(runtime=runtime or Runtime())
    interp.run(ast)
    return interp


class TestInterpreter:
    def test_define_and_dialogue(self):
        src = 'define yuki = character(name="雪", avatar="", color="#87ceeb")\nyuki "hello"\n'
        interp = run(src)
        assert "yuki" in interp.runtime.characters

    def test_variables(self):
        src = 'var x = 42\n'
        interp = run(src)
        assert interp.runtime.get("x") == 42

    def test_set_add(self):
        src = 'var x = 10\nset x += 5\n'
        interp = run(src)
        assert interp.runtime.get("x") == 15

    def test_if_true(self):
        src = 'var x = 1\nif x > 0:\n    var result = "yes"\nend\n'
        interp = run(src)
        assert interp.runtime.get("result") == "yes"

    def test_if_false(self):
        src = 'var x = 1\nif x < 0:\n    var result = "no"\nend\n'
        interp = run(src)
        assert interp.runtime.get("result") is None

    def test_if_else(self):
        src = 'var x = -1\nif x > 0:\n    var result = "positive"\nelse:\n    var result = "negative"\nend\n'
        interp = run(src)
        assert interp.runtime.get("result") == "negative"

    def test_while_loop(self):
        src = 'var i = 0\nvar count = 0\nwhile i < 3:\n    set count += 1\n    set i += 1\nend\n'
        interp = run(src)
        assert interp.runtime.get("count") == 3

    def test_python_block(self):
        src = 'python:\n    qf.set("result", 123)\nend\n'
        interp = run(src)
        assert interp.runtime.get("result") == 123

    def test_python_cross_block_state(self):
        src = 'python:\n    my_var = 42\nend\npython:\n    qf.set("copied", my_var)\nend\n'
        interp = run(src)
        assert interp.runtime.get("copied") == 42

    def test_string_interpolation_var(self):
        from core.text_utils import interpolate_text
        runtime = Runtime()
        runtime.set("name", "Alice")
        result = interpolate_text("Hello {name}", runtime.get, None, None)
        assert result == "Hello Alice"

    def test_string_interpolation_python(self):
        from core.text_utils import interpolate_text
        result = interpolate_text("Result: {python: 2 + 3}", lambda n: None, None, None)
        assert result == "Result: 5"
