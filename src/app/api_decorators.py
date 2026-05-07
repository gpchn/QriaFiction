import json
from functools import wraps


class ApiError(Exception):
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


def api_method(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
            return {"success": True, "data": result, "error": None}
        except ApiError as e:
            return {"success": False, "data": e.data, "error": {"code": e.code, "message": e.message}}
        except Exception as e:
            return {"success": False, "data": None, "error": {"code": 500, "message": str(e)}}
    return wrapper
