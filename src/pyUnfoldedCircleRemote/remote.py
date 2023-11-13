import socket
import time
import copy
from urllib.parse import urljoin, urlparse
import aiohttp
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


class UCRemoteGroup(list):
    """List of Unfolded Circle Remotes"""

    def __init__(self, *args):
        super(UCRemoteGroup, self).__init__(args[0])


class UCRemote:
    """Unfolded Circle Remote Class"""

    def __init__(self, api_url, pin=None, apikey=None) -> None:
        self.endpoint = self.validate_url(api_url)
        self.apikey = apikey
        self.pin = pin
        self.activities = []
        self._name = ""
        self._model_name = ""
        self._model_number = ""
        self._serial_number = ""
        self._hw_revision = ""
        self._manufacturer = "Unfolded Circle"
        self._battery_level = 0
        self._battery_status = ""
        self._is_charging = bool
        self._ambient_light_intensity = 0
        self._update_in_progress = False
        self._next_update_check_date = ""
        self._sw_version = ""
        self._automatic_updates = bool
        self._available_update = []
        self._latest_sw_version = ""
        self._release_notes_url = ""
        self._online = True

    @property
    def name(self):
        """Name of the remote"""
        return self._name or "Unfolded Circle Remote Two"

    @property
    def sw_version(self):
        """Software Version"""
        return self._sw_version or "N/A"

    @property
    def model_name(self):
        """Model Name"""
        return self._model_name or "Remote Two"

    @property
    def model_number(self):
        """Model Number"""
        return self._model_number or "N/A"

    @property
    def serial_number(self):
        """Represents UC Remote Serial Number"""
        return self._serial_number or "N/A"

    @property
    def online(self):
        """Remote online state"""
        return self._online

    @property
    def is_charging(self):
        """Is Remote charging"""
        return self._is_charging

    @property
    def battery_level(self):
        """Integer percent of battery level remaining"""
        return self._battery_level

    @property
    def ambient_light_intensity(self):
        """Integer of lux"""
        return self._ambient_light_intensity

    @property
    def manufacturer(self):
        """Remote Manufacturer"""
        return self._manufacturer

    @property
    def hw_revision(self):
        """Remote Hardware Revision"""
        return self._hw_revision

    @property
    def battery_status(self):
        """Remote Battery Charging Status"""
        return self._battery_status

    @property
    def update_in_progress(self):
        """Remote Update is in progress"""
        return self._update_in_progress

    @property
    def next_update_check_date(self):
        """Remote Next Update Check Date"""
        return self._next_update_check_date

    @property
    def automatic_updates(self):
        """Does remote have automatic updates turned on"""
        return self._automatic_updates

    @property
    def available_update(self):
        """List of available updates"""
        return self._available_update

    @property
    def latest_sw_version(self):
        """Latest software release version"""
        return self._latest_sw_version

    @property
    def release_notes_url(self):
        """Release notes url"""
        return self._release_notes_url

    def validate_url(self, uri):
        """Validates passed in URL and attempts to correct api endpoint if path isn't supplied"""
        parsed_url = urlparse(uri)
        if parsed_url.scheme not in ["http", "https"]:
            raise ValueError(f"Endpoint {uri} should begin with http or https")
        if parsed_url.path == "/":  # Only host supplied
            uri = uri + "api/"
            return uri
        if parsed_url.path == "":
            uri = uri + "/api/"
            return uri
        if (
            parsed_url.path[-1] != "/"
        ):  # User supplied an endpoint, make sure it has a trailing slash
            uri = uri + "/"
        return uri

    async def raise_on_error(self, response):
        """Raise an HTTP error if the response returns poorly"""
        if not response.ok:
            content = await response.json()
            msg = f"{response.status} Request: {content['code']} Reason: {content['message']}"
            raise HTTPError(response.status, msg)
        return response

    def url(self, path="/") -> str:
        """Method to join path with base url"""
        return urljoin(self.endpoint, path)

    def client(self) -> aiohttp.ClientSession:
        """Creates a aiohttp client object with needed headers and defaults"""
        if self.apikey:
            headers = {
                "Authorization": "Bearer " + self.apikey,
                "Accept": "application/json",
            }
            return aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=5)
            )
        if self.pin:
            auth = aiohttp.BasicAuth(AUTH_USERNAME, self.pin)
            return aiohttp.ClientSession(
                auth=auth, timeout=aiohttp.ClientTimeout(total=2)
            )

    async def get_activities(self):
        """Returns activities from UC Remote"""
        async with self.client() as session:
            async with session.get(self.url("activities?page=1&limit=10")) as response:
                await self.raise_on_error(response)
                for activity in await response.json():
                    self.activities.append(Activity(activity=activity, remote=self))
                return await response.json()

    async def can_connect(self) -> bool:
        """Validates we can communicate with the remote given the supplied information"""
        async with self.client() as session:
            async with session.head(self.url("activities")) as response:
                return response.status == 200

    async def get_api_keys(self) -> str:
        """Gets all api Keys"""
        async with self.client() as session:
            async with session.get(
                self.url("auth/api_keys"),
            ) as response:
                await self.raise_on_error(response)
                return await response.json()

    async def create_api_key(self) -> str:
        """Creates api Key"""
        body = {"name": AUTH_APIKEY_NAME, "scopes": ["admin"]}

        async with self.client() as session:
            async with session.post(self.url("auth/api_keys"), json=body) as response:
                await self.raise_on_error(response)
                api_info = await response.json()
                self.apikey = api_info["api_key"]
        return self.apikey

    async def revoke_api_key(self, key_name=AUTH_APIKEY_NAME):
        """Revokes api Key"""
        for key in await self.get_api_keys():
            if key["name"] == key_name:
                api_key_id = key["key_id"]
                break
        else:
            msg = f"API Key '{key_name}' not found."
            raise ApiKeyNotFound(key_name, msg)

        async with self.client() as session:
            async with session.delete(
                self.url("auth/api_keys/" + api_key_id)
            ) as response:
                await self.raise_on_error(response)

    async def get_remote_information(self) -> str:
        """Get System information from remote"""
        async with self.client() as session:
            async with session.get(self.url("system")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._model_name = information["model_name"]
                self._model_number = information["model_number"]
                self._serial_number = information["serial_number"]
                self._hw_revision = information["hw_revision"]
                return information

    async def get_remote_configuration(self) -> str:
        """Get System configuration from remote"""
        async with self.client() as session:
            async with session.get(self.url("cfg")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._name = information.get("device").get("name")
                return information

    async def get_remote_battery_information(self) -> str:
        """Get Battery information from remote"""
        async with self.client() as session:
            async with session.get(self.url("system/power/battery")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._battery_level = information["capacity"]
                self._battery_status = information["status"]
                self._is_charging = information["power_supply"]
                return information

    async def get_remote_ambient_light_information(self) -> int:
        """Get Remote Ambient Light Level"""
        async with self.client() as session:
            async with session.get(
                self.url("system/sensors/ambient_light")
            ) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._ambient_light_intensity = information["intensity"]
                return self._ambient_light_intensity

    async def get_remote_update_information(self) -> bool:
        """Get remote update information"""
        async with self.client() as session:
            async with session.get(self.url("system/update")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._update_in_progress = information["update_in_progress"]
                self._next_update_check_date = information["next_check_date"]
                self._sw_version = information["installed_version"]
                self._automatic_updates = information["update_check_enabled"]
                if "available" in information.keys():
                    self._available_update = information["available"]
                    for update in self._available_update:
                        if update.get("channel") == "STABLE":
                            if (
                                self._latest_sw_version == ""
                                or self._latest_sw_version < update.get("version")
                            ):
                                self._release_notes_url = update.get(
                                    "release_notes_url"
                                )
                                self._latest_sw_version = update.get("version")
                else:
                    self._latest_sw_version = self._sw_version
                return information

    async def get_remote_force_update_information(self) -> bool:
        """Force a remote firmware update check"""
        async with self.client() as session:
            async with session.put(self.url("system/update")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                self._update_in_progress = information["update_in_progress"]
                self._next_update_check_date = information["next_check_date"]
                self._sw_version = information["installed_version"]
                self._automatic_updates = information["update_check_enabled"]
                if "available" in information.keys():
                    self._available_update = information["available"]
                return information

    async def update_remote(self) -> str:
        "WIP: Starts the latest firmware update"
        async with self.client() as session:
            async with session.post(self.url("system/update/latest")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                return information

    async def get_update_status(self) -> str:
        "WIP: Gets Update Status -- Only supports latest"
        async with self.client() as session:
            async with session.get(self.url("system/update/latest")) as response:
                await self.raise_on_error(response)
                information = await response.json()
                return information

    async def get_activity_state(self, entity_id) -> str:
        """Get activity state for a remote entity"""
        async with self.client() as session:
            async with session.get(self.url("activities?page=1&limit=10")) as response:
                await self.raise_on_error(response)
                current_activities = await response.json()
                for current_activity in current_activities:
                    if entity_id == current_activity["entity_id"]:
                        return current_activity["attributes"]["state"]

    async def update(self):
        """Retrivies all information about the remote"""
        await self.get_remote_battery_information()
        await self.get_remote_ambient_light_information()
        await self.get_remote_update_information()
        await self.get_remote_configuration()
        await self.get_remote_information()


class Activity:
    """Class representing a Unfolded Circle Remote Activity"""

    def __init__(self, activity: str, remote: UCRemote) -> None:
        self._name = activity["name"]["en"]
        self._id = activity["entity_id"]
        self._remote = remote
        self._state = activity.get("attributes").get("state")

    @property
    def name(self):
        """Name of the Activity"""
        return self._name

    @property
    def id(self):
        """ID of the Activity"""
        return self._id

    @property
    def state(self):
        """State of the Activity"""
        return self._state

    @property
    def remote(self):
        """Remote Object"""
        return self._remote

    async def turn_on(self) -> None:
        """Turn on an Activity"""
        body = {"entity_id": self._id, "cmd_id": "activity.on"}

        async with self._remote.client() as session:
            async with session.put(
                self._remote.url("entities/" + self._id + "/command"), json=body
            ) as response:
                await self._remote.raise_on_error(response)
                self._state = "ON"

    async def turn_off(self) -> None:
        """Turn off an Activity"""
        body = {"entity_id": self._id, "cmd_id": "activity.off"}

        async with self._remote.client() as session:
            async with session.put(
                self._remote.url("entities/" + self._id + "/command"), json=body
            ) as response:
                await self._remote.raise_on_error(response)
                self._state = "OFF"

    def is_on(self) -> bool:
        """Is Activity Running"""
        return self._state == "ON"

    async def update(self) -> None:
        """Updates activity state information"""
        self._state = await self._remote.get_activity_state(self._id)
        # await self._remote.update()


def discover_devices(apikey):
    """Zero Conf class"""

    class DeviceListener:
        """Zeroconf Device Listener"""

        def __init__(self):
            self.apikey = apikey
            self.devices = []

        def add_service(self, zconf, type_, name):
            """Called by zeroconf when something is found"""
            info = zconf.get_service_info(type_, name)
            host = socket.inet_ntoa(info.addresses[0])
            endpoint = f"http://{host}:{info.port}/api/"
            self.devices.append(UCRemote(endpoint, self.apikey))

        def update_service(self, zconf, type_, name):
            """Nothing"""

        def remove_service(self, zconf, type_, name):
            """Nothing"""

    zconf = zeroconf.Zeroconf(interfaces=zeroconf.InterfaceChoice.Default)
    listener = DeviceListener()
    zeroconf.ServiceBrowser(zconf, ZEROCONF_SERVICE_TYPE, listener)
    try:
        time.sleep(ZEROCONF_TIMEOUT)
    finally:
        zconf.close()
    return UCRemoteGroup(copy.deepcopy(listener.devices))
