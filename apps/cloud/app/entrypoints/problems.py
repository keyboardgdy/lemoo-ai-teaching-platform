"""RFC 9457 responses with stable codes and request correlation."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ProblemException(Exception):
    def __init__(
        self,
        *,
        status: int,
        code: str,
        title: str,
        detail: str,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = str(request.state.request_id)
    content: dict[str, Any] = {
        "type": f"https://errors.lemoo.invalid/{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        "request_id": request_id,
    }
    if errors is not None:
        content["errors"] = errors
    return JSONResponse(
        status_code=status,
        content=content,
        media_type="application/problem+json",
    )


async def problem_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    if not isinstance(exception, ProblemException):
        raise exception
    return problem_response(
        request,
        status=exception.status,
        code=exception.code,
        title=exception.title,
        detail=exception.detail,
    )


async def validation_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    if not isinstance(exception, RequestValidationError):
        raise exception
    errors = [
        {
            "location": [str(part) for part in error["loc"]],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exception.errors()
    ]
    return problem_response(
        request,
        status=422,
        code="request_validation_failed",
        title="Request validation failed",
        detail="The request does not match the Stage 1A API contract.",
        errors=errors,
    )
