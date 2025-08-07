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

	def base(self, req: Request, exc: Exception) -> JSONResponse:
		if not isinstance(exc, BaseError):
			return self.generic(req, exc)

		return JSONResponse(status_code=exc.code, content=exc.to_dict())

	def validation(self, req: Request, exc: Exception) -> JSONResponse:
		if not isinstance(exc, (ValidationError, RequestValidationError)):
			return self.generic(req, exc)
		
		detail = str(exc.errors())
		return self.base(req, BadRequest(detail))

	def generic(self, req: Request, exc: Exception) -> JSONResponse:
		if self._logger:
			self._logger.error(f'request for "{req.url}" failed with a unexpected error: {exc}', exc_info=True)

		return self.base(req, InternalError(str(exc)))
