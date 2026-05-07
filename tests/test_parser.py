import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.ast import *


def parse(src: str) -> Program:
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse()


class TestParser:
    def test_empty(self):
        prog = parse("")
        assert isinstance(prog, Program)
        assert len(prog.statements) == 0

    def test_dialogue(self):
        prog = parse('yuki "你好！"\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, DialogueStmt)
        assert stmt.character == "yuki"
        assert stmt.text == "你好！"

    def test_define(self):
        prog = parse('define yuki = character(name="雪", avatar="", color="#87ceeb")\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, DefineCharacterStmt)
        assert stmt.name == "yuki"
        assert stmt.display_name == "雪"
        assert stmt.color == "#87ceeb"

    def test_label(self):
        prog = parse('label start:\n    yuki "hi"\nend\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, LabelStmt)
        assert stmt.name == "start"
        assert len(stmt.body) == 1

    def test_var_and_set(self):
        prog = parse('var x = 0\nset x += 1\n')
        assert len(prog.statements) == 2
        assert isinstance(prog.statements[0], VarStmt)
        assert isinstance(prog.statements[1], SetStmt)

    def test_if_else(self):
        prog = parse('if x > 0:\n    yuki "positive"\nelse:\n    yuki "negative"\nend\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.branches) == 1
        assert stmt.else_body is not None

    def test_while(self):
        prog = parse('while i < 3:\n    set i += 1\nend\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, WhileStmt)

    def test_jump(self):
        prog = parse('jump start\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.target == "start"

    def test_jump_with_condition(self):
        prog = parse('jump start if flag == true\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.condition is not None

    def test_interact(self):
        prog = parse('interact:\n    "打招呼" -> greet (desc="你好")\n    fallback "不知道"\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, InteractStmt)
        assert len(stmt.actions) == 1
        assert len(stmt.fallbacks) == 1

    def test_python_block(self):
        src = 'python:\n    import random\n    dice = random.randint(1, 6)\nend\n'
        prog = parse(src)
        stmt = prog.statements[0]
        assert isinstance(stmt, PythonBlockStmt)
        assert "import random" in stmt.code

    def test_break_continue(self):
        prog = parse('break\ncontinue\n')
        assert len(prog.statements) == 2
        assert isinstance(prog.statements[0], BreakStmt)
        assert isinstance(prog.statements[1], ContinueStmt)
