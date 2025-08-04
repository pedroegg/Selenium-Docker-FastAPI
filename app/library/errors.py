from __future__ import annotations

from http import HTTPStatus
from typing import Final

__all__ = [
	"BaseError",
	"InternalError",
	"BadRequest",
	"UnprocessableEntity",
	"NotFound",
	"Conflict",
	"Unauthorized",
	"Forbidden",
	"TooManyRequests",
]

class BaseError(Exception):
	"""Base class for domain/business errors mapped to HTTP responses."""

	code: Final[int] = HTTPStatus.INTERNAL_SERVER_ERROR
	name: Final[str] = "BASE_ERROR"

	def __init__(self, description: str) -> None:
		self.description = description
		super().__init__(description)

	def to_dict(self) -> dict[str, str | int]:
		return {
			"code": self.code,
			"name": self.name,
			"description": self.description,
		}

	def __str__(self) -> str:
		return f"{self.name}({self.code}): {self.description}"

class InternalError(BaseError):
	code: Final[int] = HTTPStatus.INTERNAL_SERVER_ERROR
	name: Final[str] = "INTERNAL_ERROR"

class BadRequest(BaseError):
	code: Final[int] = HTTPStatus.BAD_REQUEST
	name: Final[str] = "BAD_REQUEST"

class UnprocessableEntity(BaseError):
	code: Final[int] = HTTPStatus.UNPROCESSABLE_ENTITY
	name: Final[str] = "UNPROCESSABLE_ENTITY"

class NotFound(BaseError):
	code: Final[int] = HTTPStatus.NOT_FOUND
	name: Final[str] = "NOT_FOUND"

class Conflict(BaseError):
	code: Final[int] = HTTPStatus.CONFLICT
	name: Final[str] = "CONFLICT"

class Unauthorized(BaseError):
	code: Final[int] = HTTPStatus.UNAUTHORIZED
	name: Final[str] = "UNAUTHORIZED"

class Forbidden(BaseError):
	code: Final[int] = HTTPStatus.FORBIDDEN
	name: Final[str] = "FORBIDDEN"

class TooManyRequests(BaseError):
	code: Final[int] = HTTPStatus.TOO_MANY_REQUESTS
	name: Final[str] = "TOO_MANY_REQUESTS"
