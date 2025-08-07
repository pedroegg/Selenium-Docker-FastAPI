from __future__ import annotations

import logging
logger = logging.getLogger("Proxy")

import os
from contextlib import AbstractContextManager
from typing import Dict, Any, Final

from browsermobproxy import Server, Client

_BROWSERMOB_PATH: Final[str | None] = os.getenv("BROWSERMOB_PATH")
if not _BROWSERMOB_PATH:
	raise RuntimeError("BROWSERMOB_PATH env var must be set")

_BROWSERMOB_PORT = int(os.getenv('BROWSERMOB_PORT', '9090'))

__all__ = ["ProxyServer", "ProxyClient", "get_proxy_server"]

# Singleton instance
_proxy_server: ProxyServer | None = None

def get_proxy_server() -> ProxyServer | None:
	global _proxy_server
	return _proxy_server

class ProxyServer:
	_server: Server | None

	def __init__(self) -> None:
		self._server = Server(_BROWSERMOB_PATH, options={"port": _BROWSERMOB_PORT})
		self._server.start()

		global _proxy_server
		_proxy_server = self

		logger.info("BrowserMob Proxy server started.")

	def new_client(self) -> ProxyClient:
		if not self._server:
			raise RuntimeError('Proxy server not initialized or closed')

		return ProxyClient(self._server.create_proxy())

	def __exit__(self, exc_type, exc, tb) -> bool:
		self.close()
		return False

	def __del__(self) -> None:
		self.close()

	def close(self) -> None:
		global _proxy_server

		if self._server:
			try:
				self._server.stop()
				logger.info("BrowserMob Proxy server stopped.")

			except Exception as e:
				logger.error(f"Failed to stop BrowserMob Proxy server: {e}")

			finally:
				self._server = None
				_proxy_server = None

class ProxyClient(AbstractContextManager):
	_client: Client | None

	def __init__(self, client: Client) -> None:
		self._client = client

	@property
	def client(self) -> Client:
		if not self._client:
			raise RuntimeError('Proxy client not initialized or closed')
		
		return self._client

	def get_address(self) -> str:
		return self.client.proxy

	def add_headers(self, headers: Dict[str, Any]) -> None:
		self.client.headers(headers)

	def __exit__(self, exc_type, exc, tb) -> bool:
		self.close()
		return False

	def __del__(self) -> None:
		self.close()

	def close(self) -> None:
		if self._client:
			try:
				self._client.close()

			except Exception as e:
				logger.error(f"Failed to stop BrowserMob Proxy client: {e}")

			finally:
				self._client = None
