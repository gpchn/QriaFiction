import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime
from core.ast import *
from core.text_utils import interpolate_text
import pytest


def run(src: str, runtime: Runtime = None):
    """Helper to execute source code and return interpreter."""
    tokens = Lexer(src).tokenize()
    ast = Parser(tokens).parse()
    interp = Interpreter(runtime=runtime or Runtime())
    interp.run(ast)
    return interp


class TestDefineAndDialogue:
    """测试定义和对话"""

    def test_define_and_dialogue(self):
        src = 'define yuki = character(name="雪", avatar="", color="#87ceeb")\nyuki "hello"\n'
        interp = run(src)
        assert "yuki" in interp.runtime.characters

    def test_bg_sets_background(self):
        src = 'bg "school.png"\n'
        interp = run(src)
        assert interp.runtime.background == "school.png"

    def test_bg_none_clears(self):
        src = 'bg "school.png"\nbg none\n'
        interp = run(src)
        assert interp.runtime.background is None


class TestVariables:
    """测试变量"""

    def test_variable_declaration(self):
        src = 'var x = 42\n'
        interp = run(src)
        assert interp.runtime.get("x") == 42

    def test_set_add(self):
        src = 'var x = 10\nset x += 5\n'
        interp = run(src)
        assert interp.runtime.get("x") == 15


class TestConditionals:
    """测试条件语句"""

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

    def test_elif_chain(self):
        src = '''var x = 0
if x > 0:
    var result = "positive"
elseif x < 0:
    var result = "negative"
elseif x == 0:
    var result = "zero"
else:
    var result = "other"
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "zero"

    def test_nested_if(self):
        src = '''var a = true
var b = true
if a == true:
    if b == true:
        var result = "both true"
    end
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "both true"


class TestLoops:
    """测试循环"""

    def test_while_loop(self):
        src = 'var i = 0\nvar count = 0\nwhile i < 3:\n    set count += 1\n    set i += 1\nend\n'
        interp = run(src)
        assert interp.runtime.get("count") == 3

    def test_break_from_while(self):
        src = '''var i = 0
var count = 0
while i < 10:
    set count += 1
    if count >= 3:
        break
    end
    set i += 1
end
'''
        interp = run(src)
        assert interp.runtime.get("count") == 3

    def test_continue_in_while(self):
        src = '''var i = 0
var count = 0
while i < 5:
    set i += 1
    if i == 3:
        continue
    end
    set count += 1
end
'''
        interp = run(src)
        assert interp.runtime.get("count") == 4


class TestPythonBlock:
    """测试Python块"""

    def test_python_block(self):
        src = 'python:\n    qf.set("result", 123)\nend\n'
        interp = run(src)
        assert interp.runtime.get("result") == 123

    def test_python_cross_block_state(self):
        src = 'python:\n    my_var = 42\nend\npython:\n    qf.set("copied", my_var)\nend\n'
        interp = run(src)
        assert interp.runtime.get("copied") == 42


class TestJump:
    """测试跳转"""

    def test_jump_to_label(self):
        src = '''label start:
    jump target
end
label target:
    var result = "reached"
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "reached"

    def test_jump_with_condition_true(self):
        src = '''var flag = true
label start:
    jump target if flag == true
    var skipped = true
end
label target:
    var result = "jumped"
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "jumped"
        assert interp.runtime.get("skipped") is None

    def test_jump_with_condition_false(self):
        src = '''var flag = false
label start:
    jump target if flag == true
    var result = "not jumped"
end
label target:
    var wrong = true
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "not jumped"
        assert interp.runtime.get("wrong") is None

    def test_jump_otherwise(self):
        src = '''var flag = false
label start:
    jump target if flag == true
    jump target2 otherwise
end
label target:
    var wrong = true
end
label target2:
    var result = "otherwise"
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "otherwise"
        assert interp.runtime.get("wrong") is None


class TestCallReturn:
    """测试调用和返回"""

    def test_call_pushes_to_call_stack(self):
        """call 将调用者推入 call_stack"""
        src = '''label start:
    call sub
end
label sub:
    var in_sub = true
end
'''
        interp = run(src)
        assert interp.runtime.get("in_sub") == True
        assert len(interp.runtime.call_stack) == 1
        assert interp.runtime.call_stack[0][0] == "start"

    def test_return_pops_from_call_stack(self):
        """return 从 call_stack 弹出"""
        src = '''label start:
    call sub
end
label sub:
    return
end
'''
        interp = run(src)
        assert interp.runtime.call_stack == []

    def test_call_does_not_return_on_jump(self):
        """如果子标签中没有 return 就跳转到别处，不返回"""
        src = '''label start:
    call sub
    var after = true
end
label sub:
    var in_sub = true
    jump end_label
end
label end_label:
    var ended = true
end
'''
        interp = run(src)
        assert interp.runtime.get("in_sub") == True
        assert interp.runtime.get("ended") == True
        assert interp.runtime.get("after") is None


class TestInputStmt:
    """测试输入语句"""

    def test_input_queues_pending(self):
        src = 'input player_name "请输入名字："\n'
        interp = run(src)
        assert interp.runtime.pending_input is not None
        assert interp.runtime.pending_input["name"] == "player_name"
        assert "请输入名字：" in interp.runtime.pending_input["prompt"]


class TestSaveLoadStmt:
    """测试保存加载语句"""

    def test_save_sets_pending(self):
        src = 'save\n'
        interp = run(src)
        assert interp.runtime.pending_save == True


class TestOptions:
    """测试选项"""

    def test_options_sets_pending(self):
        src = '''options:
    "Go" -> go (desc="go somewhere")
    "Stay" -> stay (desc="stay here")
end
'''
        interp = run(src)
        assert interp.runtime.pending_options is not None
        assert len(interp.runtime.pending_options["items"]) == 2


class TestDottedLabels:
    """测试点分标签"""

    def test_jump_dotted_label(self):
        src = '''label start:
    jump other_file.scene
end
label other_file.scene:
    var result = "reached"
end
'''
        interp = run(src)
        assert interp.runtime.get("result") == "reached"

    def test_call_dotted_label(self):
        src = '''label start:
    call other_file.helper
end
label other_file.helper:
    var called = true
end
'''
        interp = run(src)
        assert interp.runtime.get("called") == True


class TestStringInterpolation:
    """测试字符串插值"""

    def test_variable_interpolation(self):
        runtime = Runtime()
        runtime.set("name", "Alice")
        result = interpolate_text("Hello {name}", runtime.get, None, None)
        assert result == "Hello Alice"

    def test_python_interpolation(self):
        result = interpolate_text("Result: {python: 2 + 3}", lambda n: None, None, None)
        assert result == "Result: 5"

    def test_multiple_variables(self):
        runtime = Runtime()
        runtime.set("name", "Alice")
        runtime.set("age", 25)
        result = interpolate_text("我是 {name}，今年 {age} 岁", runtime.get, None, None)
        assert result == "我是 Alice，今年 25 岁"

    def test_python_expr_interpolation(self):
        result = interpolate_text("2+3={python: 2+3}", lambda n: None, None, None)
        assert result == "2+3=5"

    def test_simple_expr(self):
        result = interpolate_text("2+3={python: 2+3}", lambda n: None, None, None)
        assert result == "2+3=5"

    def test_python_error_returns_placeholder(self):
        """Python 表达式错误时保留原占位符"""
        result = interpolate_text("Error: {python: 1/0}", lambda n: None, None, None)
        assert "1/0" in result


class TestInterpreterErrors:
    """测试解释器错误处理"""

    def test_jump_to_unknown_label_raises(self):
        """跳转到未知标签应抛出错误"""
        src = '''label start:
    jump unknown_label
end
'''
        from core.errors import QFRuntimeError
        interp = Interpreter(runtime=Runtime())
        tokens = Lexer(src).tokenize()
        ast = Parser(tokens).parse()
        try:
            interp.run(ast)
            assert False, "Should have raised QFRuntimeError"
        except QFRuntimeError as e:
            assert "未知标签" in str(e)

    def test_variable_undefined_returns_none(self):
        """未定义变量返回 None"""
        src = 'var result = undefined_var\n'
        interp = run(src)
        assert interp.runtime.get("result") is None

    def test_arithmetic_with_none(self):
        """None 参与算术运算"""
        src = 'var x = undefined_var + 1\n'
        interp = run(src)
        assert interp.runtime.get("x") == 1

    def test_division_by_zero(self):
        """除以零"""
        src = 'var x = 10 / 0\n'
        interp = run(src)
        assert interp.runtime.get("x") == 10

    def test_empty_label_body(self):
        """空标签体"""
        src = '''label start:
end
'''
        interp = run(src)
        assert interp.runtime.current_label == "start"

    def test_nested_loops(self):
        """嵌套循环"""
        src = '''var i = 0
var j = 0
var count = 0
while i < 2:
    set j = 0
    while j < 2:
        set count += 1
        set j += 1
    end
    set i += 1
end
'''
        interp = run(src)
        assert interp.runtime.get("count") == 4
