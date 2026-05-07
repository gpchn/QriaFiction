import json
import threading
import webview
from pathlib import Path
from app.config import config_store, project_store
from app.logger import app_logger
from app.api_decorators import api_method, ApiError
from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime


class GameRunner:
    def __init__(self):
        self.runtime = Runtime()
        self.interp = None
        self.program = None
        self.window = None
        self.pending_events = []
        self.user_input_event = threading.Event()
        self.current_actions = []
        self.current_fallbacks = []
        self._running = False
        self._lock = threading.Lock()

    def is_running(self):
        return self._running

    def stop(self):
        self._running = False
        if self.runtime:
            self.runtime.running = False
            self.user_input_event.set()

    def reset(self):
        with self._lock:
            self.runtime = Runtime()
            self.interp = None
            self.program = None
            self.pending_events = []
            self.user_input_event.clear()
            self.current_actions = []
            self.current_fallbacks = []

    def load_script(self, path: str):
        src = Path(path).read_text(encoding="utf-8")
        lexer = Lexer(src, path)
        tokens = lexer.tokenize()
        parser = Parser(tokens, path)
        self.program = parser.parse()
        self.interp = Interpreter(runtime=self.runtime, ai_config={"provider": "keyword"})
        self.interp._collect_labels(self.program)

    def _ui_call(self, method, *args):
        if self.window:
            self.window.evaluate_js(
                f"{method}({', '.join(json.dumps(a, ensure_ascii=False) for a in args)})"
            )

    def _show_dialogue(self, char_name, text):
        if char_name:
            char = self.runtime.characters.get(char_name)
            name = char.name if char else char_name
            color = char.color if char else ""
            avatar = char.avatar if char else ""
        else:
            name = ""
            color = ""
            avatar = ""
        msg_type = "system" if not name else "character"
        self._ui_call("addMessage", msg_type, text, name, color, avatar)

    def _show_user_message(self, text):
        self._ui_call("addMessage", "user", text, "你", "", "")

    def _show_fallback(self, text):
        self._ui_call("addMessage", "system", text)

    def _set_background(self, path):
        self._ui_call("setBackground", path or "")

    def _set_status(self, text):
        self._ui_call("setStatus", text)

    def _get_user_input(self, prompt):
        self._ui_call("getUserInput", prompt)
        self.user_input_event.wait()
        self.user_input_event.clear()
        return self.pending_events.pop(0) if self.pending_events else ""

    def _start_interact(self, actions, fallbacks):
        self.current_actions = actions
        self.current_fallbacks = fallbacks
        action_data = [{"name": a.name, "desc": a.desc} for a in actions]
        self._ui_call("handleInteract", "", action_data, fallbacks)

    def _jump_to(self, label):
        if label in self.interp.labels:
            self._execute_block_safe(self.interp.labels[label])

    def start_game(self, script_path: str, ai_provider: str):
        self._running = True
        self.reset()
        self.load_script(script_path)
        self.runtime.variables.clear()
        self.runtime.background = None
        self.runtime.pending_dialogues = []
        self.runtime.pending_input = None
        self.runtime.pending_interact = None
        self.runtime.pending_quit = False
        self.runtime.running = True
        self.interp = Interpreter(runtime=self.runtime, ai_config={"provider": ai_provider})
        self.interp._collect_labels(self.program)
        self._run_main()
        self._running = False

    def _run_main(self):
        if "start" in self.interp.labels:
            self._execute_block_safe(self.interp.labels["start"])
        else:
            self._execute_block_safe(self.program.statements)

    def _execute_block_safe(self, statements):
        import core.ast as ast_mod
        i = 0
        while i < len(statements) and self.runtime.running:
            if self.runtime.pending_jump:
                target = self.runtime.pending_jump
                self.runtime.pending_jump = None
                self.runtime.current_label = target
                if target == "__break__" or target == "__continue__":
                    return
                if target in self.interp.labels:
                    self._execute_block_safe(self.interp.labels[target])
                    return
                else:
                    self._show_fallback(f"未知标签: {target}")
                    return

            stmt = statements[i]
            self._process_stmt(stmt)

            if self.runtime.pending_jump:
                continue

            if self.runtime.pending_dialogues:
                for d in self.runtime.pending_dialogues:
                    self._show_dialogue(d["character"], d["text"])
                self.runtime.pending_dialogues = []

            if self.runtime.pending_input:
                prompt = self.runtime.pending_input["prompt"]
                name = self.runtime.pending_input["name"]
                self.runtime.pending_input = None
                user_text = self._get_user_input(prompt)
                self._show_user_message(user_text)
                self.runtime.set(name, user_text)
                continue

            if self.runtime.pending_interact:
                actions = self.runtime.pending_interact["actions"]
                fallbacks = self.runtime.pending_interact["fallbacks"]
                self.runtime.pending_interact = None
                matched = self._run_interact_loop(actions, fallbacks)
                if not matched:
                    return

            if self.runtime.pending_quit:
                self._show_fallback("故事结束")
                self.runtime.running = False
                return

            i += 1

    def _run_interact_loop(self, actions, fallbacks) -> bool:
        self._start_interact(actions, fallbacks)
        self.user_input_event.wait()
        self.user_input_event.clear()
        if not self.pending_events:
            return False

        user_text = self.pending_events.pop(0)
        if not user_text:
            return False

        self._show_user_message(user_text)
        self.runtime.set("_user_input", user_text)

        available = [a for a in actions if not a.condition or self.interp._eval_expr(a.condition)]

        matched = None
        user_lower = user_text.lower()
        for action in available:
            keywords = action.desc.lower().split()
            if any(kw in user_lower for kw in keywords if len(kw) > 1):
                matched = action
                break

        if matched:
            self.runtime.set("_matched_action", matched.name)
            self.current_actions = []
            self.current_fallbacks = []
            self._jump_to(matched.label)
            return True
        else:
            import random
            fb = random.choice(fallbacks) if fallbacks else "..."
            self._show_fallback(fb)
            return self._run_interact_loop(actions, fallbacks)

    def _process_stmt(self, stmt):
        import core.ast as ast_mod
        if isinstance(stmt, ast_mod.DefineCharacterStmt):
            from core.runtime import Character
            self.runtime.add_character(stmt.name, Character(
                name=stmt.display_name,
                avatar=stmt.avatar,
                color=stmt.color,
            ))
        elif isinstance(stmt, ast_mod.BgStmt):
            self.runtime.background = stmt.path
            self._set_background(stmt.path)
        elif isinstance(stmt, ast_mod.DialogueStmt):
            self.runtime.queue_dialogue(stmt.character, stmt.text)
        elif isinstance(stmt, ast_mod.InteractStmt):
            self.runtime.queue_interact(actions=stmt.actions, fallbacks=stmt.fallbacks)
        elif isinstance(stmt, ast_mod.LabelStmt):
            pass
        elif isinstance(stmt, ast_mod.JumpStmt):
            if stmt.is_otherwise:
                self.runtime.set_jump(stmt.target)
            elif stmt.condition:
                if self.interp._eval_expr(stmt.condition):
                    self.runtime.set_jump(stmt.target)
            else:
                self.runtime.set_jump(stmt.target)
        elif isinstance(stmt, ast_mod.CallStmt):
            if stmt.condition and not self.interp._eval_expr(stmt.condition):
                return
            self.runtime.call_stack.append(self.runtime.current_label)
            self.runtime.set_jump(stmt.target)
        elif isinstance(stmt, ast_mod.ReturnStmt):
            if self.runtime.call_stack:
                caller = self.runtime.call_stack.pop()
                self.runtime.set_jump(caller)
        elif isinstance(stmt, ast_mod.VarStmt):
            if stmt.name == "__break__":
                self.runtime.set_jump("__break__")
            elif stmt.name == "__continue__":
                self.runtime.set_jump("__continue__")
            elif stmt.value:
                self.runtime.set(stmt.name, self.interp._eval_expr(stmt.value))
            else:
                self.runtime.set(stmt.name, None)
        elif isinstance(stmt, ast_mod.SetStmt):
            value = self.interp._eval_expr(stmt.value)
            current = self.runtime.get(stmt.name)
            if stmt.operator == "=":
                self.runtime.set(stmt.name, value)
            elif stmt.operator == "+=":
                self.runtime.set(stmt.name, (current or 0) + value)
            elif stmt.operator == "-=":
                self.runtime.set(stmt.name, (current or 0) - value)
            elif stmt.operator == "*=":
                self.runtime.set(stmt.name, (current or 0) * value)
            elif stmt.operator == "/=":
                current = current or 1
                self.runtime.set(stmt.name, current / value)
        elif isinstance(stmt, ast_mod.InputStmt):
            self.runtime.queue_input_prompt(stmt.name, stmt.prompt)
        elif isinstance(stmt, ast_mod.WaitStmt):
            pass
        elif isinstance(stmt, ast_mod.QuitStmt):
            self.runtime.pending_quit = True
        elif isinstance(stmt, ast_mod.PythonBlockStmt):
            self.interp._execute_python(stmt.code)
        elif isinstance(stmt, ast_mod.IncludeStmt):
            pass

    def submit_input(self, text):
        self.pending_events.append(text)
        self.user_input_event.set()


game_runner = GameRunner()


class LauncherApi:
    API_VERSION = "v1"

    def __init__(self):
        self.current_view = "launcher"
        self.current_project = None

    @api_method
    def get_projects(self):
        return project_store.get_projects()

    @api_method
    def import_project(self, zip_path: str):
        if not zip_path:
            raise ApiError(400, "ZIP 文件路径不能为空")
        try:
            return project_store.import_project(zip_path)
        except ValueError as e:
            raise ApiError(400, str(e))

    @api_method
    def delete_project(self, project_id: str):
        if not project_id:
            raise ApiError(400, "项目ID不能为空")
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            raise ApiError(400, "无效的项目ID")
        project_store.delete_project(project_id)
        return True

    @api_method
    def launch_project(self, project_id: str):
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            raise ApiError(400, "无效的项目ID")
        if game_runner.is_running():
            raise ApiError(409, "已有游戏正在运行")
        proj = project_store.get_project(project_id)
        if not proj:
            raise ApiError(404, f"项目不存在: {project_id}")

        script_path = proj.get("script_main", "")
        if not script_path or not Path(script_path).exists():
            raise ApiError(404, f"主脚本不存在")

        display = proj.get("display", {})
        ai_provider = config_store.get("default_ai_provider", "keyword")

        self.current_project = proj
        self.current_view = "game"
        game_runner.window = webview.windows[0]

        def run_game():
            try:
                game_runner.start_game(script_path, ai_provider)
            except Exception as e:
                app_logger.error(f"游戏运行错误: {e}")
                game_runner._show_fallback(f"错误: {e}")

        threading.Thread(target=run_game, daemon=True).start()
        return True

    @api_method
    def return_to_launcher(self):
        self.current_view = "launcher"
        self.current_project = None
        return True

    @api_method
    def get_ai_models(self):
        return config_store.get_ai_models()

    @api_method
    def add_ai_model(self, model_json: str):
        data = json.loads(model_json)
        if not data.get("name"):
            raise ApiError(400, "模型名称不能为空")
        if not data.get("api_key"):
            raise ApiError(400, "API Key 不能为空")
        config_store.add_ai_model(data)
        return True

    @api_method
    def remove_ai_model(self, model_id: str):
        config_store.remove_ai_model(model_id)
        return True

    @api_method
    def get_config(self):
        return config_store.get_all()

    @api_method
    def set_config(self, key: str, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        config_store.set(key, value)
        return True

    @api_method
    def get_logs(self, limit: int = 200):
        return app_logger.get_logs(limit)

    @api_method
    def clear_data(self):
        from app.config import CONFIG_FILE, DATA_DIR
        import shutil
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        log_dir = DATA_DIR / "logs"
        if log_dir.exists():
            for f in log_dir.iterdir():
                if f.suffix == ".log":
                    f.unlink()
        return True

    @api_method
    def submit_input(self, text):
        game_runner.submit_input(text)
        return True

    @api_method
    def ai_match(self, user_input, actions, fallbacks):
        available = []
        for a in actions:
            available.append({"name": a["name"], "desc": a["desc"]})

        matched = None
        user_lower = user_input.lower()
        for action in available:
            keywords = action["desc"].lower().split()
            if any(kw in user_lower for kw in keywords if len(kw) > 1):
                matched = action["name"]
                break

        if matched:
            return {"matched": matched}
        else:
            import random
            fb = random.choice(fallbacks) if fallbacks else "..."
            return {"matched": None, "fallback": fb}

    @api_method
    def on_action_matched(self, result):
        return True
