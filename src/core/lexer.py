from core.tokens import TokenType, KEYWORDS
from core.errors import LexerError


class Token:
    def __init__(self, type_: TokenType, value, line: int, col: int):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class Lexer:
    def __init__(self, source: str, filename: str = "<unknown>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent_stack = [0]
        self.at_line_start = True

    def _peek(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self):
        while self.pos < len(self.source) and self.source[self.pos] in (" ", "\t"):
            self._advance()

    def _read_string(self, quote: str) -> str:
        result = []
        self._advance()
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch == "\\":
                self._advance()
                esc = self._advance()
                if esc == "n":
                    result.append("\n")
                elif esc == "t":
                    result.append("\t")
                elif esc == "\\":
                    result.append("\\")
                elif esc == quote:
                    result.append(quote)
                else:
                    result.append("\\")
                    result.append(esc)
            elif ch == quote:
                self._advance()
                return "".join(result)
            elif ch == "\n":
                raise LexerError("字符串中不允许换行", self.line, self.col, self.filename)
            else:
                result.append(self._advance())
        raise LexerError("未闭合的字符串", self.line, self.col, self.filename)

    def _read_number(self) -> Token:
        start_col = self.col
        start_line = self.line
        result = []
        has_dot = False
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == "."):
            if self.source[self.pos] == ".":
                if has_dot:
                    break
                has_dot = True
            result.append(self._advance())
        value = float("".join(result)) if has_dot else int("".join(result))
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def _read_identifier(self) -> Token:
        start_col = self.col
        start_line = self.line
        result = []
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == "_"):
            result.append(self._advance())
        text = "".join(result)
        type_ = KEYWORDS.get(text, TokenType.IDENTIFIER)
        return Token(type_, text, start_line, start_col)

    def _handle_indent(self) -> list:
        indent = 0
        saved_pos = self.pos
        saved_line = self.line
        saved_col = self.col
        while self.pos < len(self.source) and self.source[self.pos] in (" ", "\t"):
            ch = self.source[self.pos]
            if ch == " ":
                indent += 1
            elif ch == "\t":
                indent += 4
            self.pos += 1

        if self.pos < len(self.source) and self.source[self.pos] == "\n":
            self.pos += 1
            self.line += 1
            self.col = 1
            return []

        tokens = []
        if indent > self.indent_stack[-1]:
            self.indent_stack.append(indent)
            tokens.append(Token(TokenType.INDENT, indent, self.line, self.col))
        elif indent < self.indent_stack[-1]:
            while self.indent_stack and indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, indent, self.line, self.col))
        self.pos = saved_pos
        self.line = saved_line
        self.col = saved_col
        return tokens

    def tokenize(self) -> list:
        tokens = []

        while self.pos < len(self.source):
            ch = self._peek()
            next_ch = self._peek_next()

            if ch == "#":
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
                continue

            if ch in (" ", "\t"):
                if self.at_line_start:
                    indent_tokens = self._handle_indent()
                    if indent_tokens:
                        tokens.extend(indent_tokens)
                        self.at_line_start = False
                    else:
                        while self.pos < len(self.source) and self._peek() in (" ", "\t"):
                            self._advance()
                else:
                    self._skip_whitespace()
                continue

            if ch == "\n":
                self._advance()
                self.at_line_start = True
                tokens.append(Token(TokenType.NEWLINE, "\n", self.line - 1, 1))
                continue

            self.at_line_start = False

            if ch == '"':
                value = self._read_string('"')
                tokens.append(Token(TokenType.STRING, value, self.line, self.col))
                continue

            if ch == "'":
                value = self._read_string("'")
                tokens.append(Token(TokenType.STRING, value, self.line, self.col))
                continue

            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self._read_identifier())
                continue

            if ch == "+" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", self.line, self.col - 2))
                continue

            if ch == "+":
                self._advance()
                tokens.append(Token(TokenType.PLUS, "+", self.line, self.col - 1))
                continue

            if ch == "-" and next_ch == ">":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.ARROW, "->", self.line, self.col - 2))
                continue

            if ch == "-" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", self.line, self.col - 2))
                continue

            if ch == "-":
                self._advance()
                tokens.append(Token(TokenType.MINUS, "-", self.line, self.col - 1))
                continue

            if ch == "*" and next_ch == "*":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.POWER, "**", self.line, self.col - 2))
                continue

            if ch == "*" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.MULTIPLY_ASSIGN, "*=", self.line, self.col - 2))
                continue

            if ch == "*":
                self._advance()
                tokens.append(Token(TokenType.MULTIPLY, "*", self.line, self.col - 1))
                continue

            if ch == "/" and next_ch == "/":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.INT_DIVIDE, "//", self.line, self.col - 2))
                continue

            if ch == "/" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.DIVIDE_ASSIGN, "/=", self.line, self.col - 2))
                continue

            if ch == "/":
                self._advance()
                tokens.append(Token(TokenType.DIVIDE, "/", self.line, self.col - 1))
                continue

            if ch == "%":
                self._advance()
                tokens.append(Token(TokenType.MODULO, "%", self.line, self.col - 1))
                continue

            if ch == "=" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.EQUAL, "==", self.line, self.col - 2))
                continue

            if ch == "=":
                self._advance()
                tokens.append(Token(TokenType.ASSIGN, "=", self.line, self.col - 1))
                continue

            if ch == "!" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.NOT_EQUAL, "!=", self.line, self.col - 2))
                continue

            if ch == "<" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.LESS_EQUAL, "<=", self.line, self.col - 2))
                continue

            if ch == "<":
                self._advance()
                tokens.append(Token(TokenType.LESS, "<", self.line, self.col - 1))
                continue

            if ch == ">" and next_ch == "=":
                self._advance()
                self._advance()
                tokens.append(Token(TokenType.GREATER_EQUAL, ">=", self.line, self.col - 2))
                continue

            if ch == ">":
                self._advance()
                tokens.append(Token(TokenType.GREATER, ">", self.line, self.col - 1))
                continue

            if ch == "(":
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", self.line, self.col - 1))
                continue

            if ch == ")":
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", self.line, self.col - 1))
                continue

            if ch == ":":
                self._advance()
                tokens.append(Token(TokenType.COLON, ":", self.line, self.col - 1))
                continue

            if ch == ",":
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", self.line, self.col - 1))
                continue

            raise LexerError(f"未知字符: {ch!r}", self.line, self.col, self.filename)

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, 0, self.line, self.col))

        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens
