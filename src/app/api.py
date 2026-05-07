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
from core.runtime import Runtime, Character
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
        self.runtime = None
        self.interp = None
        self.program = None
        self.window = None
        self.user_input_event = threading.Event()
        self.user_input_value = ""
        self.continue_event = threading.Event()
        self._python_scope = {}
        self._running = False
        self._lock = threading.Lock()
        self._script_dir = None
        self._save_dir = None
        self._current_stmt_index = 0
        self._call_stack = []
        self._last_include_stmt = None

    def is_running(self):
        return self._running

    def stop(self):
        _log("I", "stop", "called")
        self._running = False
        if self.runtime:
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
            self._call_stack = []
            self._current_stmt_index = 0
            self._script_dir = None
            self._save_dir = None

    def load_script(self, path: str):
        _log("I", "load", f"path={path}")
        src = Path(path).read_text(encoding="utf-8")
        self._script_dir = Path(path).parent
        self._save_dir = self._script_dir.parent / "saves"
        self._save_dir.mkdir(parents=True, exist_ok=True)
        Runtime.init_save_dir(self._save_dir)
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

    def _resolve_resource_path(self, path: str, as_data_url: bool = False) -> str:
        if not path:
            return ""
        if Path(path).is_absolute():
            target = Path(path)
        elif self._script_dir:
            target = (self._script_dir.parent / path).resolve()
        else:
            target = Path(path).resolve()
        if not target.exists():
            return ""
        if not as_data_url:
            return target.as_posix()
        try:
            import base64
            ext = target.suffix.lower()
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
            mime = mime_map.get(ext, "image/png")
            data = base64.b64encode(target.read_bytes()).decode()
            return f"data:{mime};base64,{data}"
        except Exception:
            return ""

    def _show_dialogue(self, char_name, text):
        if char_name:
            char = self.runtime.characters.get(char_name)
            name = char.name if char else char_name
            color = char.color if char else ""
            avatar = self._resolve_resource_path(char.avatar, as_data_url=True) if char and char.avatar else ""
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
        ai_config = {"provider": ai_provider}
        models = config_store.get_ai_models()
        for m in models:
            if m.get("provider") == ai_provider:
                ai_config["model"] = m.get("model", "")
                ai_config["api_key"] = m.get("api_key", "")
                if m.get("base_url"):
                    ai_config["url"] = m["base_url"]
                break
        self.interp = Interpreter(runtime=self.runtime, ai_config=ai_config, script_dir=self._script_dir)
        self.interp._collect_labels(self.program)
        self._python_scope["qf"] = self.interp.qf_ctx
        self._run_program()
        _log("I", "start", "finished")
        self._running = False

    def _run_program(self):
        non_label_stmts = []
        for stmt in self.program.statements:
            if hasattr(stmt, 'name') and isinstance(stmt.name, str) and hasattr(stmt, 'body'):
                continue
            non_label_stmts.append(stmt)

        if non_label_stmts:
            _log("I", "run", f"executing {len(non_label_stmts)} top-level statements")
            self._exec_block(non_label_stmts)
            if not self.runtime.running:
                return

        if "start" in self.interp.labels:
            self._exec_label("start")

    def _exec_label(self, label_name: str, resume_from: int = 0):
        _log("I", "label", f"{label_name} (resume={resume_from})")
        if label_name not in self.interp.labels:
            self._show_dialogue(None, f"[错误] 未知标签: {label_name}")
            return
        self.runtime.current_label = label_name
        self.interp.runtime.current_label = label_name
        self._exec_block(self.interp.labels[label_name], resume_from=resume_from)

    def _exec_block(self, statements: list, resume_from: int = 0):
        import core.ast as ast_mod
        i = resume_from
        while i < len(statements) and self.runtime.running:
            self._current_stmt_index = i
            stmt = statements[i]

            self._exec_stmt(stmt)

            if not self.runtime.running:
                return

            if self.runtime.pending_jump:
                target = self.runtime.pending_jump
                self.runtime.pending_jump = None
                if target == "__break__" or target == "__continue__":
                    return
                if self._call_stack:
                    label, resume_idx = self._call_stack.pop()
                    _log("I", "return", f"-> {label}[{resume_idx}]")
                    self._exec_label(label, resume_from=resume_idx)
                    return
                self._exec_label(target)
                return

            if self.runtime.pending_save:
                self.runtime.pending_save = False
                self._do_save()
                i += 1
                continue

            if self.runtime.pending_load:
                self.runtime.pending_load = False
                self._do_load()
                if self.runtime.pending_jump:
                    target = self.runtime.pending_jump
                    self.runtime.pending_jump = None
                    if target == "__break__" or target == "__continue__":
                        return
                    if self._call_stack:
                        label, resume_idx = self._call_stack.pop()
                        _log("I", "return", f"-> {label}[{resume_idx}]")
                        self._exec_label(label, resume_from=resume_idx)
                        return
                    self._exec_label(target)
                    return
                i += 1
                continue

            if self.runtime.pending_quit:
                self._show_dialogue(None, "故事结束")
                self.runtime.running = False
                return

            i += 1

    def _exec_stmt(self, stmt):
        import core.ast as ast_mod

        self.interp._execute(stmt)

        if isinstance(stmt, ast_mod.BgStmt):
            resolved = self._resolve_resource_path(stmt.path, as_data_url=True) if stmt.path else ""
            self._ui_call("setBackground", resolved)

        elif isinstance(stmt, ast_mod.DialogueStmt):
            self._show_dialogue(stmt.character, stmt.text)

        elif isinstance(stmt, ast_mod.InteractStmt):
            self._exec_interact(stmt.actions, stmt.fallbacks)

        elif isinstance(stmt, ast_mod.CallStmt):
            if stmt.condition and not self.interp._eval_expr(stmt.condition):
                return
            caller = (self.runtime.current_label, self._current_stmt_index + 1)
            self._call_stack.append(caller)
            _log("I", "call", f"push {caller}, jump to {stmt.target}")

        elif isinstance(stmt, ast_mod.ReturnStmt):
            _log("I", "return", f"call_stack={self._call_stack}")
            if self._call_stack:
                label, resume_idx = self._call_stack.pop()
                self.runtime.pending_jump = label
                _log("I", "return", f"will resume at {label}[{resume_idx}]")

        elif isinstance(stmt, ast_mod.InputStmt):
            user_text = self._wait_for_input(stmt.prompt)
            self.runtime.set(stmt.name, user_text)
            _log("I", "input", f"stored {stmt.name}={user_text}")

        elif isinstance(stmt, ast_mod.IfStmt):
            pass

        elif isinstance(stmt, ast_mod.WhileStmt):
            pass

        elif isinstance(stmt, ast_mod.WaitStmt):
            if stmt.is_click:
                self._wait_for_continue()
            elif isinstance(stmt.duration, (int, float)):
                import time
                time.sleep(stmt.duration)

        elif isinstance(stmt, ast_mod.SaveStmt):
            pass

        elif isinstance(stmt, ast_mod.LoadStmt):
            pass

        elif isinstance(stmt, ast_mod.QuitStmt):
            pass

        elif isinstance(stmt, ast_mod.PythonBlockStmt):
            if self.runtime.pending_jump:
                _log("I", "python", f"jump -> {self.runtime.pending_jump}")

        elif isinstance(stmt, ast_mod.IncludeStmt):
            self._last_include_stmt = stmt
            self._exec_include()

    def _exec_include(self):
        import core.ast as ast_mod
        stmt = self._last_include_stmt
        if not stmt:
            return

        if self._script_dir:
            target = self._script_dir / stmt.path
        else:
            target = Path(stmt.path)

        if not target.exists():
            self._show_dialogue(None, f"[错误] 无法加载脚本: {stmt.path}")
            return

        _log("I", "include", f"loading {target}")
        src = target.read_text(encoding="utf-8")
        lexer = Lexer(src, str(target))
        tokens = lexer.tokenize()
        parser = Parser(tokens, str(target))
        included_program = parser.parse()

        for s in included_program.statements:
            if isinstance(s, ast_mod.LabelStmt):
                if s.name not in self.interp.labels:
                    self.interp.labels[s.name] = s.body
            else:
                self._exec_stmt(s)
                if not self.runtime.running:
                    return

    def _exec_interact(self, actions, fallbacks):
        _log("I", "interact", [a.name for a in actions])
        available = [a for a in actions if not a.condition or self.interp._eval_expr(a.condition)]
        fb_texts = []
        for fb in fallbacks:
            if hasattr(fb, 'value'):
                fb_texts.append(fb.value)
            else:
                fb_texts.append(str(fb))
        self._ui_call("handleInteract", "你想做什么？", fb_texts)

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
                fb = random.choice(fb_texts) if fb_texts else "..."
                _log("I", "interact", f"fallback: {fb}")
                self._show_dialogue(None, fb)
                self._ui_call("handleInteract", "你想做什么？", fb_texts)

    def _match_action(self, user_text: str, actions: list):
        if self.interp.ai_engine and self.interp.ai_engine.provider != "keyword":
            matched_name = self.interp.ai_engine.match_action(
                user_input=user_text,
                actions=actions,
                runtime=self.runtime,
            )
            if matched_name:
                _log("I", "ai_match", f"matched: {matched_name}")
                for a in actions:
                    if a.name == matched_name:
                        return a
            else:
                _log("I", "ai_match", f"no match, fallback to fuzzywuzzy")

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

    def _get_save_path(self, slot: str) -> Path:
        return self._save_dir / f"{slot}.json"

    def _do_save(self, slot: str = None):
        slot = slot or self.runtime._save_slot
        save_data = self.runtime.save_game(slot)
        save_path = self._get_save_path(slot)

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            _log("I", "save", f"saved to {save_path}")
            self._ui_call("showSaveMessage", f"游戏已保存 [{slot}]")
            self._wait_for_continue()
        except Exception as e:
            _log("E", "save", str(e))
            self._ui_call("showSaveMessage", f"保存失败: {e}")
            self._wait_for_continue()

    def _do_load(self, slot: str = None):
        slot = slot or self.runtime._load_slot
        save_path = self._get_save_path(slot)

        if not save_path.exists():
            _log("W", "load", f"no save file: {save_path}")
            self._ui_call("showSaveMessage", f"存档不存在 [{slot}]")
            self._wait_for_continue()
            return

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)
            success = self.runtime.load_game(save_data)
            if success:
                _log("I", "load", f"loaded from {save_path}")
                self._call_stack.clear()
                self.runtime.clear_pending()
                self.runtime.running = True
                self._ui_call("showSaveMessage", f"已加载存档 [{slot}]")
                self._wait_for_continue()
                self.runtime.set_jump(self.runtime.current_label)
            else:
                self._ui_call("showSaveMessage", "加载存档失败")
                self._wait_for_continue()
        except Exception as e:
            _log("E", "load", str(e))
            self._ui_call("showSaveMessage", f"加载失败: {e}")
            self._wait_for_continue()


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
                error_msg = str(e)
                if hasattr(e, 'line') and e.line:
                    src_line = ""
                    if game_runner.interp:
                        src_line = game_runner.interp.get_source_line(e.filename, e.line)
                    if src_line:
                        error_msg = f"[{e.filename}:{e.line}:{e.col}] {src_line.strip()}\n{error_msg}"
                game_runner._show_dialogue(None, f"错误: {error_msg}")

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

    @api_method
    def get_save_slots(self):
        if not game_runner._save_dir or not game_runner._save_dir.exists():
            return []
        slots = []
        for f in sorted(game_runner._save_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as sf:
                    data = json.load(sf)
                slots.append({
                    "name": f.stem,
                    "timestamp": data.get("timestamp", 0),
                    "playtime": data.get("playtime", 0),
                    "label": data.get("current_label", ""),
                })
            except Exception:
                slots.append({"name": f.stem, "timestamp": 0, "playtime": 0, "label": ""})
        return slots

    @api_method
    def save_game(self, slot: str):
        if not slot or ".." in slot:
            raise ApiError(400, "无效的存档名")
        if game_runner._save_dir:
            game_runner._do_save(slot)
            return True
        raise ApiError(500, "存档目录未初始化")

    @api_method
    def load_game(self, slot: str):
        if not slot or ".." in slot:
            raise ApiError(400, "无效的存档名")
        if game_runner._running:
            game_runner._do_load(slot)
            return True
        raise ApiError(409, "游戏未运行")

    @api_method
    def delete_save(self, slot: str):
        if not slot or ".." in slot:
            raise ApiError(400, "无效的存档名")
        save_path = game_runner._get_save_path(slot) if game_runner._save_dir else None
        if save_path and save_path.exists():
            save_path.unlink()
            return True
        raise ApiError(404, "存档不存在")

    @api_method
    def reload_script(self):
        if not game_runner._running:
            raise ApiError(409, "游戏未运行")
        if not game_runner._script_dir:
            raise ApiError(500, "无法获取脚本目录")
        game_runner.stop()
        import time
        time.sleep(0.1)
        proj = project_store.get_project(launcher_api.current_project.get("id", "") if launcher_api.current_project else "")
        if not proj:
            raise ApiError(404, "项目信息丢失")
        script_path = proj.get("script_main", "")
        if not script_path or not Path(script_path).exists():
            raise ApiError(404, "主脚本不存在")
        ai_provider = config_store.get("default_ai_provider", "keyword")
        game_runner.reset()
        game_runner._running = True
        game_runner.load_script(script_path)
        game_runner.runtime.running = True
        ai_config = {"provider": ai_provider}
        models = config_store.get_ai_models()
        for m in models:
            if m.get("provider") == ai_provider:
                ai_config["model"] = m.get("model", "")
                ai_config["api_key"] = m.get("api_key", "")
                if m.get("base_url"):
                    ai_config["url"] = m["base_url"]
                break
        game_runner.interp = Interpreter(runtime=game_runner.runtime, ai_config=ai_config, script_dir=game_runner._script_dir)
        game_runner.interp._collect_labels(game_runner.program)
        game_runner._python_scope["qf"] = game_runner.interp.qf_ctx

        def run_game():
            try:
                game_runner._run_program()
            except Exception as e:
                _log("E", "game", str(e))
                app_logger.error(f"游戏运行错误: {e}")
                error_msg = str(e)
                if hasattr(e, 'line') and e.line:
                    src_line = ""
                    if game_runner.interp:
                        src_line = game_runner.interp.get_source_line(e.filename, e.line)
                    if src_line:
                        error_msg = f"[{e.filename}:{e.line}:{e.col}] {src_line.strip()}\n{error_msg}"
                game_runner._show_dialogue(None, f"错误: {error_msg}")
            finally:
                game_runner._running = False

        game_runner._show_dialogue(None, "脚本已重新加载")
        threading.Thread(target=run_game, daemon=True).start()
        return True


launcher_api = LauncherApi()
