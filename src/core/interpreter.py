import random
from pathlib import Path

from core.ast import *
from core.runtime import Runtime, Character
from core.ai_engine import AIEngine
from core.errors import RuntimeError as QFRuntimeError
from core.text_utils import interpolate_text


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

    def run(self, program: Program):
        self._collect_labels(program)
        if "start" in self.labels:
            self._execute_block(self.labels["start"])
        else:
            self._execute_block(program.statements)

    def _collect_labels(self, program: Program):
        for stmt in program.statements:
            if isinstance(stmt, LabelStmt):
                self.labels[stmt.name] = stmt.body

    def _execute_block(self, statements: list):
        i = 0
        while i < len(statements) and self.runtime.running:
            if self.runtime.pending_jump:
                target = self.runtime.pending_jump
                self.runtime.pending_jump = None
                if target in self.labels:
                    self._execute_block(self.labels[target])
                    return
                else:
                    raise QFRuntimeError(f"未知标签: {target}")

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

            i += 1

    def _interpolate(self, text: str) -> str:
        return interpolate_text(
            text=text,
            get_var_func=self.runtime.get,
            python_scope=None,
            qf_ctx=self.qf_ctx,
        )

    def _execute(self, stmt: Stmt):
        if isinstance(stmt, DefineCharacterStmt):
            self.runtime.add_character(stmt.name, Character(
                name=stmt.display_name,
                avatar=stmt.avatar,
                color=stmt.color,
            ))

        elif isinstance(stmt, BgStmt):
            self.runtime.background = stmt.path

        elif isinstance(stmt, DialogueStmt):
            text = self._interpolate(stmt.text)
            self.runtime.queue_dialogue(stmt.character, text)

        elif isinstance(stmt, InteractStmt):
            self.runtime.queue_interact(
                actions=stmt.actions,
                fallbacks=stmt.fallbacks,
            )

        elif isinstance(stmt, LabelStmt):
            self.runtime.current_label = stmt.name

        elif isinstance(stmt, JumpStmt):
            if stmt.is_otherwise:
                self.runtime.set_jump(stmt.target)
            elif stmt.condition:
                if self._eval_expr(stmt.condition):
                    self.runtime.set_jump(stmt.target)
            else:
                self.runtime.set_jump(stmt.target)

        elif isinstance(stmt, CallStmt):
            if stmt.condition and not self._eval_expr(stmt.condition):
                return
            self.runtime.call_stack.append(self.runtime.current_label)
            self.runtime.set_jump(stmt.target)

        elif isinstance(stmt, ReturnStmt):
            if self.runtime.call_stack:
                caller = self.runtime.call_stack.pop()
                self.runtime.set_jump(caller)

        elif isinstance(stmt, VarStmt):
            if stmt.value:
                self.runtime.set(stmt.name, self._eval_expr(stmt.value))
            else:
                self.runtime.set(stmt.name, None)

        elif isinstance(stmt, BreakStmt):
            self.runtime.set_jump("__break__")

        elif isinstance(stmt, ContinueStmt):
            self.runtime.set_jump("__continue__")

        elif isinstance(stmt, SetStmt):
            value = self._eval_expr(stmt.value)
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
                self.runtime.set(stmt.name, current / value if value else current)

        elif isinstance(stmt, InputStmt):
            self.runtime.queue_input_prompt(stmt.name, stmt.prompt)

        elif isinstance(stmt, IfStmt):
            for branch in stmt.branches:
                if self._eval_expr(branch.condition):
                    self._execute_block(branch.body)
                    return
            if stmt.else_body:
                self._execute_block(stmt.else_body)

        elif isinstance(stmt, WhileStmt):
            while self._eval_expr(stmt.condition):
                self._execute_block(stmt.body)
                if self.runtime.pending_jump == "__break__":
                    self.runtime.pending_jump = None
                    return
                if self.runtime.pending_jump == "__continue__":
                    self.runtime.pending_jump = None
                if self.runtime.pending_dialogues or self.runtime.pending_input or self.runtime.pending_interact:
                    return
                if self.runtime.pending_save or self.runtime.pending_load or self.runtime.pending_quit:
                    return

        elif isinstance(stmt, WaitStmt):
            self.runtime.queue_dialogue(None, f"[等待 {stmt.duration or '点击'}]")

        elif isinstance(stmt, SaveStmt):
            self.runtime.pending_save = True

        elif isinstance(stmt, LoadStmt):
            self.runtime.pending_load = True

        elif isinstance(stmt, QuitStmt):
            self.runtime.pending_quit = True

        elif isinstance(stmt, PythonBlockStmt):
            self._execute_python(stmt.code)

        elif isinstance(stmt, IncludeStmt):
            self._execute_include(stmt.path)

    def _execute_include(self, path: str):
        if self.script_dir:
            target = self.script_dir / path
        else:
            target = Path(path)

        if not target.exists():
            raise QFRuntimeError(f"无法加载脚本文件: {path}")

        from core.lexer import Lexer
        from core.parser import Parser

        src = target.read_text(encoding="utf-8")
        self._source_cache[str(target)] = src.split("\n")
        lexer = Lexer(src, str(target))
        tokens = lexer.tokenize()
        parser = Parser(tokens, str(target))
        included_program = parser.parse()

        self._collect_labels(included_program)
        for stmt in included_program.statements:
            if not isinstance(stmt, LabelStmt):
                self._execute(stmt)
                if self.runtime.pending_jump or self.runtime.pending_dialogues or self.runtime.pending_input or self.runtime.pending_save or self.runtime.pending_load:
                    return

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
