from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class AppLogger:
    def __init__(self):
        self._log_path = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    def _log(self, level: str, message: str):
        line = f"[{datetime.now().isoformat()}] [{level.upper()}] {message}"
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass

    def debug(self, message: str):
        self._log("debug", message)

    def info(self, message: str):
        self._log("info", message)

    def warn(self, message: str):
        self._log("warn", message)

    def error(self, message: str):
        self._log("error", message)

    def get_logs(self, limit: int = 200) -> list:
        if not self._log_path.exists():
            return []
        lines = self._log_path.read_text(encoding="utf-8").strip().split("\n")
        return lines[-limit:]


app_logger = AppLogger()
