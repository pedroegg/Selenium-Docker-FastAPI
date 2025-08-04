"""Endpoints that interact with a headless browser via Selenium."""

from __future__ import annotations
import logging
logger = logging.getLogger("Browser router")

import io
from typing import Optional, Dict, Any, Annotated

from fastapi import APIRouter, Query, Body
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from selenium.common.exceptions import TimeoutException

from library.selenium_utils import HeadlessChrome, StealthChrome
from library.errors import InternalError

class BrowserInput(BaseModel):
	url: str = Field(alias='url', description='Target URL')
	stealth_mode: bool = Field(default=False, alias='stealth', description='Activate this option to use the Stealth mode browser')
	timeout: Optional[float] = Field(default=None, alias='timeout', description='Maximum time in seconds to wait for page to load and return')
	headers: Optional[Dict[str, Any]] = Field(default=None, alias='headers', description='Headers to use')
	cookies: Optional[Dict[str, str]] = Field(default=None, alias='cookies', description='Cookies to use')

router = APIRouter(prefix="/browser", tags=["browser"])

@router.get("/screenshot", response_class=StreamingResponse, summary="Return a PNG screenshot of the page")
def screenshot(url: str = Query(alias='url', description="Target URL")):
	logger.info(f"called screenshot: {url}")

	browser = HeadlessChrome()

	try:
		with browser:
			browser.get(url)
			png = browser.screenshot_png()

	except TimeoutException:
		raise InternalError(f'Page took too much time to load')

	except:
		raise

	return StreamingResponse(io.BytesIO(png), media_type="image/png")

@router.post("/html", response_class=HTMLResponse, summary="Return the fully rendered HTML of the page")
def html(data: Annotated[BrowserInput, Body(default_factory=BrowserInput)]):

	if data.stealth_mode:
		browser = StealthChrome(data.headers, data.cookies, data.timeout)
	else:
		browser = HeadlessChrome(data.headers, data.cookies, data.timeout)

	try:
		with browser:
			browser.get(data.url)
			html_source = browser.html()

	except TimeoutException:
		raise InternalError(f'Page took too much time to load')

	except:
		raise

	return html_source
