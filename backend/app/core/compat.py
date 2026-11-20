"""
Compatibility layer for Pydantic and FastAPI.
Allows the codebase and test suite to run in isolated/offline environments
even before external pip packages are installed, while seamlessly utilizing
full Pydantic and FastAPI when installed.
"""

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field, ValidationError
    BaseModel = _PydanticBaseModel
except ImportError:
    class ValidationError(Exception):
        """Validation error fallback."""
        pass

    class _FieldInfo:
        def __init__(self, default=..., default_factory=None, **kwargs):
            self.default = default
            self.default_factory = default_factory
            self.kwargs = kwargs

    def Field(default=..., default_factory=None, **kwargs):
        return _FieldInfo(default, default_factory, **kwargs)

    class BaseModel:
        def __init__(self, **kwargs):
            # Check class annotations and defaults
            annotations = getattr(self.__class__, "__annotations__", {})
            for key, val_type in annotations.items():
                default_val = getattr(self.__class__, key, None)
                if isinstance(default_val, _FieldInfo):
                    if key in kwargs:
                        val = kwargs[key]
                    elif default_val.default_factory is not None:
                        val = default_val.default_factory()
                    elif default_val.default is not ...:
                        val = default_val.default
                    else:
                        raise ValidationError(f"Missing required field: '{key}'")
                elif key in kwargs:
                    val = kwargs[key]
                elif hasattr(self.__class__, key):
                    val = getattr(self.__class__, key)
                else:
                    raise ValidationError(f"Missing required field: '{key}'")
                
                # Check min_length if specified
                if isinstance(default_val, _FieldInfo) and "min_length" in default_val.kwargs:
                    min_len = default_val.kwargs["min_length"]
                    if len(val) < min_len:
                        raise ValidationError(f"Field '{key}' must have min length {min_len}")
                        
                setattr(self, key, val)

            for k, v in kwargs.items():
                if not hasattr(self, k):
                    setattr(self, k, v)

        def dict(self):
            return {
                k: v for k, v in self.__dict__.items()
                if not k.startswith("_")
            }

        def model_dump(self):
            return self.dict()

        def __repr__(self):
            fields = ", ".join(f"{k}={v!r}" for k, v in self.dict().items())
            return f"{self.__class__.__name__}({fields})"


try:
    from fastapi import FastAPI, APIRouter, HTTPException, status, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"HTTP {status_code}: {detail}")

    class status:
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_500_INTERNAL_SERVER_ERROR = 500

    class APIRouter:
        def __init__(self, *args, **kwargs):
            self.routes = []

        def post(self, *args, **kwargs):
            def decorator(fn):
                self.routes.append(("POST", args, kwargs, fn))
                return fn
            return decorator

        def get(self, *args, **kwargs):
            def decorator(fn):
                self.routes.append(("GET", args, kwargs, fn))
                return fn
            return decorator

        def delete(self, *args, **kwargs):
            def decorator(fn):
                self.routes.append(("DELETE", args, kwargs, fn))
                return fn
            return decorator

    class FastAPI:
        def __init__(self, *args, **kwargs):
            self.routes = []

        def include_router(self, router, *args, **kwargs):
            self.routes.extend(router.routes)

        def add_middleware(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

        def exception_handler(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    class CORSMiddleware:
        pass

    class JSONResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code

    class UploadFile:
        def __init__(self, filename="unknown", file=None):
            self.filename = filename
            self.file = file

    def File(*args, **kwargs):
        return None
