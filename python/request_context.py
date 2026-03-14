from contextvars import ContextVar

from fastapi import Request

_request_var: ContextVar[Request] = ContextVar("current_request")


def set_request(req: Request) -> None:
    _request_var.set(req)


def get_request() -> Request:
    return _request_var.get()
