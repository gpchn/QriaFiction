from core.lexer import Lexer
from core.parser import Parser
from core.interpreter import Interpreter
from core.runtime import Runtime
from core.errors import LexerError, QFSyntaxError, SemanticError, QFRuntimeError


def compile_source(source: str, filename: str = "<source>"):
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, filename)
    program = parser.parse()
    interp = Interpreter()
    return interp, program


def run_source(source: str, filename: str = "<source>", ai_config: dict = None):
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
    "QFSyntaxError",
    "SemanticError",
    "QFRuntimeError",
]
