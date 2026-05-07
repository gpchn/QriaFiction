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
        self.indent_stack = [0]

    def _tokenize_content(self, text: str, line_num: int, col_offset: int) -> list:
        tokens = []
        i = 0
        while i < len(text):
            ch = text[i]
            nc = text[i + 1] if i + 1 < len(text) else "\0"

            if ch in (" ", "\t"):
                i += 1
                continue

            if ch == '"':
                j = i + 1
                parts = []
                while j < len(text):
                    if text[j] == "\\":
                        j += 1
                        if j < len(text):
                            e = text[j]
                            if e == "n": parts.append("\n")
                            elif e == "t": parts.append("\t")
                            elif e == "\\": parts.append("\\")
                            elif e == '"': parts.append('"')
                            else: parts.extend(["\\", e])
                        j += 1
                    elif text[j] == '"':
                        break
                    else:
                        parts.append(text[j])
                        j += 1
                tokens.append(Token(TokenType.STRING, "".join(parts), line_num, col_offset + i))
                i = j + 1
                continue

            if ch == "'":
                j = i + 1
                parts = []
                while j < len(text) and text[j] != "'":
                    parts.append(text[j])
                    j += 1
                tokens.append(Token(TokenType.STRING, "".join(parts), line_num, col_offset + i))
                i = j + 1
                continue

            if ch.isdigit():
                j = i
                has_dot = False
                while j < len(text) and (text[j].isdigit() or text[j] == "."):
                    if text[j] == ".":
                        if has_dot: break
                        has_dot = True
                    j += 1
                num = float(text[i:j]) if has_dot else int(text[i:j])
                tokens.append(Token(TokenType.NUMBER, num, line_num, col_offset + i))
                i = j
                continue

            if ch.isalpha() or ch == "_":
                j = i
                while j < len(text) and (text[j].isalnum() or text[j] == "_"):
                    j += 1
                word = text[i:j]
                tokens.append(Token(KEYWORDS.get(word, TokenType.IDENTIFIER), word, line_num, col_offset + i))
                i = j
                continue

            ops = {
                "+=": TokenType.PLUS_ASSIGN, "-=": TokenType.MINUS_ASSIGN,
                "*=": TokenType.MULTIPLY_ASSIGN, "/=": TokenType.DIVIDE_ASSIGN,
                "**": TokenType.POWER, "//": TokenType.INT_DIVIDE,
                "->": TokenType.ARROW, "==": TokenType.EQUAL,
                "!=": TokenType.NOT_EQUAL, "<=": TokenType.LESS_EQUAL,
                ">=": TokenType.GREATER_EQUAL,
            }
            matched = False
            for op_str, op_type in ops.items():
                if text[i:i+len(op_str)] == op_str:
                    tokens.append(Token(op_type, op_str, line_num, col_offset + i))
                    i += len(op_str)
                    matched = True
                    break
            if matched:
                continue

            singles = {
                "+": TokenType.PLUS, "-": TokenType.MINUS,
                "*": TokenType.MULTIPLY, "/": TokenType.DIVIDE,
                "%": TokenType.MODULO, "=": TokenType.ASSIGN,
                "<": TokenType.LESS, ">": TokenType.GREATER,
                "(": TokenType.LPAREN, ")": TokenType.RPAREN,
                ":": TokenType.COLON, ",": TokenType.COMMA,
            }
            if ch in singles:
                tokens.append(Token(singles[ch], ch, line_num, col_offset + i))
                i += 1
                continue

            raise LexerError(f"未知字符: {ch!r}", line_num, col_offset + i, self.filename)

        return tokens

    def _strip_comment(self, text: str) -> str:
        in_str = False
        str_ch = None
        skip_next = False
        for ci, c in enumerate(text):
            if skip_next:
                skip_next = False
                continue
            if in_str:
                if c == "\\":
                    skip_next = True
                elif c == str_ch:
                    in_str = False
                continue
            if c in ('"', "'"):
                in_str = True
                str_ch = c
            elif c == "#":
                return text[:ci]
        return text

    def tokenize(self) -> list:
        tokens = []
        lines = self.source.split("\n")
        i = 0

        while i < len(lines):
            raw = lines[i]
            line_num = i + 1

            text = self._strip_comment(raw)

            # Skip blank/comment-only lines
            if not text.strip():
                i += 1
                continue

            # Measure indent
            indent = 0
            for c in text:
                if c == " ": indent += 1
                elif c == "\t": indent += 4
                else: break
            content = text[indent:]
            col_offset = 1 + indent

            # Check for python: block
            if content == "python:":
                raw_lines = []
                j = i + 1
                while j < len(lines):
                    rl = lines[j]
                    if not rl.strip():
                        raw_lines.append("")
                        j += 1
                        continue
                    ri = 0
                    for c in rl:
                        if c in (" ", "\t"): ri += 1
                        else: break
                    if ri <= indent:
                        break
                    raw_lines.append(rl[indent:])
                    j += 1

                if raw_lines:
                    # Strip common leading whitespace from all non-empty lines
                    min_indent = float('inf')
                    for line in raw_lines:
                        if line.strip():
                            ci = 0
                            for c in line:
                                if c in (" ", "\t"): ci += 1
                                else: break
                            if ci < min_indent:
                                min_indent = ci
                    if min_indent == float('inf'):
                        min_indent = 0
                    code_lines = [line[min_indent:] if line else line for line in raw_lines]
                    code = "\n".join(code_lines)
                    tokens.append(Token(TokenType.PYTHON_CODE, code, line_num, col_offset))
                else:
                    tokens.append(Token(TokenType.PYTHON, "python", line_num, col_offset))
                i = j
                continue

            # Indent management
            if indent > self.indent_stack[-1]:
                self.indent_stack.append(indent)
                tokens.append(Token(TokenType.INDENT, indent, line_num, col_offset))
            elif indent < self.indent_stack[-1]:
                while self.indent_stack and indent < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    tokens.append(Token(TokenType.DEDENT, indent, line_num, col_offset))

            # Tokenize content
            tokens.extend(self._tokenize_content(content, line_num, col_offset))
            tokens.append(Token(TokenType.NEWLINE, "\n", line_num, 1))
            i += 1

        # Close all indent levels
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, 0, len(lines), 1))

        tokens.append(Token(TokenType.EOF, None, len(lines), 1))
        return tokens
