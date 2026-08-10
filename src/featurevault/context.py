import contextlib
from contextvars import ContextVar
from typing import Any, Generator

_FEATURE_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar(
    "_FEATURE_CONTEXT", default=None
)


def get_current_context() -> dict[str, Any]:
    """Returns the current thread/task context or an empty dict if unset."""
    ctx = _FEATURE_CONTEXT.get()
    return ctx.copy() if ctx is not None else {}


def set_current_context(context: dict[str, Any]) -> None:
    """Sets the current thread/task context dictionary."""
    _FEATURE_CONTEXT.set(context)


def clear_current_context() -> None:
    """Resets the context to None."""
    _FEATURE_CONTEXT.set(None)


@contextlib.contextmanager
def context(**kwargs: Any) -> Generator[None, None, None]:
    """
    Context manager for background tasks, Celery workers, or unit tests.
    
    Usage:
        with feature.context(user_id="user_101", is_staff=True):
            if feature.is_enabled("BG_FLAG"):
                ...
    """
    previous_ctx = _FEATURE_CONTEXT.get()
    new_ctx = (previous_ctx.copy() if previous_ctx else {})
    new_ctx.update(kwargs)
    
    token = _FEATURE_CONTEXT.set(new_ctx)
    try:
        yield
    finally:
        _FEATURE_CONTEXT.reset(token)