import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.runtime import Runtime, Character


class TestRuntimeVariables:
    """测试运行时变量"""

    def setup_method(self):
        self.runtime = Runtime()

    def test_get_set(self):
        self.runtime.set("x", 42)
        assert self.runtime.get("x") == 42

    def test_builtin_vars(self):
        self.runtime.set("_user_input", "hello")
        assert self.runtime.get("_user_input") == "hello"

    def test_playtime(self):
        time.sleep(0.01)
        pt = self.runtime.get("_playtime")
        assert pt > 0

    def test_get_nonexistent_key(self):
        assert self.runtime.get("nonexistent") is None

    def test_set_and_get_none(self):
        self.runtime.set("key", None)
        assert self.runtime.get("key") is None

    def test_set_and_get_complex(self):
        self.runtime.set("data", {"nested": {"key": "value"}})
        assert self.runtime.get("data")["nested"]["key"] == "value"

    def test_set_and_get_list(self):
        self.runtime.set("items", [1, 2, 3])
        assert self.runtime.get("items") == [1, 2, 3]

    def test_set_and_get_string(self):
        self.runtime.set("msg", "Hello World")
        assert self.runtime.get("msg") == "Hello World"

    def test_overwrite_variable(self):
        self.runtime.set("x", 10)
        self.runtime.set("x", 20)
        assert self.runtime.get("x") == 20


class TestRuntimePending:
    """测试待处理状态"""

    def setup_method(self):
        self.runtime = Runtime()

    def test_pending_options(self):
        self.runtime.pending_options = {"items": [{"text": "Go", "label": "go"}]}
        assert self.runtime.pending_options is not None
        assert len(self.runtime.pending_options["items"]) == 1

    def test_pending_input(self):
        self.runtime.pending_input = {"name": "player_name", "prompt": "Enter name:"}
        assert self.runtime.pending_input is not None
        assert self.runtime.pending_input["name"] == "player_name"

    def test_pending_audio(self):
        self.runtime.pending_audio = {"type": "music", "path": "bgm.mp3"}
        assert self.runtime.pending_audio is not None

    def test_pending_jump(self):
        self.runtime.pending_jump = "next_scene"
        assert self.runtime.pending_jump == "next_scene"

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

    def test_clear_pending_with_options(self):
        self.runtime.pending_options = {"items": []}
        self.runtime.clear_pending()
        assert self.runtime.pending_options is None


class TestRuntimeSaveLoad:
    """测试存档加载"""

    def setup_method(self):
        self.runtime = Runtime()

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

    def test_save_includes_audio_state(self):
        self.runtime.music_volume = 0.7
        self.runtime.sound_volume = 0.5
        data = self.runtime.save_game()
        assert data.get("music_volume") == 0.7
        assert data.get("sound_volume") == 0.5

    def test_load_restores_audio_state(self):
        self.runtime.music_volume = 0.7
        data = self.runtime.save_game()
        new_rt = Runtime()
        new_rt.load_game(data)
        assert new_rt.music_volume == 0.7

    def test_save_includes_current_music(self):
        self.runtime.current_music = "bgm/main.mp3"
        data = self.runtime.save_game()
        assert data.get("current_music") == "bgm/main.mp3"

    def test_save_empty_state(self):
        data = self.runtime.save_game()
        assert isinstance(data, dict)
        assert "variables" in data

    def test_load_into_existing_state(self):
        self.runtime.set("old", "value")
        data = self.runtime.save_game()
        self.runtime.set("old", None)
        self.runtime.load_game(data)
        assert self.runtime.get("old") == "value"

    def test_playtime_increases(self):
        start = self.runtime.get("_playtime")
        time.sleep(0.05)
        end = self.runtime.get("_playtime")
        assert end > start


class TestCharacters:
    """测试角色"""

    def setup_method(self):
        self.runtime = Runtime()

    def test_characters(self):
        char = Character(name="雪", avatar="", color="#87ceeb")
        self.runtime.add_character("yuki", char)
        assert "yuki" in self.runtime.characters
        assert self.runtime.characters["yuki"].name == "雪"

    def test_dialogue_queue(self):
        self.runtime.queue_dialogue("yuki", "hello")
        assert len(self.runtime.pending_dialogues) == 1
        assert self.runtime.pending_dialogues[0]["text"] == "hello"

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

    def test_character_dict_minimal(self):
        char = Character(name="", avatar="", color="#000000")
        d = char.to_dict()
        assert d["name"] == ""
        assert d["avatar"] == ""
        assert d["color"] == "#000000"

    def test_character_from_dict_minimal(self):
        char = Character.from_dict({"name": "", "avatar": "", "color": "#fff"})
        assert char.name == ""

    def test_character_dict_with_data(self):
        char = Character(name="Test", avatar="test.png", color="#ff0000")
        d = char.to_dict()
        restored = Character.from_dict(d)
        assert restored.name == char.name
        assert restored.avatar == char.avatar
        assert restored.color == char.color
