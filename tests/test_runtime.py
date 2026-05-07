import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.runtime import Runtime, Character


class TestRuntime:
    def setup_method(self):
        self.runtime = Runtime()

    def test_get_set(self):
        self.runtime.set("x", 42)
        assert self.runtime.get("x") == 42

    def test_builtin_vars(self):
        self.runtime.set("_user_input", "hello")
        assert self.runtime.get("_user_input") == "hello"

    def test_playtime(self):
        import time
        time.sleep(0.01)
        pt = self.runtime.get("_playtime")
        assert pt > 0

    def test_characters(self):
        char = Character(name="雪", avatar="", color="#87ceeb")
        self.runtime.add_character("yuki", char)
        assert "yuki" in self.runtime.characters
        assert self.runtime.characters["yuki"].name == "雪"

    def test_dialogue_queue(self):
        self.runtime.queue_dialogue("yuki", "hello")
        assert len(self.runtime.pending_dialogues) == 1
        assert self.runtime.pending_dialogues[0]["text"] == "hello"

    def test_save_load(self):
        self.runtime.set("x", 100)
        self.runtime.background = "bg/school.png"
        self.runtime.current_label = "scene_2"

        data = self.runtime.save_game()
        assert data["variables"]["x"] == 100
        assert data["background"] == "bg/school.png"
        assert data["current_label"] == "scene_2"

        self.runtime2 = Runtime()
        assert self.runtime2.get("x") is None
        self.runtime2.load_game(data)
        assert self.runtime2.get("x") == 100
        assert self.runtime2.background == "bg/school.png"

    def test_clear_pending(self):
        self.runtime.pending_dialogues = [{"text": "x"}]
        self.runtime.pending_input = {"name": "n"}
        self.runtime.pending_jump = "test"
        self.runtime.pending_save = True

        self.runtime.clear_pending()
        assert self.runtime.pending_dialogues == []
        assert self.runtime.pending_input is None
        assert self.runtime.pending_jump is None
        assert self.runtime.pending_save is False

    def test_character_to_dict(self):
        char = Character(name="雪", avatar="a.png", color="#87ceeb")
        d = char.to_dict()
        assert d["name"] == "雪"
        assert d["avatar"] == "a.png"
        assert d["color"] == "#87ceeb"

    def test_character_from_dict(self):
        d = {"name": "雪", "avatar": "a.png", "color": "#87ceeb"}
        char = Character.from_dict(d)
        assert char.name == "雪"
