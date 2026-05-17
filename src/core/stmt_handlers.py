from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.ast import Stmt
    from core.interpreter import Interpreter


class StmtHandler(ABC):
    def __init__(self, interpreter: 'Interpreter'):
        self.interpreter = interpreter
        self.runtime = interpreter.runtime

    @abstractmethod
    def can_handle(self, stmt: 'Stmt') -> bool:
        pass

    @abstractmethod
    def execute(self, stmt: 'Stmt') -> None:
        pass

    def _interpolate(self, text: str) -> str:
        return self.interpreter._interpolate(text)

    def _eval_expr(self, expr):
        return self.interpreter._eval_expr(expr)


class DefineCharacterStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import DefineCharacterStmt
        return isinstance(stmt, DefineCharacterStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import DefineCharacterStmt
        from core.runtime import Character
        assert isinstance(stmt, DefineCharacterStmt)
        self.runtime.add_character(stmt.name, Character(
            name=stmt.display_name,
            avatar=stmt.avatar,
            color=stmt.color,
        ))


class BgStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import BgStmt
        return isinstance(stmt, BgStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import BgStmt
        assert isinstance(stmt, BgStmt)
        self.runtime.background = stmt.path


class DialogueStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import DialogueStmt
        return isinstance(stmt, DialogueStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import DialogueStmt
        assert isinstance(stmt, DialogueStmt)
        text = self._interpolate(stmt.text)
        self.runtime.queue_dialogue(stmt.character, text)


class InteractStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import InteractStmt
        return isinstance(stmt, InteractStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import InteractStmt
        assert isinstance(stmt, InteractStmt)
        self.runtime.queue_interact(
            actions=stmt.actions,
            fallbacks=stmt.fallbacks,
        )


class OptionsStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import OptionsStmt
        return isinstance(stmt, OptionsStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import OptionsStmt
        assert isinstance(stmt, OptionsStmt)
        self.runtime.queue_options(items=stmt.items)


class LabelStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import LabelStmt
        return isinstance(stmt, LabelStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import LabelStmt
        assert isinstance(stmt, LabelStmt)
        self.runtime.current_label = stmt.name


class JumpStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import JumpStmt
        return isinstance(stmt, JumpStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import JumpStmt
        assert isinstance(stmt, JumpStmt)
        if stmt.is_otherwise:
            self.runtime.set_jump(stmt.target)
        elif stmt.condition:
            if self._eval_expr(stmt.condition):
                self.runtime.set_jump(stmt.target)
        else:
            self.runtime.set_jump(stmt.target)


class CallStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import CallStmt
        return isinstance(stmt, CallStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import CallStmt
        assert isinstance(stmt, CallStmt)
        if stmt.condition and not self._eval_expr(stmt.condition):
            return
        self.runtime.call_stack.append((self.runtime.current_label, self.runtime.statement_index))
        self.runtime.set_jump(stmt.target)


class ReturnStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import ReturnStmt
        return isinstance(stmt, ReturnStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import ReturnStmt
        assert isinstance(stmt, ReturnStmt)
        if self.runtime.call_stack:
            caller_label, caller_index = self.runtime.call_stack.pop()
            self.runtime.current_label = caller_label
            self.runtime.statement_index = caller_index
            self.runtime.pending_jump = None  # 防止继续执行子程序


class VarStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import VarStmt
        return isinstance(stmt, VarStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import VarStmt
        assert isinstance(stmt, VarStmt)
        if stmt.value:
            self.runtime.set(stmt.name, self._eval_expr(stmt.value))
        else:
            self.runtime.set(stmt.name, None)


class BreakStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import BreakStmt
        return isinstance(stmt, BreakStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import BreakStmt
        assert isinstance(stmt, BreakStmt)
        self.runtime.set_jump("__break__")


class ContinueStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import ContinueStmt
        return isinstance(stmt, ContinueStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import ContinueStmt
        assert isinstance(stmt, ContinueStmt)
        self.runtime.set_jump("__continue__")


class SetStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import SetStmt
        return isinstance(stmt, SetStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import SetStmt
        assert isinstance(stmt, SetStmt)
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


class InputStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import InputStmt
        return isinstance(stmt, InputStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import InputStmt
        assert isinstance(stmt, InputStmt)
        self.runtime.queue_input_prompt(stmt.name, stmt.prompt)


class IfStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import IfStmt
        return isinstance(stmt, IfStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import IfStmt
        assert isinstance(stmt, IfStmt)
        for branch in stmt.branches:
            if self._eval_expr(branch.condition):
                self.runtime.statement_index = 0
                self.interpreter._execute_block(branch.body)
                return
        if stmt.else_body:
            self.runtime.statement_index = 0
            self.interpreter._execute_block(stmt.else_body)


class WhileStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import WhileStmt
        return isinstance(stmt, WhileStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import WhileStmt
        assert isinstance(stmt, WhileStmt)
        while self._eval_expr(stmt.condition):
            self.runtime.statement_index = 0
            self.interpreter._execute_block(stmt.body)
            if self.runtime.pending_jump == "__break__":
                self.runtime.pending_jump = None
                return
            if self.runtime.pending_jump == "__continue__":
                self.runtime.pending_jump = None
            if self.runtime.pending_dialogues or self.runtime.pending_input or self.runtime.pending_interact:
                return
            if self.runtime.pending_save or self.runtime.pending_load or self.runtime.pending_quit:
                return


class WaitStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import WaitStmt
        return isinstance(stmt, WaitStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import WaitStmt
        assert isinstance(stmt, WaitStmt)
        self.runtime.queue_dialogue(None, f"[等待 {stmt.duration or '点击'}]")


class SaveStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import SaveStmt
        return isinstance(stmt, SaveStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import SaveStmt
        assert isinstance(stmt, SaveStmt)
        self.runtime.pending_save = True


class LoadStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import LoadStmt
        return isinstance(stmt, LoadStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import LoadStmt
        assert isinstance(stmt, LoadStmt)
        self.runtime.pending_load = True


class QuitStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import QuitStmt
        return isinstance(stmt, QuitStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import QuitStmt
        assert isinstance(stmt, QuitStmt)
        self.runtime.pending_quit = True


class PythonBlockStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import PythonBlockStmt
        return isinstance(stmt, PythonBlockStmt)

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import PythonBlockStmt
        assert isinstance(stmt, PythonBlockStmt)
        self.interpreter._execute_python(stmt.code)


class AudioStmtHandler(StmtHandler):
    def can_handle(self, stmt: 'Stmt') -> bool:
        from core.ast import PlayMusicStmt, PlaySoundStmt, StopMusicStmt, StopSoundStmt, SetVolumeStmt
        return isinstance(stmt, (PlayMusicStmt, PlaySoundStmt, StopMusicStmt, StopSoundStmt, SetVolumeStmt))

    def execute(self, stmt: 'Stmt') -> None:
        from core.ast import PlayMusicStmt, PlaySoundStmt, StopMusicStmt, StopSoundStmt, SetVolumeStmt

        if isinstance(stmt, PlayMusicStmt):
            self.runtime.pending_audio = {
                "type": "play_music",
                "path": stmt.path,
                "loop": stmt.loop,
                "volume": stmt.volume,
                "fade_in": stmt.fade_in,
            }
        elif isinstance(stmt, PlaySoundStmt):
            self.runtime.pending_audio = {
                "type": "play_sound",
                "path": stmt.path,
                "volume": stmt.volume,
            }
        elif isinstance(stmt, StopMusicStmt):
            self.runtime.pending_audio = {
                "type": "stop_music",
                "fade_out": stmt.fade_out,
            }
        elif isinstance(stmt, StopSoundStmt):
            self.runtime.pending_audio = {
                "type": "stop_sound",
            }
        elif isinstance(stmt, SetVolumeStmt):
            if stmt.music_volume >= 0:
                self.runtime.music_volume = stmt.music_volume
                self.runtime.pending_audio = {
                    "type": "set_volume",
                    "music_volume": stmt.music_volume,
                    "sound_volume": self.runtime.sound_volume,
                }
            if stmt.sound_volume >= 0:
                self.runtime.sound_volume = stmt.sound_volume
                self.runtime.pending_audio = {
                    "type": "set_volume",
                    "music_volume": self.runtime.music_volume,
                    "sound_volume": stmt.sound_volume,
                }
