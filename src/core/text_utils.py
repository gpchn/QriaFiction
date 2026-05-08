import re
from typing import Callable, Any, Optional


_SAFE_BUILTINS = {
    "abs": abs, "bool": bool, "int": int, "float": float,
    "str": str, "len": len, "list": list, "dict": dict,
    "tuple": tuple, "set": set, "range": range, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter, "sorted": sorted,
    "min": min, "max": max, "sum": sum, "round": round,
    "repr": repr, "type": type, "isinstance": isinstance,
    "join": lambda sep, items: sep.join(str(i) for i in items),
    "true": True, "false": False, "null": None,
}


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
            safe_scope = dict(scope)
            safe_scope["__builtins__"] = _SAFE_BUILTINS
            try:
                return str(eval(code, safe_scope))
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
    if log_func:
        original_get_var = get_var_func

        def logging_get_var(var_name: str):
            val = original_get_var(var_name)
            log_func("D", "interp", f"{{{var_name}}} -> {val!r}")
            return val

        get_var_func = logging_get_var

    return interpolate_text(text, get_var_func, python_scope, qf_ctx)
