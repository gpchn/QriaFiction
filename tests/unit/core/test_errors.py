import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from core.errors import LexerError, QFSyntaxError, QFRuntimeError, QriaFictionError


class TestErrorHierarchy:
    """测试错误类层次结构"""

    def test_lexer_error_is_qf_error(self):
        err = LexerError("test", 1, 1, "file.qf")
        assert isinstance(err, QriaFictionError)

    def test_syntax_error_is_qf_error(self):
        err = QFSyntaxError("test", 1, 1, "file.qf")
        assert isinstance(err, QriaFictionError)

    def test_runtime_error_is_qf_error(self):
        err = QFRuntimeError("test")
        assert isinstance(err, QriaFictionError)


class TestLexerError:
    """测试词法错误"""

    def test_basic(self):
        err = LexerError("test error", 5, 10, "file.qf")
        assert err.message == "test error"
        assert err.line == 5
        assert err.col == 10
        assert err.filename == "file.qf"

    def test_str_representation(self):
        err = LexerError("invalid char", 3, 7, "test.qf")
        str_repr = str(err)
        assert "invalid char" in str_repr
        assert "3" in str_repr
        assert "7" in str_repr

    def test_default_filename(self):
        err = LexerError("error", 1, 1)
        assert err.filename is None


class TestSyntaxError:
    """测试语法错误"""

    def test_basic(self):
        err = QFSyntaxError("expected colon", 10, 5, "script.qf")
        assert err.message == "expected colon"
        assert err.line == 10
        assert err.col == 5

    def test_str(self):
        err = QFSyntaxError("missing end", 15, 3, "test.qf")
        str_repr = str(err)
        assert "missing end" in str_repr
        assert "15" in str_repr


class TestRuntimeError:
    """测试运行时错误"""

    def test_basic(self):
        err = QFRuntimeError("unknown label")
        assert err.message == "unknown label"

    def test_str(self):
        err = QFRuntimeError("division by zero")
        assert str(err) == "unknown label" or "division by zero" in str(err)
