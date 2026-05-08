class QriaFictionError(Exception):
    def __init__(self, message: str, line: int = None, col: int = None, filename: str = None):
        self.message = message
        self.line = line
        self.col = col
        self.filename = filename
        parts = []
        if filename:
            parts.append(filename)
        if line is not None:
            parts.append(f"行{line}")
            if col is not None:
                parts.append(f"列{col}")
        loc = ":".join(parts) if parts else None
        if loc:
            super().__init__(f"[{loc}] {message}")
        else:
            super().__init__(message)


class LexerError(QriaFictionError):
    pass


class QFSyntaxError(QriaFictionError):
    pass


class SemanticError(QriaFictionError):
    pass


class QFRuntimeError(QriaFictionError):
    pass
