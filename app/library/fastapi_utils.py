"""FastAPI helpers.

• APIRouter – thin wrapper around ``fastapi.APIRouter`` that automatically
  registers exception handlers for the project-specific ``BaseError`` hierarchy so you don’t need to repeat them for every router/app.
"""

from __future__ import annotations
from logging import Logger

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from library.errors import BaseError, InternalError, BadRequest

class ErrorHandler:
	def __init__(self, logger: Logger | None = None) -> None:
		self._logger = logger

	def base_error_handler(self, _: Request, exc: BaseError) -> JSONResponse:
		return JSONResponse(status_code=exc.code, content=exc.to_dict())

	def validation_error_handler(self, request: Request, exc: ValidationError | RequestValidationError) -> JSONResponse:
		detail = exc.errors()
		return self.base_error_handler(request, BadRequest(detail))

	def generic_error_handler(self, request: Request, exc: Exception) -> JSONResponse:
		if self._logger:
			self._logger.error(exc, exc_info=True)

		return self.base_error_handler(request, InternalError(str(exc)))
