"""QriaFiction - 互动小说脚本语言解释器"""

from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime
from core.errors import LexerError, SyntaxError, SemanticError, RuntimeError


def compile_source(source: str, filename: str = "<source>") -> Interpreter:
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename)
    program = parser.parse()
    interp = Interpreter()
    return interp, program


def run_source(source: str, filename: str = "<source>", ai_config: dict = None) -> Interpreter:
    interp, program = compile_source(source, filename)
    interp = Interpreter(ai_config=ai_config)
    interp.run(program)
    return interp


__all__ = [
    "Lexer",
    "Parser",
    "Interpreter",
    "Runtime",
    "compile_source",
    "run_source",
    "LexerError",
    "SyntaxError",
    "SemanticError",
    "RuntimeError",
]
