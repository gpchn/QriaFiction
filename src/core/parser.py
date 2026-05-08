from core.tokens import TokenType, KEYWORDS
from core.lexer import Token
from core.errors import QFSyntaxError
from core.ast import *


class Parser:
    def __init__(self, tokens: list, filename: str = "<unknown>"):
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    def _peek(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _advance(self):
        tok = self._peek()
        self.pos += 1
        return tok

    def _expect(self, type_: TokenType) -> Token:
        tok = self._peek()
        if tok.type != type_:
            raise QFSyntaxError(
                f"期望 {type_.name}，但得到 {tok.type.name} ({tok.value!r})",
                tok.line, tok.col, self.filename
            )
        return self._advance()

    def _match(self, *types: TokenType) -> Token | None:
        if self._peek().type in types:
            return self._advance()
        return None

    def _consume_newlines(self):
        while self._match(TokenType.NEWLINE):
            pass

    def _parse_program(self) -> Program:
        program = Program()
        self._consume_block_tokens()
        while self._peek().type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt:
                program.statements.append(stmt)
            self._consume_block_tokens()
        return program

    def _parse_statement(self) -> Stmt | None:
        tok = self._peek()

        if tok.type == TokenType.DEFINE:
            return self._parse_define()
        elif tok.type == TokenType.BG:
            return self._parse_bg()
        elif tok.type == TokenType.INTERACT:
            return self._parse_interact()
        elif tok.type == TokenType.LABEL:
            return self._parse_label()
        elif tok.type == TokenType.JUMP:
            return self._parse_jump()
        elif tok.type == TokenType.CALL:
            return self._parse_call()
        elif tok.type == TokenType.RETURN:
            self._advance()
            return ReturnStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.VAR:
            return self._parse_var()
        elif tok.type == TokenType.SET:
            return self._parse_set()
        elif tok.type == TokenType.INPUT:
            return self._parse_input()
        elif tok.type == TokenType.IF:
            return self._parse_if()
        elif tok.type == TokenType.WHILE:
            return self._parse_while()
        elif tok.type == TokenType.WAIT:
            return self._parse_wait()
        elif tok.type == TokenType.SAVE:
            self._advance()
            return SaveStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.LOAD:
            self._advance()
            return LoadStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.QUIT:
            self._advance()
            return QuitStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.PYTHON:
            return self._parse_python()
        elif tok.type == TokenType.PYTHON_CODE:
            return self._parse_python_code()
        elif tok.type == TokenType.MUSIC:
            return self._parse_music()
        elif tok.type == TokenType.SOUND:
            return self._parse_sound()
        elif tok.type == TokenType.STOP:
            return self._parse_stop_audio()
        elif tok.type == TokenType.VOLUME:
            return self._parse_volume()
        elif tok.type == TokenType.BREAK:
            self._advance()
            return BreakStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.CONTINUE:
            self._advance()
            return ContinueStmt(line=tok.line, col=tok.col)
        elif tok.type == TokenType.DEDENT:
            return None
        elif tok.type == TokenType.END:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.COLON:
                return self._parse_label()
            return None
        elif tok.type == TokenType.STRING:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.ARROW:
                return None
            return self._parse_dialogue_or_interact_item()
        elif tok.type == TokenType.IDENTIFIER:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.STRING:
                return self._parse_dialogue()
            return None
        else:
            raise QFSyntaxError(f"意外的 token: {tok.type.name} ({tok.value!r})", tok.line, tok.col, self.filename)

    def _parse_define(self) -> DefineCharacterStmt:
        self._expect(TokenType.DEFINE)
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        self._expect(TokenType.CHARACTER)
        self._expect(TokenType.LPAREN)

        params = {}
        while True:
            if self._peek().type == TokenType.RPAREN:
                break
            key = self._expect(TokenType.IDENTIFIER)
            self._expect(TokenType.ASSIGN)
            val = self._expect(TokenType.STRING)
            params[key.value] = val.value
            if self._match(TokenType.COMMA):
                continue
            break

        self._expect(TokenType.RPAREN)
        return DefineCharacterStmt(
            name=name_tok.value,
            display_name=params.get("name", ""),
            avatar=params.get("avatar", ""),
            color=params.get("color", "#000000"),
        )

    def _parse_bg(self) -> BgStmt:
        self._expect(TokenType.BG)
        tok = self._peek()
        if tok.type == TokenType.NONE:
            self._advance()
            return BgStmt(path=None)
        elif tok.type == TokenType.STRING:
            self._advance()
            return BgStmt(path=tok.value)
        else:
            raise QFSyntaxError(f"期望字符串或 none，得到 {tok.type.name}", tok.line, tok.col, self.filename)

    def _parse_music(self) -> PlayMusicStmt:
        self._expect(TokenType.MUSIC)
        path = self._expect(TokenType.STRING)
        stmt = PlayMusicStmt(path=path.value)
        while self._peek().type in (TokenType.WITH, TokenType.VOLUME, TokenType.LOOP):
            tok = self._peek()
            if tok.type == TokenType.WITH:
                self._advance()
                kw = self._peek()
                if kw.type == TokenType.FADE:
                    self._advance()
                    dur = self._expect(TokenType.NUMBER)
                    stmt.fade_in = dur.value
                elif kw.type == TokenType.VOLUME:
                    self._advance()
                    vol = self._expect(TokenType.NUMBER)
                    stmt.volume = vol.value
            elif tok.type == TokenType.VOLUME:
                self._advance()
                vol = self._expect(TokenType.NUMBER)
                stmt.volume = vol.value
            elif tok.type == TokenType.LOOP:
                self._advance()
                val = self._peek()
                if val.type in (TokenType.TRUE, TokenType.FALSE):
                    self._advance()
                    stmt.loop = (val.type == TokenType.TRUE)
                else:
                    stmt.loop = True
        return stmt

    def _parse_sound(self) -> PlaySoundStmt:
        self._expect(TokenType.SOUND)
        path = self._expect(TokenType.STRING)
        stmt = PlaySoundStmt(path=path.value)
        if self._peek().type == TokenType.VOLUME:
            self._advance()
            vol = self._expect(TokenType.NUMBER)
            stmt.volume = vol.value
        return stmt

    def _parse_stop_audio(self) -> Stmt:
        self._expect(TokenType.STOP)
        tok = self._peek()
        if tok.type == TokenType.MUSIC:
            self._advance()
            stmt = StopMusicStmt()
            if self._peek().type == TokenType.WITH:
                self._advance()
                kw = self._peek()
                if kw.type == TokenType.FADE:
                    self._advance()
                    dur = self._expect(TokenType.NUMBER)
                    stmt.fade_out = dur.value
            return stmt
        elif tok.type == TokenType.SOUND:
            self._advance()
            return StopSoundStmt()
        else:
            raise QFSyntaxError(f"期望 music 或 sound，得到 {tok.type.name}", tok.line, tok.col, self.filename)

    def _parse_volume(self) -> SetVolumeStmt:
        self._expect(TokenType.VOLUME)
        stmt = SetVolumeStmt()
        if self._peek().type == TokenType.MUSIC:
            self._advance()
            self._expect(TokenType.ASSIGN)
            vol = self._expect(TokenType.NUMBER)
            stmt.music_volume = vol.value
        elif self._peek().type == TokenType.SOUND:
            self._advance()
            self._expect(TokenType.ASSIGN)
            vol = self._expect(TokenType.NUMBER)
            stmt.sound_volume = vol.value
        else:
            raise QFSyntaxError(f"期望 music 或 sound，得到 {self._peek().type.name}", self._peek().line, self._peek().col, self.filename)
        return stmt

    def _parse_interact(self) -> InteractStmt:
        self._expect(TokenType.INTERACT)
        self._expect(TokenType.COLON)
        self._consume_block_tokens()

        stmt = InteractStmt()
        while self._peek().type != TokenType.END:
            self._consume_block_tokens()
            if self._peek().type == TokenType.END:
                break
            if self._peek().type == TokenType.FALLBACK:
                self._advance()
                fb_tok = self._expect(TokenType.STRING)
                stmt.fallbacks.append(fb_tok.value)
            elif self._peek().type == TokenType.STRING:
                action = self._parse_interact_action()
                stmt.actions.append(action)
            else:
                raise QFSyntaxError(f"interact 块中期望动作或 fallback", self._peek().line, self._peek().col, self.filename)

        end_tok = self._expect(TokenType.END)
        if not stmt.fallbacks:
            raise QFSyntaxError("interact 块中至少需要一条 fallback", end_tok.line, end_tok.col, self.filename)
        return stmt

    def _parse_param_key(self) -> str:
        tok = self._peek()
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return tok.value
        if tok.type in (TokenType.DESC, TokenType.CONDITION):
            self._advance()
            return tok.value
        raise QFSyntaxError(f"期望参数名，但得到 {tok.type.name} ({tok.value!r})", tok.line, tok.col, self.filename)

    def _parse_interact_action(self) -> InteractAction:
        name_tok = self._expect(TokenType.STRING)
        self._expect(TokenType.ARROW)
        label_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)

        desc = ""
        condition = None

        while True:
            if self._peek().type == TokenType.RPAREN:
                break
            key = self._parse_param_key()
            self._expect(TokenType.ASSIGN)
            if key == "desc":
                val = self._expect(TokenType.STRING)
                desc = val.value
            elif key == "condition":
                condition = self._parse_expression()
            self._match(TokenType.COMMA)

        self._expect(TokenType.RPAREN)
        return InteractAction(
            name=name_tok.value,
            label=label_tok.value,
            desc=desc,
            condition=condition,
        )

    def _parse_dialogue(self) -> DialogueStmt:
        char_tok = self._expect(TokenType.IDENTIFIER)
        text_tok = self._expect(TokenType.STRING)
        return DialogueStmt(character=char_tok.value, text=text_tok.value)

    def _parse_dialogue_or_interact_item(self) -> Stmt:
        text_tok = self._expect(TokenType.STRING)
        if self._peek().type == TokenType.ARROW:
            self._expect(TokenType.ARROW)
            label_tok = self._expect(TokenType.IDENTIFIER)
            self._expect(TokenType.LPAREN)
            desc = ""
            condition = None
            while True:
                if self._peek().type == TokenType.RPAREN:
                    break
                key = self._parse_param_key()
                self._expect(TokenType.ASSIGN)
                if key == "desc":
                    val = self._expect(TokenType.STRING)
                    desc = val.value
                elif key == "condition":
                    condition = self._parse_expression()
                self._match(TokenType.COMMA)
            self._expect(TokenType.RPAREN)
            return InteractStmt(actions=[InteractAction(
                name=text_tok.value,
                label=label_tok.value,
                desc=desc,
                condition=condition,
            )])
        else:
            return DialogueStmt(character=None, text=text_tok.value)

    def _expect_label_name(self) -> Token:
        tok = self._peek()
        if tok.type == TokenType.IDENTIFIER:
            return self._advance()
        raise QFSyntaxError(f"期望标签名，但得到 {tok.type.name} ({tok.value!r})", tok.line, tok.col, self.filename)

    def _parse_label(self) -> LabelStmt:
        self._expect(TokenType.LABEL)
        name_tok = self._expect_label_name()
        self._expect(TokenType.COLON)
        self._consume_block_tokens()

        body = self._parse_block()
        self._expect(TokenType.END)
        return LabelStmt(name=name_tok.value, body=body)

    def _parse_jump(self) -> JumpStmt:
        self._expect(TokenType.JUMP)
        target_tok = self._expect_label_name()
        target = target_tok.value

        condition = None
        is_otherwise = False

        if self._peek().type == TokenType.IF:
            self._advance()
            condition = self._parse_expression()
        elif self._peek().type == TokenType.OTHERWISE:
            self._advance()
            is_otherwise = True

        return JumpStmt(target=target, condition=condition, is_otherwise=is_otherwise)

    def _parse_call(self) -> CallStmt:
        self._expect(TokenType.CALL)
        target_tok = self._expect_label_name()
        target = target_tok.value
        condition = None
        if self._peek().type == TokenType.IF:
            self._advance()
            condition = self._parse_expression()
        return CallStmt(target=target, condition=condition)

    def _parse_var(self) -> VarStmt:
        self._expect(TokenType.VAR)
        name = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.ASSIGN)
        value = self._parse_expression()
        return VarStmt(name=name.value, value=value)

    def _parse_set(self) -> SetStmt:
        self._expect(TokenType.SET)
        name = self._expect(TokenType.IDENTIFIER)
        op_tok = self._peek()
        if op_tok.type in (TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                           TokenType.MULTIPLY_ASSIGN, TokenType.DIVIDE_ASSIGN):
            self._advance()
            op = op_tok.value
        else:
            raise QFSyntaxError(f"期望赋值运算符", op_tok.line, op_tok.col, self.filename)
        value = self._parse_expression()
        return SetStmt(name=name.value, operator=op, value=value)

    def _parse_input(self) -> InputStmt:
        self._expect(TokenType.INPUT)
        name = self._expect(TokenType.IDENTIFIER)
        prompt = self._expect(TokenType.STRING)
        return InputStmt(name=name.value, prompt=prompt.value)

    def _parse_if(self) -> IfStmt:
        self._expect(TokenType.IF)
        condition = self._parse_expression()
        self._expect(TokenType.COLON)
        self._consume_block_tokens()

        branches = []
        else_body = []

        body = self._parse_block(stop_at={TokenType.ELSEIF, TokenType.ELSE})
        branches.append(IfBranch(condition=condition, body=body))

        while self._peek().type == TokenType.ELSEIF:
            self._advance()
            cond = self._parse_expression()
            self._expect(TokenType.COLON)
            self._consume_block_tokens()
            b = self._parse_block(stop_at={TokenType.ELSEIF, TokenType.ELSE})
            branches.append(IfBranch(condition=cond, body=b))

        if self._peek().type == TokenType.ELSE:
            self._advance()
            self._expect(TokenType.COLON)
            self._consume_block_tokens()
            else_body = self._parse_block()

        self._expect(TokenType.END)
        return IfStmt(branches=branches, else_body=else_body)

    def _parse_while(self) -> WhileStmt:
        self._expect(TokenType.WHILE)
        condition = self._parse_expression()
        self._expect(TokenType.COLON)
        self._consume_block_tokens()
        body = self._parse_block()
        self._expect(TokenType.END)
        return WhileStmt(condition=condition, body=body)

    def _consume_block_tokens(self):
        while self._peek().type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            self._advance()

    def _parse_block(self, stop_at: set = None) -> list:
        body = []
        stop_tokens = {TokenType.END}
        if stop_at:
            stop_tokens.update(stop_at)
        while self._peek().type not in stop_tokens:
            self._consume_block_tokens()
            if self._peek().type in stop_tokens:
                break
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
            self._consume_block_tokens()
        return body

    def _parse_wait(self) -> WaitStmt:
        self._expect(TokenType.WAIT)
        tok = self._peek()
        if tok.type == TokenType.CLICK:
            self._advance()
            return WaitStmt(is_click=True)
        elif tok.type == TokenType.NUMBER:
            self._advance()
            return WaitStmt(duration=tok.value)
        else:
            raise QFSyntaxError(f"期望数字或 click", tok.line, tok.col, self.filename)

    def _parse_python(self) -> PythonBlockStmt:
        self._expect(TokenType.PYTHON)
        self._expect(TokenType.COLON)
        self._consume_block_tokens()
        lines = []
        while self._peek().type != TokenType.END:
            t = self._advance()
            if t.type == TokenType.NEWLINE:
                lines.append("\n")
            else:
                lines.append(str(t.value) if t.value else t.type.name)
        self._expect(TokenType.END)
        return PythonBlockStmt(code="".join(lines))

    def _parse_python_code(self) -> PythonBlockStmt:
        tok = self._expect(TokenType.PYTHON_CODE)
        self._consume_block_tokens()
        if self._peek().type == TokenType.END:
            self._advance()
        return PythonBlockStmt(code=tok.value)

    def _parse_expression(self) -> Expr:
        return self._parse_or()

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._peek().type == TokenType.OR:
            self._advance()
            right = self._parse_and()
            left = BinOpExpr(left=left, operator="or", right=right)
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_comparison()
        while self._peek().type == TokenType.AND:
            self._advance()
            right = self._parse_comparison()
            left = BinOpExpr(left=left, operator="and", right=right)
        return left

    def _parse_comparison(self) -> Expr:
        left = self._parse_additive()
        while self._peek().type in (TokenType.EQUAL, TokenType.NOT_EQUAL,
                                     TokenType.LESS, TokenType.GREATER,
                                     TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL):
            op_tok = self._advance()
            right = self._parse_additive()
            left = BinOpExpr(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_additive(self) -> Expr:
        left = self._parse_multiplicative()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._advance()
            right = self._parse_multiplicative()
            left = BinOpExpr(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_multiplicative(self) -> Expr:
        left = self._parse_power()
        while self._peek().type in (TokenType.MULTIPLY, TokenType.DIVIDE,
                                     TokenType.INT_DIVIDE, TokenType.MODULO):
            op_tok = self._advance()
            right = self._parse_power()
            left = BinOpExpr(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_power(self) -> Expr:
        base = self._parse_unary()
        if self._peek().type == TokenType.POWER:
            self._advance()
            exp = self._parse_power()
            return BinOpExpr(left=base, operator="**", right=exp)
        return base

    def _parse_unary(self) -> Expr:
        if self._peek().type == TokenType.NOT:
            op_tok = self._advance()
            operand = self._parse_unary()
            return UnaryOpExpr(operator="not", operand=operand)
        if self._peek().type == TokenType.MINUS:
            self._advance()
            operand = self._parse_unary()
            return UnaryOpExpr(operator="-", operand=operand)
        return self._parse_primary()

    def _parse_primary(self) -> Expr:
        tok = self._peek()

        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberExpr(value=tok.value)

        if tok.type == TokenType.STRING:
            self._advance()
            return StringExpr(value=tok.value)

        if tok.type == TokenType.TRUE:
            self._advance()
            return BoolExpr(value=True)

        if tok.type == TokenType.FALSE:
            self._advance()
            return BoolExpr(value=False)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return VarExpr(name=tok.value)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise QFSyntaxError(f"期望表达式，得到 {tok.type.name} ({tok.value!r})", tok.line, tok.col, self.filename)

    def parse(self) -> Program:
        return self._parse_program()
