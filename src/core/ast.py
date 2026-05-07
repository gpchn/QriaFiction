from dataclasses import dataclass, field
from core.tokens import TokenType


@dataclass
class ASTNode:
    line: int = 0
    col: int = 0


@dataclass
class Expr(ASTNode):
    pass


@dataclass
class NumberExpr(Expr):
    value: int | float = 0


@dataclass
class StringExpr(Expr):
    value: str = ""


@dataclass
class BoolExpr(Expr):
    value: bool = False


@dataclass
class VarExpr(Expr):
    name: str = ""


@dataclass
class BinOpExpr(Expr):
    left: Expr = None
    operator: str = ""
    right: Expr = None


@dataclass
class UnaryOpExpr(Expr):
    operator: str = ""
    operand: Expr = None


@dataclass
class PythonExpr(Expr):
    code: str = ""


@dataclass
class Stmt(ASTNode):
    pass


@dataclass
class Program(ASTNode):
    statements: list = field(default_factory=list)


@dataclass
class DefineCharacterStmt(Stmt):
    name: str = ""
    display_name: str = ""
    avatar: str = ""
    color: str = ""


@dataclass
class BgStmt(Stmt):
    path: str | None = None


@dataclass
class InteractAction:
    name: str = ""
    label: str = ""
    desc: str = ""
    condition: Expr = None


@dataclass
class InteractStmt(Stmt):
    actions: list = field(default_factory=list)
    fallbacks: list = field(default_factory=list)


@dataclass
class DialogueStmt(Stmt):
    character: str | None = None
    text: str = ""


@dataclass
class LabelStmt(Stmt):
    name: str = ""
    body: list = field(default_factory=list)


@dataclass
class JumpStmt(Stmt):
    target: str = ""
    condition: Expr = None
    is_otherwise: bool = False


@dataclass
class CallStmt(Stmt):
    target: str = ""
    condition: Expr = None


@dataclass
class ReturnStmt(Stmt):
    pass


@dataclass
class VarStmt(Stmt):
    name: str = ""
    value: Expr = None


@dataclass
class SetStmt(Stmt):
    name: str = ""
    operator: str = ""
    value: Expr = None


@dataclass
class InputStmt(Stmt):
    name: str = ""
    prompt: str = ""


@dataclass
class IfBranch:
    condition: Expr = None
    body: list = field(default_factory=list)


@dataclass
class IfStmt(Stmt):
    branches: list = field(default_factory=list)
    else_body: list = field(default_factory=list)


@dataclass
class WhileStmt(Stmt):
    condition: Expr = None
    body: list = field(default_factory=list)


@dataclass
class WaitStmt(Stmt):
    duration: float | None = None
    is_click: bool = False


@dataclass
class SaveStmt(Stmt):
    pass


@dataclass
class LoadStmt(Stmt):
    pass


@dataclass
class QuitStmt(Stmt):
    pass


@dataclass
class PythonBlockStmt(Stmt):
    code: str = ""


@dataclass
class IncludeStmt(Stmt):
    path: str = ""
