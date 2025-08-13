"""Utilities to work with a headless Chrome driver.

Provides the `HeadlessChrome` context-manager class that:
• applies sane default options for container runtimes;
• automatically waits for pages to be fully loaded (JS included);
• guarantees `driver.quit()` is called even when exceptions occur;
• logs errors on teardown when a logger is provided.
"""

from __future__ import annotations

import logging
logger = logging.getLogger("Selenium utils")

import os
import time
from contextlib import AbstractContextManager
from abc import abstractmethod
from typing import List, Dict, Any, Tuple, Callable, Union, Final

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from library.proxy_utils import get_proxy_server, ProxyClient

__all__ = ["HeadlessChrome"]

_DEFAULT_TIMEOUT = int(os.getenv("PAGELOAD_TIMEOUT", "15"))

_CHROME_BIN: Final[str | None] = os.getenv("CHROME_BIN")
_CHROMEDRIVER_PATH: Final[str | None] = os.getenv("CHROMEDRIVER_PATH")

if not _CHROME_BIN:
	raise RuntimeError("CHROME_BIN env var must be set")

if not _CHROMEDRIVER_PATH:
	raise RuntimeError("CHROMEDRIVER_PATH env var must be set")

class SeleniumBrowser(AbstractContextManager):
	"""Selenium Chrome driver with auto-cleanup and helper methods."""

	def __init__(
			self,
			headers: Dict[str, Any] | None = None,
			cookies: List[Dict[str, str]] | None = None,
			timeout: float | None = None
		) -> None:

		self._proxy: ProxyClient | None = None
		self._timeout = timeout or _DEFAULT_TIMEOUT
		self._headers = headers
		self._cookies = cookies

		self._driver: Union[webdriver.Chrome, uc.Chrome, None] = self._create_driver()

	@abstractmethod
	def _create_driver(self) -> Union[webdriver.Chrome, uc.Chrome]:
		"""Create and return a configured Selenium Chrome driver."""
		pass
	
	@property
	def driver(self) -> WebDriver:
		if not self._driver:
			raise RuntimeError('WebDriver not initialized or closed')
		
		return self._driver

	def __exit__(self, exc_type, exc, tb):
		self.close()
		return False

	def __del__(self):
		self.close()

	def close(self):
		if self._proxy:
			try:
				self._proxy.close()
			
			except Exception as e:
				logger.error(f'Failed to close proxy connection: {e}')
			
			finally:
				self._proxy = None
		
		if self._driver:
			try:
				self._driver.quit()

			except WebDriverException as exc:
				logger.error("Error during driver.quit(): %s", exc, exc_info=True)

			finally:
				self._driver = None

	def get(self, url: str) -> None:
		"""Navigate to *url* and wait until the document is fully loaded."""

		self.driver.get(url)
		if self._cookies and len(self._cookies) > 0:
			for cookie in self._cookies:
				self.driver.add_cookie(cookie)
			
			self.driver.get(url)

		self._wait_until_page_ready(self._timeout)

	def screenshot_png(self) -> bytes:
		"""Return a PNG screenshot of the current page."""
		return self.driver.get_screenshot_as_png()

	def html(self) -> str:
		"""Return the current page HTML source after load."""
		return self.driver.page_source

	def _wait_until_page_ready(self, timeout: float | None) -> None:
		"""Block until document.readyState == 'complete' or timeout."""

		if timeout is None:
			timeout = float(self._timeout)

		logger.info(f'Waiting for page to be ready for a maximum of {timeout} seconds')

		start = time.monotonic()
		deadline = start + timeout
		def remaining():
			return max(0.0, deadline - time.monotonic())

		steps: List[Tuple[str, Callable]] = [
			('readyState', lambda: wait_ready_event(self.driver, remaining())),
			('loadEventEnd', lambda: wait_lazyload(self.driver, remaining())),
			('network idle', lambda: wait_network_idle(self.driver, remaining())),
			('DOM quiet', lambda: wait_dom_quiet(self.driver, remaining())),
			('next paint', lambda: wait_animation_frame(self.driver, remaining())),
		]

		try:
			for name, wait_fn in steps:
				rem = remaining()
				if rem <= 0:
					raise TimeoutException(f'Timeout before step "{name}"')

				wait_fn()

			logger.info("Page is ready")

		except TimeoutException:
			logger.error("Page load timeout after %s seconds", timeout)
			raise

		except Exception as e:
			logger.error(f"Error waiting for page to be ready: {e}")
			raise

class HeadlessChrome(SeleniumBrowser):
	def _create_driver(self) -> webdriver.Chrome:
		"""Create and return a configured headless Chrome driver."""

		args = [
			"--headless=new",
			"--no-sandbox",
			"--disable-gpu",
			"--disable-dev-shm-usage",
			"--window-size=1920,1080",
		]

		options = Options()
		for arg in args:
			options.add_argument(arg)

		if self._headers:
			proxy_server = get_proxy_server()
			if not proxy_server:
				raise Exception('proxy server not available')

			self._proxy = proxy_server.new_client()
			self._proxy.add_headers(self._headers)

			logger.info(f'Using proxy "{self._proxy.get_address()}"')
			options.add_argument(f'--proxy-server={self._proxy.get_address()}')
			options.add_argument('--ignore-certificate-errors')
			options.add_argument('--allow-insecure-localhost')
			options.add_argument("--proxy-bypass-list=<-loopback>")
			options.set_capability("acceptInsecureCerts", True)

		options.binary_location = _CHROME_BIN
		service = Service(executable_path=_CHROMEDRIVER_PATH)

		return webdriver.Chrome(service=service, options=options)

class StealthChrome(SeleniumBrowser):
	def _create_driver(self) -> uc.Chrome:
		"""Create and return a configured stealth Chrome driver."""

		args = [
			"--no-sandbox",
			"--disable-gpu",
			"--disable-dev-shm-usage",
			"--window-size=1920,1080",
			"--disable-popup-blocking",
			"--lang=pt-BR",
		]

		options = uc.ChromeOptions()
		for a in args:
			options.add_argument(a)

		if self._headers:
			proxy_server = get_proxy_server()
			if not proxy_server:
				raise Exception('proxy server not available')

			self._proxy = proxy_server.new_client()
			self._proxy.add_headers(self._headers)

			logger.info(f'Using proxy "{self._proxy.get_address()}"')
			options.add_argument(f'--proxy-server={self._proxy.get_address()}')
			options.add_argument('--ignore-certificate-errors')
			options.add_argument('--allow-insecure-localhost')
			options.add_argument("--proxy-bypass-list=<-loopback>")
			options.set_capability("acceptInsecureCerts", True)

		driver = uc.Chrome(
			headless=True,
			options=options,
			use_subprocess=True,
			driver_executable_path=_CHROMEDRIVER_PATH,
			browser_executable_path=_CHROME_BIN,
		)

		stealth_js = r"""
			Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
			window.chrome = window.chrome || { runtime: {} };
			Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR','pt','en-US','en'] });
			Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
			Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });

			(function() {
				const guard = (url) => (typeof url === 'string' && url.startsWith('data:'));
				const origAssign = window.location.assign.bind(window.location);
				const origReplace = window.location.replace.bind(window.location);
				window.location.assign = new Proxy(origAssign, { apply(t, thisArg, args){ if (guard(String(args[0]))) return; return t.apply(thisArg, args); } });
				window.location.replace = new Proxy(origReplace, { apply(t, thisArg, args){ if (guard(String(args[0]))) return; return t.apply(thisArg, args); } });
				const origOpen = window.open?.bind(window);
				if (origOpen) {
					window.open = new Proxy(origOpen, { apply(t, thisArg, args){ if (guard(String(args[0]||''))) return null; return t.apply(thisArg, args); } });
				}
			})();
		"""

		user_agent, accept_language = None, None
		if self._headers:
			user_agent = self._headers.get("User-Agent", None)
			accept_language = self._headers.get("Accept-Language", None)

		cdp_override_args = {
			"userAgent": user_agent or driver.execute_script("return navigator.userAgent"),
			"acceptLanguage": accept_language or "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
		}

		if not user_agent:
			cdp_override_args["platform"] = "Linux x86_64"

		driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
		driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Sao_Paulo"})
		driver.execute_cdp_cmd("Network.enable", {})
		driver.execute_cdp_cmd("Network.setUserAgentOverride", cdp_override_args)

		return driver

def wait_ready_event(driver: WebDriver, timeout: float):
	WebDriverWait(driver, timeout).until(
		lambda d: d.execute_script("return document.readyState") == "complete"
	)

def wait_lazyload(driver: WebDriver, timeout: float):
	WebDriverWait(driver, timeout).until(
		lambda d: d.execute_script(
			"const n = performance.getEntriesByType('navigation')[0];"
			"return !!n && n.loadEventEnd > 0;"
		)
	)

def wait_network_idle(driver: WebDriver, timeout: float, idle_ms: int = 600):
	start_deadline = time.monotonic() + timeout
	def remaining():
		return max(0.0, start_deadline - time.monotonic())

	driver.execute_script(r"""
		if (!window.__netHooked) {
			window.__netHooked = true;
			window.__inflight = 0;

			const origFetch = window.fetch;
			window.fetch = function() {
				window.__inflight++;
				return origFetch.apply(this, arguments)
			.finally(() => { window.__inflight--; });
		};

		const send = XMLHttpRequest.prototype.send;
		XMLHttpRequest.prototype.send = new Proxy(send, {
			apply(target, thisArg, args) {
				window.__inflight++;
				thisArg.addEventListener('loadend', () => { window.__inflight--; }, {once:true});
				return Reflect.apply(target, thisArg, args);
			}
			});
		}

		return window.__inflight || 0;
	"""
	)

	WebDriverWait(driver, remaining()).until(
		lambda d: d.execute_script("return window.__inflight || 0") == 0
	)

	quiet_start = None
	idle_s = idle_ms / 1000.0
	def stop_condition(d: WebDriver) -> bool:
		nonlocal quiet_start

		inflight = d.execute_script("return window.__inflight || 0")
		now = time.monotonic()
		if inflight == 0:
			if quiet_start is None:
				quiet_start = now

			return (now - quiet_start) >= idle_s

		quiet_start = None
		return False

	WebDriverWait(driver, timeout, poll_frequency=0.05).until(stop_condition)

def wait_dom_quiet(driver: WebDriver, timeout: float, idle_ms: int = 400):
	js = """
		if (!window.__mutObs) {
			window.__lastMut = performance.now();
			window.__mutObs = new MutationObserver(() => { window.__lastMut = performance.now(); });
			window.__mutObs.observe(document, { subtree: true, childList: true, attributes: true, characterData: true });
		}

		return performance.now() - window.__lastMut;
	"""

	WebDriverWait(driver, timeout, poll_frequency=0.05).until(
		lambda d: d.execute_script(js) >= idle_ms
	)

def wait_animation_frame(driver: WebDriver, timeout: float):
	driver.set_script_timeout(timeout)
	driver.execute_async_script(
		"const done = arguments[arguments.length - 1];"
		"requestAnimationFrame(()=>requestAnimationFrame(()=>done()));"
	)
