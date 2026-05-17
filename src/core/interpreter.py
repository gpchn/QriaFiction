import random
from pathlib import Path

from core.ast import *
from core.runtime import Runtime, Character
from core.ai_engine import AIEngine
from core.errors import QFRuntimeError
from core.text_utils import interpolate_text
from core.stmt_handlers import (
    StmtHandler,
    DefineCharacterStmtHandler,
    BgStmtHandler,
    DialogueStmtHandler,
    InteractStmtHandler,
    OptionsStmtHandler,
    LabelStmtHandler,
    JumpStmtHandler,
    CallStmtHandler,
    ReturnStmtHandler,
    VarStmtHandler,
    BreakStmtHandler,
    ContinueStmtHandler,
    SetStmtHandler,
    InputStmtHandler,
    IfStmtHandler,
    WhileStmtHandler,
    WaitStmtHandler,
    SaveStmtHandler,
    LoadStmtHandler,
    QuitStmtHandler,
    PythonBlockStmtHandler,
    AudioStmtHandler,
)


class QriaContext:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    @property
    def user_input(self):
        return self.runtime.get("_user_input")

    @property
    def matched_action(self):
        return self.runtime.get("_matched_action")

    def get(self, name: str):
        return self.runtime.get(name)

    def set(self, name: str, value):
        self.runtime.set(name, value)

    def jump(self, label: str):
        self.runtime.set_jump(label)

    def call(self, label: str):
        self.runtime.call_stack.append(self.runtime.current_label)
        self.runtime.set_jump(label)

    def show_message(self, character: str, text: str):
        self.runtime.queue_dialogue(character, text)

    def set_bg(self, path: str):
        self.runtime.background = path

    def save(self, slot: str = "autosave"):
        self.runtime._save_slot = slot
        self.runtime.pending_save = True

    def load(self, slot: str = "autosave"):
        self.runtime._load_slot = slot
        self.runtime.pending_load = True


class Interpreter:
    def __init__(self, runtime: Runtime = None, ai_config: dict = None, script_dir: Path = None):
        self.runtime = runtime or Runtime()
        self.ai_engine = AIEngine(ai_config)
        self.labels: dict[str, list] = {}
        self.qf_ctx = QriaContext(self.runtime)
        self.script_dir = script_dir
        self._source_cache: dict[str, list[str]] = {}
        self._python_scope: dict = {"qf": None}
        self._script_registry: dict[str, Path] = {}
        self._loaded_scripts: set[str] = set()
        self._main_program: Program = None
        self._main_filename: str = "main.qf"
        self._stmt_handlers = self._init_stmt_handlers()

    def _init_stmt_handlers(self) -> list[StmtHandler]:
        return [
            DefineCharacterStmtHandler(self),
            BgStmtHandler(self),
            DialogueStmtHandler(self),
            InteractStmtHandler(self),
            OptionsStmtHandler(self),
            LabelStmtHandler(self),
            JumpStmtHandler(self),
            CallStmtHandler(self),
            ReturnStmtHandler(self),
            VarStmtHandler(self),
            BreakStmtHandler(self),
            ContinueStmtHandler(self),
            SetStmtHandler(self),
            InputStmtHandler(self),
            IfStmtHandler(self),
            WhileStmtHandler(self),
            WaitStmtHandler(self),
            SaveStmtHandler(self),
            LoadStmtHandler(self),
            QuitStmtHandler(self),
            PythonBlockStmtHandler(self),
            AudioStmtHandler(self),
        ]

    def scan_scripts(self):
        if self.script_dir and self.script_dir.exists():
            for qf_file in self.script_dir.glob("*.qf"):
                script_name = qf_file.stem
                self._script_registry[script_name] = qf_file

    def run(self, program: Program):
        self._main_program = program
        self.scan_scripts()
        self._load_all_scripts()
        self._execute_top_level_statements(program, namespace=None)
        if "start" in self.labels:
            self.runtime.current_label = "start"
            self.runtime.statement_index = 0
            self._execute_block(self.labels["start"])
        else:
            self._execute_block(program.statements)

    def _load_all_scripts(self):
        if self._main_program:
            self._collect_labels(self._main_program, namespace=None)
        self._loaded_scripts.add("main")
        for script_name, script_path in self._script_registry.items():
            if script_name not in self._loaded_scripts:
                self._load_script(script_name, script_path)

    def _load_script(self, script_name: str, script_path: Path):
        if script_name in self._loaded_scripts:
            return
        if not script_path.exists():
            return
        try:
            from core.lexer import Lexer
            from core.parser import Parser
            src = script_path.read_text(encoding="utf-8")
            self._source_cache[str(script_path)] = src.split("\n")
            lexer = Lexer(src, str(script_path))
            tokens = lexer.tokenize()
            parser = Parser(tokens, str(script_path))
            program = parser.parse()
            namespace = script_name
            self._collect_labels(program, namespace=namespace)
            self._execute_top_level_statements(program, namespace)
            self._loaded_scripts.add(script_name)
        except Exception as e:
            pass

    def _load_script_on_demand(self, script_name: str):
        if script_name in self._loaded_scripts:
            return True
        if script_name not in self._script_registry:
            return False
        script_path = self._script_registry[script_name]
        self._load_script(script_name, script_path)
        return script_name in self._loaded_scripts

    def _execute_top_level_statements(self, program: Program, namespace: str):
        for stmt in program.statements:
            if isinstance(stmt, LabelStmt):
                continue
            self._execute(stmt)
            if self.runtime.pending_jump or self.runtime.pending_dialogues or self.runtime.pending_input:
                return
            if self.runtime.pending_save or self.runtime.pending_load or self.runtime.pending_quit:
                return
            if self.runtime.pending_audio:
                return

    def _collect_labels(self, program: Program, namespace: str = None):
        for stmt in program.statements:
            if isinstance(stmt, LabelStmt):
                if namespace:
                    label_name = f"{namespace}.{stmt.name}"
                else:
                    label_name = stmt.name
                self.labels[label_name] = stmt.body

    def _execute_block(self, statements: list):
        while self.runtime.running:
            if self.runtime.pending_jump:
                target = self.runtime.pending_jump
                if target in ("__break__", "__continue__"):
                    return
                self.runtime.pending_jump = None
                if target in self.labels:
                    self.runtime.current_label = target
                    self.runtime.statement_index = 0
                    statements = self.labels[target]
                    continue
                else:
                    raise QFRuntimeError(f"未知标签: {target}")

            i = self.runtime.statement_index
            if i >= len(statements):
                return

            stmt = statements[i]
            self._execute(stmt)

            if self.runtime.pending_jump:
                continue
            if self.runtime.pending_dialogues:
                return
            if self.runtime.pending_input:
                return
            if self.runtime.pending_interact:
                return
            if self.runtime.pending_save or self.runtime.pending_load or self.runtime.pending_quit:
                return

            self.runtime.statement_index = i + 1

    def _interpolate(self, text: str) -> str:
        return interpolate_text(
            text=text,
            get_var_func=self.runtime.get,
            python_scope=None,
            qf_ctx=self.qf_ctx,
        )

    def _execute(self, stmt: Stmt):
        for handler in self._stmt_handlers:
            if handler.can_handle(stmt):
                handler.execute(stmt)
                return
        raise QFRuntimeError(f"未知的语句类型: {type(stmt).__name__}")

    def _execute_python(self, code: str):
        if self._python_scope.get("qf") is None:
            self._python_scope["qf"] = self.qf_ctx
        try:
            exec(code, self._python_scope)
        except Exception as e:
            raise QFRuntimeError(f"Python 执行错误: {e}")

    def _eval_expr(self, expr: Expr):
        if isinstance(expr, NumberExpr):
            return expr.value
        if isinstance(expr, StringExpr):
            return expr.value
        if isinstance(expr, BoolExpr):
            return expr.value
        if isinstance(expr, VarExpr):
            return self.runtime.get(expr.name)
        if isinstance(expr, BinOpExpr):
            left = self._eval_expr(expr.left)
            right = self._eval_expr(expr.right)

            if expr.operator in ("+", "-", "*", "//", "%", "**"):
                if left is None: left = 0
                if right is None: right = 0
            elif expr.operator == "/":
                if left is None: left = 0
                if right is None or right == 0: right = 1

            if expr.operator == "+":
                return left + right
            if expr.operator == "-":
                return left - right
            if expr.operator == "*":
                return left * right
            if expr.operator == "/":
                return left / right
            if expr.operator == "//":
                return left // right
            if expr.operator == "%":
                return left % right
            if expr.operator == "**":
                return left ** right
            if expr.operator == "==":
                return left == right
            if expr.operator == "!=":
                return left != right
            if expr.operator == "<":
                return left < right
            if expr.operator == ">":
                return left > right
            if expr.operator == "<=":
                return left <= right
            if expr.operator == ">=":
                return left >= right
            if expr.operator == "and":
                return left and right
            if expr.operator == "or":
                return left or right
        if isinstance(expr, UnaryOpExpr):
            operand = self._eval_expr(expr.operand)
            if expr.operator == "not":
                return not operand
            if expr.operator == "-":
                return -operand if operand is not None else 0
        raise QFRuntimeError(f"无法计算表达式: {expr}")

    def get_source_line(self, filename: str, line_num: int) -> str:
        if filename in self._source_cache:
            lines = self._source_cache[filename]
            if 0 < line_num <= len(lines):
                return lines[line_num - 1]
        return ""
