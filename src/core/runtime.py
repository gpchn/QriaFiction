import time


class Character:
    def __init__(self, name: str, avatar: str, color: str):
        self.name = name
        self.avatar = avatar
        self.color = color


class Runtime:
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

    def clear_pending(self):
        self.pending_dialogues = []
        self.pending_input = None
        self.pending_interact = None

    def set_jump(self, label: str):
        self.pending_jump = label
