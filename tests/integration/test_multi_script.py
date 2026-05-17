import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime


def run_with_scripts(main_src: str, scripts: dict):
    """Helper to run multi-script tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_dir = Path(tmpdir)
        main_path = script_dir / "main.qf"
        main_path.write_text(main_src, encoding="utf-8")
        for filename, src in scripts.items():
            script_file = script_dir / filename
            script_file.write_text(src, encoding="utf-8")
        src = main_path.read_text(encoding="utf-8")
        tokens = Lexer(src, str(main_path)).tokenize()
        program = Parser(tokens, str(main_path)).parse()
        interp = Interpreter(runtime=Runtime(), script_dir=script_dir)
        interp.run(program)
        return interp


class TestSingleScript:
    """测试单脚本"""

    def test_single_script_with_start(self):
        """Test that a single main script works."""
        src = '''
var x = 0
label start:
    set x = 42
end
'''
        interp = run_with_scripts(src, {})
        assert interp.runtime.get("x") == 42


class TestTwoScripts:
    """测试两个脚本"""

    def test_two_scripts_with_jump(self):
        """Test jumping between two scripts."""
        main_src = '''
define yuki = character(name="雪", avatar="", color="#87ceeb")
var visited_ch1 = false
label start:
    jump ch1.begin
end
'''
        ch1_src = '''
label begin:
    set visited_ch1 = true
end
'''
        interp = run_with_scripts(main_src, {"ch1.qf": ch1_src})
        assert interp.runtime.get("visited_ch1") == True
        assert "ch1.begin" in interp.labels
        assert "yuki" in interp.runtime.characters


class TestThreeScriptsChain:
    """测试三个脚本链"""

    def test_three_scripts_chain(self):
        """Test jumping through three scripts."""
        main_src = '''
var step = 0
label start:
    set step = 1
    jump ch1.begin
end
'''
        ch1_src = '''
label begin:
    set step = 2
    jump ch2.finale
end
'''
        ch2_src = '''
label finale:
    set step = 3
end
'''
        interp = run_with_scripts(main_src, {
            "ch1.qf": ch1_src,
            "ch2.qf": ch2_src,
        })
        assert interp.runtime.get("step") == 3


class TestCallAndReturn:
    """测试调用和返回"""

    def test_call_and_return_between_scripts(self):
        """Test calling and returning between scripts."""
        main_src = '''
var called = false
var returned = false
label start:
    call ch1.greet
end
label after_call:
    set returned = true
end
'''
        ch1_src = '''
label greet:
    set called = true
    jump after_call
end
'''
        interp = run_with_scripts(main_src, {"ch1.qf": ch1_src})
        assert interp.runtime.get("called") == True
        assert interp.runtime.get("returned") == True


class TestLabelNamespace:
    """测试标签命名空间"""

    def test_label_namespace_no_collision(self):
        """Test that labels from different scripts don't collide."""
        main_src = '''
var result = "main"
label start:
    jump ch1.intro
end
label main_end:
    set result = "main_end"
end
'''
        ch1_src = '''
var ch1_result = "ch1"
label intro:
    set ch1_result = "started"
    jump main_end
end
label ch1_end:
    set ch1_result = "ch1_end"
end
'''
        interp = run_with_scripts(main_src, {"ch1.qf": ch1_src})
        assert interp.runtime.get("result") == "main_end"
        assert interp.runtime.get("ch1_result") == "started"

    def test_main_script_labels_no_namespace(self):
        """Test that main.qf labels have no namespace prefix."""
        main_src = '''
var found = false
label start:
    jump my_label
end
label my_label:
    set found = true
end
'''
        interp = run_with_scripts(main_src, {})
        assert interp.runtime.get("found") == True
        assert "my_label" in interp.labels
        assert "main.my_label" not in interp.labels

    def test_non_main_scripts_have_namespace(self):
        """Test that non-main scripts have namespace prefix."""
        main_src = '''
label start:
    jump events.greeting
end
'''
        events_src = '''
label greeting:
    var greeted = true
end
'''
        interp = run_with_scripts(main_src, {"events.qf": events_src})
        assert interp.runtime.get("greeted") == True
        assert "events.greeting" in interp.labels
        assert "greeting" not in interp.labels


class TestCharacterDefinition:
    """测试角色定义"""

    def test_define_character_in_separate_script(self):
        """Test defining characters in a separate script."""
        main_src = '''
label start:
    jump chars.init
end
label after:
    var dummy = 1
end
'''
        chars_src = '''
define yuki = character(name="雪", avatar="", color="#87ceeb")
label init:
    jump after
end
'''
        interp = run_with_scripts(main_src, {"chars.qf": chars_src})
        assert "yuki" in interp.runtime.characters


class TestLabelRegistry:
    """测试标签注册"""

    def test_label_registry_contains_all_scripts(self):
        """Test that all script labels are registered."""
        main_src = '''
label start:
    var dummy = 1
end
'''
        ch1_src = '''
label scene1:
    var x = 1
end
'''
        ch2_src = '''
label scene2:
    var y = 2
end
'''
        interp = run_with_scripts(main_src, {
            "ch1.qf": ch1_src,
            "ch2.qf": ch2_src,
        })
        assert "start" in interp.labels
        assert "ch1.scene1" in interp.labels
        assert "ch2.scene2" in interp.labels
