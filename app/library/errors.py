from __future__ import annotations

from http import HTTPStatus
from typing import Final, ClassVar

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

	code: ClassVar[int]
	name: ClassVar[str]

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
	code: ClassVar[int] = HTTPStatus.INTERNAL_SERVER_ERROR
	name: ClassVar[str] = "INTERNAL_ERROR"

class BadRequest(BaseError):
	code: ClassVar[int] = HTTPStatus.BAD_REQUEST
	name: ClassVar[str] = "BAD_REQUEST"

class UnprocessableEntity(BaseError):
	code: ClassVar[int] = HTTPStatus.UNPROCESSABLE_ENTITY
	name: ClassVar[str] = "UNPROCESSABLE_ENTITY"

class NotFound(BaseError):
	code: ClassVar[int] = HTTPStatus.NOT_FOUND
	name: ClassVar[str] = "NOT_FOUND"

class Conflict(BaseError):
	code: ClassVar[int] = HTTPStatus.CONFLICT
	name: ClassVar[str] = "CONFLICT"

class Unauthorized(BaseError):
	code: ClassVar[int] = HTTPStatus.UNAUTHORIZED
	name: ClassVar[str] = "UNAUTHORIZED"

class Forbidden(BaseError):
	code: ClassVar[int] = HTTPStatus.FORBIDDEN
	name: ClassVar[str] = "FORBIDDEN"

class TooManyRequests(BaseError):
	code: ClassVar[int] = HTTPStatus.TOO_MANY_REQUESTS
	name: ClassVar[str] = "TOO_MANY_REQUESTS"
