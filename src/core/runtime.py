import json
import time
from pathlib import Path


class Character:
    def __init__(self, name: str, avatar: str, color: str):
        self.name = name
        self.avatar = avatar
        self.color = color

    def to_dict(self):
        return {"name": self.name, "avatar": self.avatar, "color": self.color}

    @classmethod
    def from_dict(cls, data):
        return cls(name=data["name"], avatar=data["avatar"], color=data["color"])


class Runtime:
    SAVE_VERSION = 1

    def __init__(self):
        self.variables: dict = {}
        self.characters: dict[str, Character] = {}
        self.background: str | None = None
        self.current_label: str = ""
        self.call_stack: list = []
        self._user_input: str = ""
        self._matched_action: str = ""
        self._start_time = time.time()
        self.running = True
        self.pending_jump: str | None = None
        self.pending_dialogues: list = []
        self.pending_input: dict | None = None
        self.pending_interact: dict | None = None
        self.pending_save = False
        self.pending_load = False
        self.pending_quit = False
        self.pending_audio: dict | None = None
        self._save_slot: str = "autosave"
        self._load_slot: str = "autosave"
        self.music_volume: float = 1.0
        self.sound_volume: float = 1.0
        self.current_music: str | None = None
        self.save_dir: Path | None = None

    def init_save_dir(self, save_dir: Path):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def get(self, name: str):
        if name.startswith("_"):
            if name == "_user_input":
                return self._user_input
            if name == "_matched_action":
                return self._matched_action
            if name == "_label":
                return self.current_label
            if name == "_playtime":
                return time.time() - self._start_time
        return self.variables.get(name)

    def set(self, name: str, value):
        if name.startswith("_"):
            if name == "_user_input":
                self._user_input = value
                return
            if name == "_matched_action":
                self._matched_action = value
                return
        self.variables[name] = value

    def add_character(self, name: str, char: Character):
        self.characters[name] = char

    def queue_dialogue(self, character: str | None, text: str):
        self.pending_dialogues.append({"character": character, "text": text})

    def queue_input_prompt(self, name: str, prompt: str):
        self.pending_input = {"name": name, "prompt": prompt}

    def queue_interact(self, actions: list, fallbacks: list):
        self.pending_interact = {"actions": actions, "fallbacks": fallbacks}

    def clear_pending_dialogues(self):
        self.pending_dialogues = []
        self.pending_input = None
        self.pending_interact = None

    def set_jump(self, label: str):
        self.pending_jump = label

    def set_save_slot(self, slot: str):
        self._save_slot = slot

    def set_load_slot(self, slot: str):
        self._load_slot = slot

    def clear_pending(self):
        self.clear_pending_dialogues()
        self.pending_jump = None
        self.pending_save = False
        self.pending_load = False
        self.pending_quit = False

    def save_game(self, slot: str | None = None) -> dict:
        slot = slot or self._save_slot
        return {
            "version": self.SAVE_VERSION,
            "timestamp": time.time(),
            "playtime": time.time() - self._start_time,
            "variables": self.variables.copy(),
            "background": self.background,
            "current_label": self.current_label,
            "call_stack": self.call_stack.copy(),
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "music_volume": self.music_volume,
            "sound_volume": self.sound_volume,
            "current_music": self.current_music,
        }

    def load_game(self, save_data: dict) -> bool:
        if not save_data:
            return False
        if save_data.get("version", 0) > self.SAVE_VERSION:
            return False
        self.variables = save_data.get("variables", {})
        self.background = save_data.get("background")
        self.current_label = save_data.get("current_label", "")
        self.call_stack = save_data.get("call_stack", [])
        self._start_time = time.time() - save_data.get("playtime", 0)
        self.music_volume = save_data.get("music_volume", 1.0)
        self.sound_volume = save_data.get("sound_volume", 1.0)
        self.current_music = save_data.get("current_music")

        self.characters.clear()
        for k, v in save_data.get("characters", {}).items():
            self.add_character(k, Character.from_dict(v))

        return True
