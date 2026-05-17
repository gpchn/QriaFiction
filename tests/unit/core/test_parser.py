import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.ast import *
from core.errors import QFSyntaxError
import pytest


def parse(src: str) -> Program:
    tokens = Lexer(src).tokenize()
    return Parser(tokens).parse()


class TestBasicStatements:
    """测试基本语句解析"""

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

    def test_break_continue(self):
        prog = parse('break\ncontinue\n')
        assert len(prog.statements) == 2
        assert isinstance(prog.statements[0], BreakStmt)
        assert isinstance(prog.statements[1], ContinueStmt)


class TestConditionals:
    """测试条件语句"""

    def test_if_else(self):
        prog = parse('if x > 0:\n    yuki "positive"\nelse:\n    yuki "negative"\nend\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.branches) == 1
        assert stmt.else_body is not None

    def test_if_elif_else(self):
        prog = parse('if x > 0:\n    yuki "positive"\nelseif x < 0:\n    yuki "negative"\nelse:\n    yuki "zero"\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.branches) == 2
        assert stmt.else_body is not None

    def test_if_only(self):
        prog = parse('if x > 0:\n    yuki "hi"\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStmt)
        assert len(stmt.branches) == 1
        assert stmt.else_body == []

    def test_nested_if(self):
        prog = parse('if a:\n    if b:\n        yuki "nested"\n    end\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStmt)
        inner = stmt.branches[0].body[0]
        assert isinstance(inner, IfStmt)


class TestLoops:
    """测试循环语句"""

    def test_while(self):
        prog = parse('while i < 3:\n    set i += 1\nend\n')
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, WhileStmt)


class TestJumpAndCall:
    """测试跳转和调用"""

    def test_jump_basic(self):
        prog = parse('jump start\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.target == "start"
        assert stmt.condition is None
        assert not stmt.is_otherwise

    def test_jump_with_condition(self):
        prog = parse('jump start if flag == true\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.condition is not None

    def test_jump_with_if(self):
        prog = parse('jump scene_a if flag == true\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.condition is not None

    def test_jump_otherwise(self):
        prog = parse('jump scene_b otherwise\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, JumpStmt)
        assert stmt.is_otherwise

    def test_jump_dotted_label(self):
        prog = parse('jump chapter.start\n')
        stmt = prog.statements[0]
        assert stmt.target == "chapter.start"

    def test_call_basic(self):
        prog = parse('call daily_event\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, CallStmt)
        assert stmt.target == "daily_event"
        assert stmt.condition is None

    def test_call_with_condition(self):
        prog = parse('call intro if day == 1\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, CallStmt)
        assert stmt.condition is not None

    def test_return(self):
        prog = parse('return\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, ReturnStmt)


class TestInteract:
    """测试交互语句"""

    def test_interact(self):
        prog = parse('interact:\n    "打招呼" -> greet (desc="你好")\n    fallback "不知道"\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, InteractStmt)
        assert len(stmt.actions) == 1
        assert len(stmt.fallbacks) == 1

    def test_interact_multiple_actions(self):
        src = '''interact:
    "Greet" -> greet (desc="say hello")
    "Ask" -> ask (desc="ask a question")
    "Leave" -> leave (desc="say goodbye")
    fallback "She doesn't understand."
end
'''
        stmt = parse(src).statements[0]
        assert isinstance(stmt, InteractStmt)
        assert len(stmt.actions) == 3
        assert len(stmt.fallbacks) == 1

    def test_interact_with_condition(self):
        src = '''interact:
    "Open" -> open_door (desc="try to open", condition=has_key)
    fallback "Locked."
end
'''
        stmt = parse(src).statements[0]
        assert stmt.actions[0].condition is not None

    def test_interact_multiple_fallbacks(self):
        src = '''interact:
    "Go" -> go (desc="go")
    fallback "Try again."
    fallback "What do you mean?"
end
'''
        stmt = parse(src).statements[0]
        assert len(stmt.fallbacks) == 2


class TestSystem:
    """测试系统语句"""

    def test_save(self):
        prog = parse('save\n')
        assert isinstance(prog.statements[0], SaveStmt)

    def test_load(self):
        prog = parse('load\n')
        assert isinstance(prog.statements[0], LoadStmt)

    def test_quit(self):
        prog = parse('quit\n')
        assert isinstance(prog.statements[0], QuitStmt)

    def test_python_block(self):
        src = 'python:\n    import random\n    dice = random.randint(1, 6)\nend\n'
        prog = parse(src)
        stmt = prog.statements[0]
        assert isinstance(stmt, PythonBlockStmt)
        assert "import random" in stmt.code


class TestWait:
    """测试等待语句"""

    def test_wait_seconds(self):
        prog = parse('wait 1.5\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, WaitStmt)
        assert stmt.duration == 1.5

    def test_wait_click(self):
        prog = parse('wait click\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, WaitStmt)
        assert stmt.is_click == True


class TestBackground:
    """测试背景语句"""

    def test_bg_path(self):
        prog = parse('bg "school.png"\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, BgStmt)
        assert stmt.path == "school.png"

    def test_bg_none(self):
        prog = parse('bg none\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, BgStmt)
        assert stmt.path is None


class TestInput:
    """测试输入语句"""

    def test_input_stmt(self):
        prog = parse('input name "请输入你的名字："\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, InputStmt)
        assert stmt.name == "name"
        assert stmt.prompt == "请输入你的名字："


class TestAudio:
    """测试音频语句"""

    def test_music_basic(self):
        prog = parse('music "bgm/main.mp3"\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.path == "bgm/main.mp3"

    def test_music_with_fade(self):
        prog = parse('music "bgm/tension.mp3" with fade 2.0\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.fade_in == 2.0

    def test_music_with_volume(self):
        prog = parse('music "bgm/sad.mp3" volume 0.5\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.volume == 0.5

    def test_music_loop_false(self):
        prog = parse('music "bgm/intro.mp3" loop false\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlayMusicStmt)
        assert stmt.loop == False

    def test_sound_basic(self):
        prog = parse('sound "sfx/door.wav"\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlaySoundStmt)
        assert stmt.path == "sfx/door.wav"

    def test_sound_with_volume(self):
        prog = parse('sound "sfx/explosion.wav" volume 0.8\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, PlaySoundStmt)
        assert stmt.volume == 0.8

    def test_stop_music(self):
        prog = parse('stop music\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, StopMusicStmt)
        assert stmt.fade_out == 0.0

    def test_stop_music_with_fade(self):
        prog = parse('stop music with fade 3.0\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, StopMusicStmt)
        assert stmt.fade_out == 3.0

    def test_stop_sound(self):
        prog = parse('stop sound\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, StopSoundStmt)

    def test_volume_music(self):
        prog = parse('volume music = 0.7\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, SetVolumeStmt)
        assert stmt.music_volume == 0.7

    def test_volume_sound(self):
        prog = parse('volume sound = 0.5\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, SetVolumeStmt)
        assert stmt.sound_volume == 0.5


class TestOptions:
    """测试选项语句"""

    def test_options_basic(self):
        prog = parse('options:\n    "Go" -> go (desc="go somewhere")\n    "Stay" -> stay (desc="stay here")\nend\n')
        stmt = prog.statements[0]
        assert isinstance(stmt, OptionsStmt)
        assert len(stmt.items) == 2
        assert stmt.items[0].text == "Go"
        assert stmt.items[0].label == "go"
        assert stmt.items[1].text == "Stay"

    def test_options_with_condition(self):
        prog = parse('options:\n    "Enter" -> enter (desc="enter", condition=has_key)\nend\n')
        stmt = prog.statements[0]
        assert stmt.items[0].condition is not None

    def test_options_in_label(self):
        prog = parse('label start:\n    options:\n        "A" -> a (desc="choice")\n    end\nend\n')
        label_stmt = prog.statements[0]
        assert isinstance(label_stmt.body[0], OptionsStmt)


class TestExpressions:
    """测试表达式"""

    def test_arithmetic_expr(self):
        prog = parse('var x = 1 + 2 * 3\n')
        assert isinstance(prog.statements[0], VarStmt)

    def test_comparison_expr(self):
        prog = parse('var x = a == b\n')
        assert isinstance(prog.statements[0], VarStmt)

    def test_string_concat(self):
        prog = parse('var msg = "Hello " + name\n')
        assert isinstance(prog.statements[0], VarStmt)

    def test_boolean_expr(self):
        prog = parse('var x = a and b\n')
        assert isinstance(prog.statements[0], VarStmt)

    def test_grouped_expr(self):
        prog = parse('var x = (1 + 2) * 3\n')
        assert isinstance(prog.statements[0], VarStmt)


class TestErrors:
    """测试错误情况"""

    def test_empty_options_raises(self):
        with pytest.raises(QFSyntaxError):
            parse('options:\nend\n')

    def test_keyword_as_label_name_raises(self):
        with pytest.raises(QFSyntaxError):
            parse('label end:\nend\n')

    def test_interact_without_fallback_raises(self):
        with pytest.raises(QFSyntaxError):
            parse('interact:\n    "Go" -> go (desc="go")\nend\n')


class TestComplexProgram:
    """测试复杂程序"""

    def test_full_program(self):
        src = '''define yuki = character(name="雪", avatar="", color="#87ceeb")
define narrator = character(name="", avatar="", color="#888888")

var gold = 100
var has_key = false

label start:
    bg "school.png"
    narrator "欢迎来到学校！"
    yuki "你好！"

    if gold >= 50:
        yuki "你很有钱呢！"
    else:
        yuki "你需要更多金币。"
    end

    options:
        "去教室" -> classroom (desc="前往教室")
        "去操场" -> playground (desc="前往操场", condition=has_key)
    end
end

label classroom:
    yuki "这里是教室。"
    music "bgm/class.mp3" with fade 1.0
    jump start
end
'''
        prog = parse(src)
        assert len(prog.statements) >= 6
