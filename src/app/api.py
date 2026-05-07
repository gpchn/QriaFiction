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
from core.text_utils import interpolate_text_with_logging


def _log(level, tag, *args):
    msg = " ".join(str(a) for a in args)
    colors = {"D": "\033[90m", "I": "\033[36m", "W": "\033[33m", "E": "\033[31m"}
    reset = "\033[0m"
    c = colors.get(level, "")
    print(f"{c}[{level}][{tag}]{reset} {msg}")
    if level == "E":
        app_logger.error(f"[{tag}] {msg}")
    elif level == "W":
        app_logger.warn(f"[{tag}] {msg}")
    else:
        app_logger.debug(f"[{tag}] {msg}")


class GameRunner:
    def __init__(self):
        self.runtime = Runtime()
        self.interp = None
        self.program = None
        self.window = None
        self.user_input_event = threading.Event()
        self.user_input_value = ""
        self.continue_event = threading.Event()
        self._python_scope = {}
        self._running = False
        self._lock = threading.Lock()
        self._return_stack = []
        self._current_index = 0

    def is_running(self):
        return self._running

    def stop(self):
        _log("I", "stop", "called")
        self._running = False
        self.runtime.running = False
        self.user_input_event.set()
        self.continue_event.set()

    def reset(self):
        with self._lock:
            _log("I", "reset", "called")
            self.runtime = Runtime()
            self.interp = None
            self.program = None
            self.user_input_event.clear()
            self.user_input_value = ""
            self.continue_event.clear()
            self._python_scope = {}
            self._return_stack = []
            self._current_index = 0

    def load_script(self, path: str):
        _log("I", "load", f"path={path}")
        src = Path(path).read_text(encoding="utf-8")
        lexer = Lexer(src, path)
        tokens = lexer.tokenize()
        _log("I", "load", f"tokens={len(tokens)}")
        parser = Parser(tokens, path)
        self.program = parser.parse()
        _log("I", "load", f"statements={len(self.program.statements)}")

    def _ui_call(self, method, *args):
        if self.window:
            js_args = ", ".join(json.dumps(a, ensure_ascii=False) for a in args)
            self.window.evaluate_js(f"{method}({js_args})")

    def _interpolate_text(self, text: str) -> str:
        qf_ctx = self.interp.qf_ctx if self.interp else None
        return interpolate_text_with_logging(
            text=text,
            get_var_func=self.runtime.get,
            python_scope=self._python_scope,
            qf_ctx=qf_ctx,
            log_func=_log,
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
        text = self._interpolate_text(text)
        _log("I", "dialogue", f"[{msg_type}]{name}: {text[:60]}")
        self._ui_call("addMessage", msg_type, text, name, color, avatar)
        self._wait_for_continue()

    def _wait_for_continue(self):
        self._ui_call("showContinue")
        self.continue_event.wait()
        self.continue_event.clear()

    def _wait_for_input(self, prompt):
        _log("I", "input", f"prompt={prompt}")
        self._ui_call("getUserInput", prompt)
        self.user_input_event.wait()
        self.user_input_event.clear()
        val = self.user_input_value
        self.user_input_value = ""
        _log("I", "input", f"got={val}")
        return val

    def start_game(self, script_path: str, ai_provider: str):
        _log("I", "start", f"path={script_path} provider={ai_provider}")
        self._running = True
        self.reset()
        self.load_script(script_path)
        self.runtime.running = True
        self.interp = Interpreter(runtime=self.runtime, ai_config={"provider": ai_provider})
        self.interp._collect_labels(self.program)
        self._run_program()
        _log("I", "start", "finished")
        self._running = False

    def _run_program(self):
        import core.ast as ast_mod

        for stmt in self.program.statements:
            if isinstance(stmt, ast_mod.LabelStmt):
                continue
            self._exec_stmt(stmt)
            if not self.runtime.running:
                return

        if "start" in self.interp.labels:
            self._exec_label("start")
        else:
            self._exec_block(self.program.statements)

    def _exec_label(self, label_name: str, resume_from: int = 0):
        _log("I", "label", f"{label_name} (resume={resume_from})")
        if label_name not in self.interp.labels:
            self._show_dialogue(None, f"[错误] 未知标签: {label_name}")
            return
        self.runtime.current_label = label_name
        self._exec_block(self.interp.labels[label_name], resume_from=resume_from)

    def _exec_block(self, statements: list, resume_from: int = 0):
        import core.ast as ast_mod
        i = resume_from
        while i < len(statements) and self.runtime.running:
            self._current_index = i
            stmt = statements[i]
            _log("D", "exec", f"[{i}] {type(stmt).__name__}")

            self._exec_stmt(stmt)

            if not self.runtime.running:
                return

            if self.runtime.pending_jump:
                target = self.runtime.pending_jump
                self.runtime.pending_jump = None
                if target == "__break__" or target == "__continue__":
                    return
                if self._return_stack:
                    label, resume_idx = self._return_stack.pop()
                    _log("I", "return", f"-> {label}[{resume_idx}]")
                    self._exec_label(label, resume_from=resume_idx)
                    return
                self._exec_label(target)
                return

            if self.runtime.pending_quit:
                self._show_dialogue(None, "故事结束")
                self.runtime.running = False
                return

            i += 1

    def _exec_stmt(self, stmt):
        import core.ast as ast_mod

        if isinstance(stmt, ast_mod.DefineCharacterStmt):
            from core.runtime import Character
            _log("I", "char", f"define {stmt.name}")
            self.runtime.add_character(stmt.name, Character(
                name=stmt.display_name,
                avatar=stmt.avatar,
                color=stmt.color,
            ))

        elif isinstance(stmt, ast_mod.BgStmt):
            _log("I", "bg", stmt.path)
            self.runtime.background = stmt.path
            self._ui_call("setBackground", stmt.path or "")

        elif isinstance(stmt, ast_mod.DialogueStmt):
            self._show_dialogue(stmt.character, stmt.text)

        elif isinstance(stmt, ast_mod.InteractStmt):
            _log("I", "interact", [a.name for a in stmt.actions])
            self._exec_interact(stmt.actions, stmt.fallbacks)

        elif isinstance(stmt, ast_mod.LabelStmt):
            self.runtime.current_label = stmt.name

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
            caller = (self.runtime.current_label, self._current_index + 1)
            self._return_stack.append(caller)
            _log("I", "call", f"push {caller}, jump to {stmt.target}")
            self.runtime.set_jump(stmt.target)

        elif isinstance(stmt, ast_mod.ReturnStmt):
            _log("I", "return", f"return_stack={self._return_stack}")
            if self._return_stack:
                label, resume_idx = self._return_stack.pop()
                self.runtime.pending_jump = label
                _log("I", "return", f"will resume at {label}[{resume_idx}]")

        elif isinstance(stmt, ast_mod.VarStmt):
            if stmt.value:
                val = self.interp._eval_expr(stmt.value)
                _log("I", "var", f"{stmt.name} = {val}")
                self.runtime.set(stmt.name, val)
            else:
                self.runtime.set(stmt.name, None)

        elif isinstance(stmt, ast_mod.SetStmt):
            value = self.interp._eval_expr(stmt.value)
            current = self.runtime.get(stmt.name)
            _log("I", "set", f"{stmt.name} {stmt.operator} {value}")
            if stmt.operator == "=":
                self.runtime.set(stmt.name, value)
            elif stmt.operator == "+=":
                self.runtime.set(stmt.name, (current or 0) + value)
            elif stmt.operator == "-=":
                self.runtime.set(stmt.name, (current or 0) - value)
            elif stmt.operator == "*=":
                self.runtime.set(stmt.name, (current or 0) * value)
            elif stmt.operator == "/=":
                self.runtime.set(stmt.name, (current or 1) / value)

        elif isinstance(stmt, ast_mod.InputStmt):
            user_text = self._wait_for_input(stmt.prompt)
            self.runtime.set(stmt.name, user_text)
            _log("I", "input", f"stored {stmt.name}={user_text}")

        elif isinstance(stmt, ast_mod.IfStmt):
            for branch in stmt.branches:
                if self.interp._eval_expr(branch.condition):
                    self._exec_block(branch.body)
                    return
            if stmt.else_body:
                self._exec_block(stmt.else_body)

        elif isinstance(stmt, ast_mod.WhileStmt):
            while self.interp._eval_expr(stmt.condition) and self.runtime.running:
                self._exec_block(stmt.body)
                if self.runtime.pending_jump == "__break__":
                    self.runtime.pending_jump = None
                    return
                if self.runtime.pending_jump == "__continue__":
                    self.runtime.pending_jump = None
                if self.runtime.pending_jump:
                    return
                if not self.runtime.running:
                    return

        elif isinstance(stmt, ast_mod.WaitStmt):
            import time
            if isinstance(stmt.duration, (int, float)):
                time.sleep(stmt.duration)

        elif isinstance(stmt, ast_mod.QuitStmt):
            self.runtime.pending_quit = True

        elif isinstance(stmt, ast_mod.PythonBlockStmt):
            _log("I", "python", stmt.code[:60])
            self._python_scope["qf"] = self.interp.qf_ctx
            try:
                exec(stmt.code, self._python_scope)
            except Exception as e:
                _log("E", "python", str(e))
                raise
            if self.runtime.pending_jump:
                _log("I", "python", f"jump -> {self.runtime.pending_jump}")

        elif isinstance(stmt, ast_mod.IncludeStmt):
            pass

    def _exec_interact(self, actions, fallbacks):
        _log("I", "interact", [a.name for a in actions])
        available = [a for a in actions if not a.condition or self.interp._eval_expr(a.condition)]
        action_data = [{"name": a.name, "desc": a.desc, "label": a.label} for a in available]
        self._ui_call("handleInteract", "", action_data, fallbacks)

        while self.runtime.running:
            self.user_input_event.wait()
            self.user_input_event.clear()
            user_text = self.user_input_value
            self.user_input_value = ""

            if not user_text:
                continue

            matched = self._match_action(user_text, available)
            if matched:
                _log("I", "interact", f"matched: {matched.name} -> {matched.label}")
                self.runtime.set("_user_input", user_text)
                self.runtime.set("_matched_action", matched.name)
                self.runtime.set_jump(matched.label)
                return
            else:
                import random
                fb = random.choice(fallbacks) if fallbacks else "..."
                _log("I", "interact", f"fallback: {fb}")
                self._show_dialogue(None, fb)
                self._ui_call("handleInteract", "", action_data, fallbacks)

    def _match_action(self, user_text: str, actions: list):
        from fuzzywuzzy import fuzz
        best_score = 0
        best_action = None
        for action in actions:
            score_name = fuzz.partial_ratio(user_text, action.name)
            score_desc = fuzz.partial_ratio(user_text, action.desc)
            score = max(score_name, score_desc)
            if score > best_score:
                best_score = score
                best_action = action
        if best_score >= 65:
            _log("I", "match", f"score={best_score} -> {best_action.name}")
            return best_action
        _log("I", "match", f"score={best_score} < 65, no match")
        return None

    def submit_input(self, text: str):
        _log("D", "submit", f"text={text}")
        self.user_input_value = text
        self.user_input_event.set()

    def continue_game(self):
        _log("D", "continue", "event set")
        self.continue_event.set()


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
        _log("I", "launch", f"project={project_id}")
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            raise ApiError(400, "无效的项目ID")
        if game_runner.is_running():
            raise ApiError(409, "已有游戏正在运行")
        proj = project_store.get_project(project_id)
        if not proj:
            raise ApiError(404, f"项目不存在: {project_id}")

        script_path = proj.get("script_main", "")
        if not script_path or not Path(script_path).exists():
            raise ApiError(404, "主脚本不存在")

        ai_provider = config_store.get("default_ai_provider", "keyword")
        self.current_project = proj
        self.current_view = "game"
        game_runner.window = webview.windows[0]

        def run_game():
            try:
                game_runner.start_game(script_path, ai_provider)
            except Exception as e:
                _log("E", "game", str(e))
                app_logger.error(f"游戏运行错误: {e}")
                game_runner._show_dialogue(None, f"错误: {e}")

        threading.Thread(target=run_game, daemon=True).start()
        return True

    @api_method
    def return_to_launcher(self):
        _log("I", "return", "called")
        game_runner.stop()
        game_runner.reset()
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
    def set_config_batch(self, updates_json: str):
        updates = json.loads(updates_json)
        config_store.set_batch(updates)
        return True

    @api_method
    def get_logs(self, limit: int = 200):
        return app_logger.get_logs(limit)

    @api_method
    def clear_data(self):
        from app.config import CONFIG_FILE, DATA_DIR
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
    def continue_game(self):
        game_runner.continue_game()
        return True

    @api_method
    def ai_match(self, user_input, actions, fallbacks):
        available = [{"name": a["name"], "desc": a["desc"]} for a in actions]
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
