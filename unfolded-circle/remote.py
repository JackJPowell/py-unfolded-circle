import aiohttp
import copy
import logging
import socket
import time
from urllib.parse import urljoin, urlparse
import zeroconf

ZEROCONF_TIMEOUT = 3
ZEROCONF_SERVICE_TYPE = "_uc-remote._tcp.local."

AUTH_APIKEY_NAME = "pyUnfoldedCircle"
AUTH_USERNAME = "web-configurator"


class HTTPError(Exception):
    """Raised when an HTTP operation fails."""

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class AuthenticationError(Exception):
    """Raised when HTTP login fails."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EmitterNotFound(Exception):
    """Raised when IR emitter with a given name can't be found.

    Attributes:
        name -- name of emitter that wasn't found
        message -- explanation of the error
    """

    def __init__(self, name, message="Emitter not found on device"):
        self.name = name
        self.message = message
        super().__init__(self.message)


class CodesetNotFound(Exception):
    """Raised when IR codeset with a given name can't be found.

    Attributes:
        name -- IR target name that wasn't found
        message -- explanation of the error
    """

    def __init__(self, name, message="IR target name not found in codesets"):
        self.name = name
        self.message = message
        super().__init__(self.message)


class CommandNotFound(Exception):
    """Raised when IR command with a given name can't be found.

    Attributes:
        name -- IR command name that wasn't found
        message -- explanation of the error
    """

    def __init__(self, name, message="IR command not found in codesets"):
        self.name = name
        self.message = message
        super().__init__(self.message)


class ApiKeyNotFound(Exception):
    """Raised when API Key with given name can't be found.

    Attributes:
        name -- Name of the API Key
        message -- explanation of the error
    """

    def __init__(self, name, message="API key name not found"):
        self.name = name
        self.message = message
        super().__init__(self.message)


class ucRemote:
    def __init__(self, pin, host, api_key: str = "") -> None:
        self.token = api_key
        self.host = host
        self.pin = pin
        self.activities = []
        self.model_name = ""
        self.model_number = ""
        self.serial_number = ""
        self.hw_revision = ""
        self.manufacturer = "Unfolded Circle"
        self.battery_level = 0
        self.battery_status = ""
        self.is_charging = bool
        self.ambient_light_intensity = 0
        self.update_in_progress = False
        self.next_update_check_date = ""
        self.sw_version = ""
        self.automatic_updates = bool
        self.available_update = []
        self.online = True

    @property
    def name(self):
        return self._name or "N/A"

    @property
    def fw_version(self):
        return self._fw_version or "N/A"

    @property
    def model_name(self):
        return self._model_name or "N/A"

    @property
    def model_number(self):
        return self._model_number or "N/A"

    @property
    def serial_number(self):
        return self._serial_number or "N/A"

    async def retrieve_activities(self):
        endpoint = self.host + "/api/activities?page=1&limit=10"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=2) as response:
                currentActivities = await response.json()
                for activity in currentActivities:
                    self.activities.append(Activity(activity=activity, remote=self))

    async def authenticate(self) -> bool:
        auth = aiohttp.BasicAuth(AUTH_USERNAME, self.pin)
        endpoint = self.host + "/api/activities"
        headers = {
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.head(
                endpoint, headers=headers, timeout=2, auth=auth
            ) as response:
                return response.status == 200

    async def get_api_key(self) -> str:
        if self.token == "":
            auth = aiohttp.BasicAuth(AUTH_USERNAME, self.pin)
            body = {"name": AUTH_APIKEY_NAME, "scopes": ["admin"]}
            endpoint = self.host + "/api/auth/api_keys"
            headers = {
                "Accept": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, headers=headers, timeout=2, auth=auth, json=body
                ) as response:
                    api_info = await response.json()
                    self.token = api_info["api_key"]
        return self.token

    async def get_remote_information(self) -> bool:
        endpoint = self.host + "/api/system"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                self.model_name = information["model_name"]
                self.model_number = information["model_number"]
                self.serial_number = information["serial_number"]
                self.hw_revision = information["hw_revision"]
                return response.status == 200

    async def get_remote_battery_information(self) -> bool:
        endpoint = self.host + "/api/system/power/battery"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                self.battery_level = information["capacity"]
                self.battery_status = information["status"]
                self.is_charging = information["power_supply"]
                return response.status == 200

    async def get_remote_ambient_light_information(self) -> bool:
        endpoint = self.host + "/api/system/sensors/ambient_light"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                self.ambient_light_intensity = information["intensity"]
                return response.status == 200

    async def get_remote_update_information(self) -> bool:
        endpoint = self.host + "/api/system/update"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                self.update_in_progress = information["update_in_progress"]
                self.next_update_check_date = information["next_check_date"]
                self.sw_version = information["installed_version"]
                self.automatic_updates = information["update_check_enabled"]
                if "available" in information.keys():
                    self.available_update = information["available"]
                return response.status == 200

    async def get_remote_force_update_information(self) -> bool:
        endpoint = self.host + "/api/system/update"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                self.update_in_progress = information["update_in_progress"]
                self.next_update_check_date = information["next_check_date"]
                self.sw_version = information["installed_version"]
                self.automatic_updates = information["update_check_enabled"]
                if "available" in information.keys():
                    self.available_update = information["available"]
                return response.status == 200

    async def update_remote(self) -> bool:
        endpoint = self.host + "/api/system/update/latest"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, timeout=2) as response:
                information = await response.json()
                return response.status == 200

    async def get_activity_state(self, entity_id) -> str:
        endpoint = self.host + "/api/activities?page=1&limit=10"
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers, timeout=10) as response:
                currentActivities = await response.json()
                for currentActivity in currentActivities:
                    if entity_id == currentActivity["entity_id"]:
                        return currentActivity["attributes"]["state"]

    async def update(self):
        await self.get_remote_battery_information()
        await self.get_remote_ambient_light_information()
        await self.get_remote_update_information()


class Activity:
    def __init__(self, activity: str, remote: ucRemote) -> None:
        self.name = activity["name"]["en"]
        self._id = activity["entity_id"]
        self.remote = remote
        self.state = "OFF"

    async def turn_on(self) -> None:
        endpoint = self.remote.host + "/api/entities/" + self._id + "/command"
        body = {"entity_id": self._id, "cmd_id": "activity.on"}
        headers = {
            "Authorization": "Bearer " + self.remote.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(
                endpoint, headers=headers, timeout=10, json=body
            ) as response:
                self.state = "ON"
                return response.status == 200

    async def turn_off(self) -> None:
        endpoint = self.remote.host + "/api/entities/" + self._id + "/command"
        body = {"entity_id": self._id, "cmd_id": "activity.off"}
        headers = {
            "Authorization": "Bearer " + self.remote.token,
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(
                endpoint, headers=headers, timeout=10, body=body
            ) as response:
                self.state = "OFF"
                return response.status == 200

    def is_on(self) -> bool:
        return self.state == "ON"

    async def update(self) -> None:
        self.state = await self.remote.get_activity_state(self._id)
        await self.remote.update()
