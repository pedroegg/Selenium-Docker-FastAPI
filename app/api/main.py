"""Application entry-point.

Exposes the FastAPI instance called **app** so that ASGI servers such as
*uvicorn* or *gunicorn* can import it directly.
"""

import os
from dotenv import load_dotenv
load_dotenv('.env')

if os.getenv('ENV') == 'development':
	import shutil
	from webdriver_manager.chrome import ChromeDriverManager

	chrome_path = (
		shutil.which("google-chrome") or
		shutil.which("google-chrome-stable") or
		shutil.which("chromium") or
		shutil.which("chromium-browser")
	)

	if not chrome_path:
		raise RuntimeError('Chrome/Chromium not found in system.')

	chromedriver_path = ChromeDriverManager().install()
	os.environ['CHROME_BIN'] = chrome_path
	os.environ['CHROMEDRIVER_PATH'] = chromedriver_path

import logging
logging.basicConfig(level=int(os.getenv('LOG_LEVEL')), force=True)
logger = logging.getLogger('API')

import atexit
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger.info('intializing...')

from library.fastapi_utils import ErrorHandler
from library.proxy_utils import ProxyServer
from library.errors import BaseError
from api.routers import browser_router

app = FastAPI(
	title=os.getenv("API_TITLE"),
	version=os.getenv("API_VERSION"),
)

error_handler = ErrorHandler(logger)
app.add_exception_handler(BaseError, error_handler.base_error_handler)
app.add_exception_handler(ValidationError, error_handler.validation_error_handler)
app.add_exception_handler(RequestValidationError, error_handler.validation_error_handler)
app.add_exception_handler(Exception, error_handler.generic_error_handler)

origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["GET"],
)

proxy_server = ProxyServer()
atexit.register(proxy_server.close)

app.include_router(browser_router)

logger.info('ready!')
