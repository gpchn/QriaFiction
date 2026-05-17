from enum import Enum, auto


class TokenType(Enum):
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    IDENTIFIER = auto()

    DEFINE = auto()
    CHARACTER = auto()
    BG = auto()
    NONE = auto()
    INTERACT = auto()
    FALLBACK = auto()
    OPTIONS = auto()
    DESC = auto()
    CONDITION = auto()
    LABEL = auto()
    JUMP = auto()
    CALL = auto()
    RETURN = auto()
    VAR = auto()
    SET = auto()
    INPUT = auto()
    IF = auto()
    ELSEIF = auto()
    ELSE = auto()
    WHILE = auto()
    BREAK = auto()
    CONTINUE = auto()
    WAIT = auto()
    CLICK = auto()
    SAVE = auto()
    LOAD = auto()
    QUIT = auto()
    PYTHON = auto()
    PYTHON_CODE = auto()
    END = auto()
    WITH = auto()
    AT = auto()
    OTHERWISE = auto()
    MUSIC = auto()
    SOUND = auto()
    VOLUME = auto()
    FADE = auto()
    STOP = auto()
    LOOP = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    INT_DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    MULTIPLY_ASSIGN = auto()
    DIVIDE_ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    GREATER = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()

    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    ARROW = auto()

    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()


KEYWORDS = {
    "define": TokenType.DEFINE,
    "character": TokenType.CHARACTER,
    "bg": TokenType.BG,
    "none": TokenType.NONE,
    "interact": TokenType.INTERACT,
    "fallback": TokenType.FALLBACK,
    "options": TokenType.OPTIONS,
    "desc": TokenType.DESC,
    "condition": TokenType.CONDITION,
    "label": TokenType.LABEL,
    "jump": TokenType.JUMP,
    "call": TokenType.CALL,
    "return": TokenType.RETURN,
    "var": TokenType.VAR,
    "set": TokenType.SET,
    "input": TokenType.INPUT,
    "if": TokenType.IF,
    "elseif": TokenType.ELSEIF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "wait": TokenType.WAIT,
    "click": TokenType.CLICK,
    "save": TokenType.SAVE,
    "load": TokenType.LOAD,
    "quit": TokenType.QUIT,
    "python": TokenType.PYTHON,
    "end": TokenType.END,
    "with": TokenType.WITH,
    "at": TokenType.AT,
    "otherwise": TokenType.OTHERWISE,
    "music": TokenType.MUSIC,
    "sound": TokenType.SOUND,
    "volume": TokenType.VOLUME,
    "fade": TokenType.FADE,
    "stop": TokenType.STOP,
    "loop": TokenType.LOOP,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}
