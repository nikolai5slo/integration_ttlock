"""Sample API Client."""
from hashlib import md5
import logging
import aiohttp
import async_timeout
import time
from urllib.parse import urljoin, urlencode

TIMEOUT = 20

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class TTLockApiClient:
    """TTLock API Client"""

    def __init__(
        self,
        server_url: str,
        client_id: str,
        client_secret: str,
        username: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._server_url = server_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._username = username
        self._session = session
        self._access_token = None
        self._refresh_token = None
        self._on_refresh_token_callback = lambda _: None

    def on_new_refresh_token(self, callback: callable):
        """set refresh token callback"""
        self._on_refresh_token_callback = callback

    async def async_authenticate(self, secret: str, typ: str) -> dict:
        """Authenticate with password or refresh token."""

        data = {
            "clientId": self._client_id,
            "clientSecret": self._client_secret,
            "username": self._username,
        }

        if typ == "password":
            data["password"] = md5(secret.encode()).hexdigest()
        if typ == "refresh_token":
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = secret

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = await self._api_wrapper(
            "post", "/oauth2/token", data=data, headers=headers
        )

        if "refresh_token" in response:
            self._refresh_token = response["refresh_token"]
            self._on_refresh_token_callback(self._refresh_token)

        if "access_token" in response:
            self._access_token = response["access_token"]

        return response

    async def _auth_wrapper(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> dict:
        """Wrap api call with authentication"""

        if data is None:
            data = {}
        data["clientId"] = self._client_id
        data["accessToken"] = self._access_token

        response = await self._api_wrapper(method, url, data, headers)

        # Check if token is invalid
        if "errcode" in response and response["errcode"] == 10003:
            # Get new token
            auth_response = await self.async_authenticate(
                self._refresh_token, "refresh_token"
            )
            if "access_token" in auth_response:
                # Update this request tokens
                data["clientId"] = self._client_id
                data["accessToken"] = self._access_token

                # Retry request
                response = self._api_wrapper(method, url, data, headers)
            else:
                raise PermissionError("cannot refresh token")

        return response

    async def _api_wrapper(
        self, method: str, url: str, data: dict = None, headers: dict = None
    ) -> dict:
        """Get information from the API."""
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = urljoin(self._server_url, url)

        async with async_timeout.timeout(TIMEOUT):
            if method == "get":
                url = url + "?" + urlencode(data)
                response = await self._session.get(url, headers=headers)

                return await response.json()

            elif method == "put":
                response = await self._session.put(url, headers=headers, json=data)
                return await response.json()

            elif method == "patch":
                response = await self._session.patch(url, headers=headers, json=data)
                return await response.json()

            elif method == "post":
                if headers["Content-Type"] == "application/x-www-form-urlencoded":
                    response = await self._session.post(url, headers=headers, data=data)
                else:
                    response = await self._session.post(url, headers=headers, json=data)
                return await response.json()

    async def list_lock(self):
        """This API will return all the locks  related to a gateway."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        params = {"pageNo": 1, "pageSize": 1000, "date": int(time.time_ns() / 1000000)}
        response = await self._auth_wrapper(
            "get", "/v3/lock/list", data=params, headers=headers
        )

        if "errcode" in response and response["errcode"] != 0:
            raise TTLockError(response["errcode"], response["errmsg"])

        return response["list"]

    async def query_open_state(self, lock_id):
        """Get the open state of a lock via gateway or WiFi lock."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        params = {"lockId": lock_id, "date": int(time.time_ns() / 1000000)}
        response = await self._auth_wrapper(
            "get", "/v3/lock/queryOpenState", data=params, headers=headers
        )

        if "errcode" in response and response["errcode"] != 0:
            raise TTLockError(response["errcode"], response["errmsg"])

        return response

    async def list_lock_record(self, lock_id):
        """Get the open state of a lock via gateway or WiFi lock."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        params = {
            "lockId": lock_id,
            "date": int(time.time_ns() / 1000000),
            "pageSize": 100,
            "pageNo": 1,
        }
        response = await self._auth_wrapper(
            "get", "/v3/lockRecord/list", data=params, headers=headers
        )

        if "errcode" in response and response["errcode"] != 0:
            raise TTLockError(response["errcode"], response["errmsg"])

        return response["list"]

    async def lock_lock(
        self,
        lock_id: str,
    ):
        """Lock the lock remotely via gateway or WiFi lock."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"lockId": lock_id, "date": int(time.time_ns() / 1000000)}
        response = await self._auth_wrapper(
            "post", "/v3/lock/lock", data=data, headers=headers
        )

        if "errcode" in response and response["errcode"] != 0:
            raise TTLockError(response["errcode"], response["errmsg"])

        return response

    async def lock_unlock(
        self,
        lock_id: str,
    ):
        """Unlock the lock remotely via gateway or WiFi lock."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"lockId": lock_id, "date": int(time.time_ns() / 1000000)}
        response = await self._auth_wrapper(
            "post", "/v3/lock/unlock", data=data, headers=headers
        )

        if "errcode" in response and response["errcode"] != 0:
            raise TTLockError(response["errcode"], response["errmsg"])

        return response


class TTLockError(Exception):
    """Represents TTLock API error"""

    def __init__(self, code, message="TTLock error"):
        self.code = code
        self.message = message
        super().__init__(self.message)
