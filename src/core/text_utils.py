import re
from typing import Callable, Any, Optional


def interpolate_text(
    text: str,
    get_var_func: Callable[[str], Optional[Any]],
    python_scope: Optional[dict] = None,
    qf_ctx: Any = None,
) -> str:
    def replacer(match):
        var_name = match.group(1).strip()

        if var_name.startswith("python:"):
            code = var_name[len("python:"):].strip()
            scope = {"qf": qf_ctx}
            if python_scope:
                scope.update(python_scope)
            try:
                return str(eval(code, scope))
            except Exception:
                return match.group(0)

        val = get_var_func(var_name)
        return str(val) if val is not None else ""

    return re.sub(r"\{([^}]+)\}", replacer, text)


def interpolate_text_with_logging(
    text: str,
    get_var_func: Callable[[str], Optional[Any]],
    python_scope: Optional[dict] = None,
    qf_ctx: Any = None,
    log_func: Optional[Callable] = None,
) -> str:
    def replacer(match):
        var_name = match.group(1).strip()

        if var_name.startswith("python:"):
            code = var_name[len("python:"):].strip()
            scope = {"qf": qf_ctx}
            if python_scope:
                scope.update(python_scope)
            try:
                return str(eval(code, scope))
            except Exception:
                return match.group(0)

        val = get_var_func(var_name)
        if log_func:
            log_func("D", "interp", f"{{{var_name}}} -> {val!r}")
        return str(val) if val is not None else ""

    return re.sub(r"\{([^}]+)\}", replacer, text)
