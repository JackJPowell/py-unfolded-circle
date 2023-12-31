"""Module to interact with the Unfolded Circle Remote Two."""
import asyncio
import copy
import re
import socket
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
import zeroconf

ZEROCONF_TIMEOUT = 3
ZEROCONF_SERVICE_TYPE = "_uc-remote._tcp.local."

SYSTEM_COMMANDS = [
    "STANDBY",
    "REBOOT",
    "POWER_OFF",
    "RESTART",
    "RESTART_UI",
    "RESTART_CORE",
]


class HTTPError(Exception):
    """Raised when an HTTP operation fails."""

    def __init__(self, status_code, message) -> None:
        """Raise HTTP Error."""
        self.status_code = status_code
        self.message = message
        super().__init__(self.message, self.status_code)


class AuthenticationError(Exception):
    """Raised when HTTP login fails."""

    def __init__(self, message) -> None:
        """Raise Auth http error."""
        self.message = message
        super().__init__(self.message)


class SystemCommandNotFound(Exception):
    """Raised when an invalid system command is supplied."""

    def __init__(self, message) -> None:
        """Raise command no found error."""
        self.message = message
        super().__init__(self.message)


class InvalidIRFormat(Exception):
    """Raised when invalid or insufficient IR details are passed."""

    def __init__(self, message) -> None:
        """Raise invalid IR format error."""
        self.message = message
        super().__init__(self.message)


class NoEmitterFound(Exception):
    """Raised when no emitter could be identified from criteria given."""

    def __init__(self, message) -> None:
        """Raise invalid emitter error."""
        self.message = message
        super().__init__(self.message)


class ApiKeyNotFound(Exception):
    """Raised when API Key with given name can't be found.

    Attributes:
        name -- Name of the API Key
        message -- explanation of the error
    """

    def __init__(self, name, message="API key name not found") -> None:
        """Raise API key not found."""
        self.name = name
        self.message = message
        super().__init__(self.message)


class RemoteGroup(list):
    """List of Unfolded Circle Remotes."""

    def __init__(self, *args) -> None:
        """Create list of UC Remotes."""
        super().__init__(args[0])


class Remote:
    """Unfolded Circle Remote Class."""
    AUTH_APIKEY_NAME = "pyUnfoldedCircle"
    AUTH_USERNAME = "web-configurator"
    

    def __init__(self, api_url, pin=None, apikey=None) -> None:
        """Create a new UC Remote Object."""
        self.endpoint = self.validate_url(api_url)
        self.configuration_url = self.derive_configuration_url()
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
        self._memory_total = 0
        self._memory_available = 0
        self._storage_total = 0
        self._storage_available = 0
        self._cpu_load = {}
        self._cpu_load_one = 0.0
        self._remotes = []
        self._docks = []
        self._ir_custom = []
        self._ir_codesets = []

    @property
    def name(self):
        """Name of the remote."""
        return self._name or "Unfolded Circle Remote Two"

    @property
    def memory_available(self):
        """Percentage of Memory used on the remote."""
        return int(round(self._memory_available, 0))

    @property
    def storage_available(self):
        """Percentage of Storage used on the remote."""
        return int(round(self._storage_available, 0))

    @property
    def sw_version(self):
        """Software Version."""
        return self._sw_version or "N/A"

    @property
    def model_name(self):
        """Model Name."""
        return self._model_name or "Remote Two"

    @property
    def model_number(self):
        """Model Number."""
        return self._model_number or "N/A"

    @property
    def serial_number(self):
        """Represents UC Remote Serial Number."""
        return self._serial_number or "N/A"

    @property
    def online(self):
        """Remote online state."""
        return self._online

    @property
    def is_charging(self):
        """Is Remote charging."""
        return self._is_charging

    @property
    def battery_level(self):
        """Integer percent of battery level remaining."""
        return self._battery_level

    @property
    def ambient_light_intensity(self):
        """Integer of lux."""
        return self._ambient_light_intensity

    @property
    def manufacturer(self):
        """Remote Manufacturer."""
        return self._manufacturer

    @property
    def hw_revision(self):
        """Remote Hardware Revision."""
        if self._hw_revision == "rev2":
            return "Revision 2"
        else:
            return self._hw_revision

    @property
    def battery_status(self):
        """Remote Battery Charging Status."""
        return self._battery_status

    @property
    def update_in_progress(self):
        """Remote Update is in progress."""
        return self._update_in_progress

    @property
    def next_update_check_date(self):
        """Remote Next Update Check Date."""
        return self._next_update_check_date

    @property
    def automatic_updates(self):
        """Does remote have automatic updates turned on."""
        return self._automatic_updates

    @property
    def available_update(self):
        """List of available updates."""
        return self._available_update

    @property
    def latest_sw_version(self):
        """Latest software release version."""
        return self._latest_sw_version

    @property
    def release_notes_url(self):
        """Release notes url."""
        return self._release_notes_url

    @property
    def cpu_load(self):
        """CPU Load."""
        return self._cpu_load

    @property
    def cpu_load_one(self):
        """CPU Load 1 minute."""
        return self._cpu_load_one

    ### URL Helpers ###
    def validate_url(self, uri):
        """Validate passed in URL and attempts to correct api endpoint if path isn't supplied."""
        if re.search("^http.*", uri) is None:
            uri = (
                "http://" + uri
            )  # Normalize to absolute URLs so urlparse will parse the way we want
        parsed_url = urlparse(uri)
        # valdation = set(uri)
        if parsed_url.scheme == "":
            uri = "http://" + uri
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

    def derive_configuration_url(self) -> str:
        """Derive configuration url from endpoint url."""
        parsed_url = urlparse(self.endpoint)
        self.configuration_url = (
            f"{parsed_url.scheme}://{parsed_url.netloc}/configurator/"
        )
        return self.configuration_url

    def url(self, path="/") -> str:
        """Join path with base url."""
        return urljoin(self.endpoint, path)

    ### HTTP methods ###
    def client(self) -> aiohttp.ClientSession:
        """Create a aiohttp client object with needed headers and defaults."""
        if self.apikey:
            headers = {
                "Authorization": "Bearer " + self.apikey,
                "Accept": "application/json",
            }
            return aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=5)
            )
        if self.pin:
            auth = aiohttp.BasicAuth(self.AUTH_USERNAME, self.pin)
            return aiohttp.ClientSession(
                auth=auth, timeout=aiohttp.ClientTimeout(total=2)
            )

    async def can_connect(self) -> bool:
        """Validate we can communicate with the remote given the supplied information."""
        async with self.client() as session, session.head(
            self.url("activities")
        ) as response:
            return response.status == 200

    async def raise_on_error(self, response):
        """Raise an HTTP error if the response returns poorly."""
        if not response.ok:
            content = await response.json()
            msg = f"{response.status} Request: {content['code']} Reason: {content['message']}"
            raise HTTPError(response.status, msg)
        return response

    ### Unfolded Circle API Keys ###
    async def get_api_keys(self) -> str:
        """Get all api Keys."""
        async with self.client() as session, session.get(
            self.url("auth/api_keys"),
        ) as response:
            await self.raise_on_error(response)
            return await response.json()

    async def create_api_key(self) -> str:
        """Create api Key."""
        body = {"name": self.AUTH_APIKEY_NAME, "scopes": ["admin"]}

        async with self.client() as session, session.post(
            self.url("auth/api_keys"), json=body
        ) as response:
            await self.raise_on_error(response)
            api_info = await response.json()
            self.apikey = api_info["api_key"]
        return self.apikey

    async def revoke_api_key(self, key_name=AUTH_APIKEY_NAME):
        """Revokes api Key."""
        for key in await self.get_api_keys():
            if key["name"] == key_name:
                api_key_id = key["key_id"]
                break
        else:
            msg = f"API Key '{key_name}' not found."
            raise ApiKeyNotFound(key_name, msg)

        async with self.client() as session, session.delete(
            self.url("auth/api_keys/" + api_key_id)
        ) as response:
            await self.raise_on_error(response)

    async def get_remote_information(self) -> str:
        """Get System information from remote. model_name, model_number, serial_number, hw_revision."""
        async with self.client() as session, session.get(
            self.url("system")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._model_name = information.get("model_name")
            self._model_number = information.get("model_number")
            self._serial_number = information.get("serial_number")
            self._hw_revision = information.get("hw_revision")
            return information

    async def get_remote_configuration(self) -> str:
        """Get System configuration from remote. User supplied remote name."""
        async with self.client() as session, session.get(self.url("cfg")) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._name = information.get("device").get("name")
            return information

    async def get_activities(self):
        """Return activities from Unfolded Circle Remote."""
        async with self.client() as session, session.get(
            self.url("activities")
        ) as response:
            await self.raise_on_error(response)
            for activity in await response.json():
                self.activities.append(Activity(activity=activity, remote=self))
            return await response.json()

    async def get_remote_battery_information(self) -> str:
        """Get Battery information from remote. battery_level, battery_status, is_charging."""
        async with self.client() as session, session.get(
            self.url("system/power/battery")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._battery_level = information["capacity"]
            self._battery_status = information["status"]
            self._is_charging = information["power_supply"]
            return information

    async def get_stats(self) -> str:
        """Get usage stats from the remote."""
        async with self.client() as session, session.get(
            self.url("pub/status")
        ) as response:
            await self.raise_on_error(response)
            status = await response.json()
            self._memory_total = status.get("memory").get("total_memory") / 1048576
            self._memory_available = (
                status.get("memory").get("available_memory") / 1048576
            )

            self._storage_total = (
                status.get("filesystem").get("user_data").get("used")
                + status.get("filesystem").get("user_data").get("available") / 1048576
            )
            self._storage_available = (
                status.get("filesystem").get("user_data").get("available") / 1048576
            )

            self._cpu_load = status.get("load_avg")
            self._cpu_load_one = status.get("load_avg").get("one")

    async def get_remote_ambient_light_information(self) -> int:
        """Get Remote Ambient Light Level. ambient_light_intensity."""
        async with self.client() as session, session.get(
            self.url("system/sensors/ambient_light")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._ambient_light_intensity = information["intensity"]
            return self._ambient_light_intensity

    async def get_remote_update_information(self) -> bool:
        """Get remote update information."""
        async with self.client() as session, session.get(
            self.url("system/update")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._update_in_progress = information["update_in_progress"]
            self._next_update_check_date = information["next_check_date"]
            self._sw_version = information["installed_version"]
            self._automatic_updates = information["update_check_enabled"]
            if "available" in information:
                self._available_update = information["available"]
                for update in self._available_update:
                    if update.get("channel") in ["STABLE", "TESTING"]:
                        if (
                            self._latest_sw_version == ""
                            or self._latest_sw_version < update.get("version")
                        ):
                            self._release_notes_url = update.get("release_notes_url")
                            self._latest_sw_version = update.get("version")
                    else:
                        self._latest_sw_version = self._sw_version
            else:
                self._latest_sw_version = self._sw_version
            return information

    async def get_remote_force_update_information(self) -> bool:
        """Force a remote firmware update check."""
        async with self.client() as session, session.put(
            self.url("system/update")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            self._update_in_progress = information["update_in_progress"]
            self._next_update_check_date = information["next_check_date"]
            self._sw_version = information["installed_version"]
            self._automatic_updates = information["update_check_enabled"]
            if "available" in information:
                self._available_update = information["available"]
            return information

    async def update_remote(self) -> str:
        """Update Remote."""
        # WIP: Starts the latest firmware update."
        async with self.client() as session, session.post(
            self.url("system/update/latest")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            return information

    async def get_update_status(self) -> str:
        """Update remote status."""
        # WIP: Gets Update Status -- Only supports latest."
        async with self.client() as session, session.get(
            self.url("system/update/latest")
        ) as response:
            await self.raise_on_error(response)
            information = await response.json()
            return information

    async def get_activity_state(self, entity_id) -> str:
        """Get activity state for a remote entity."""
        async with self.client() as session, session.get(
            self.url("activities")
        ) as response:
            await self.raise_on_error(response)
            current_activities = await response.json()
            for current_activity in current_activities:
                if entity_id == current_activity["entity_id"]:
                    return current_activity["attributes"]["state"]

    async def post_system_command(self, cmd) -> str:
        """POST a system command to the remote."""
        if cmd in SYSTEM_COMMANDS:
            async with self.client() as session, session.post(
                self.url("system?cmd=" + cmd)
            ) as response:
                await self.raise_on_error(response)
                response = await response.json()
                return response
        else:
            raise SystemCommandNotFound("Invalid System Command Supplied")

    async def get_remotes(self) -> []:
        """Get list of remotes defined. (IR Remotes as defined by Unfolded Circle)."""
        remote_data = {}
        async with self.client() as session, session.get(
            self.url("remotes")
        ) as response:
            await self.raise_on_error(response)
            remotes = await response.json()
            for remote in remotes:
                if remote.get("enabled") is True:
                    remote_data = {
                        "name": remote.get("name").get("en"),
                        "entity_id": remote.get("entity_id"),
                    }
                    self._remotes.append(remote_data.copy())
            return self._remotes

    async def get_custom_codesets(self) -> []:
        """Get list of IR code sets defined."""
        ir_data = {}
        async with self.client() as session, session.get(
            self.url("ir/codes/custom")
        ) as response:
            await self.raise_on_error(response)
            code_sets = await response.json()
            for ir in code_sets:
                ir_data = {
                    "device": ir.get("device"),
                    "device_id": ir.get("device_id"),
                }
                self._ir_custom.append(ir_data.copy())
            return self._ir_custom

    async def get_remote_codesets(self) -> []:
        """Get list of remote codesets."""
        ir_data = {}
        for remote in self._remotes:
            async with self.client() as session, session.get(
                self.url("remotes/" + remote.get("entity_id") + "/ir")
            ) as response:
                await self.raise_on_error(response)
                code_set = await response.json()
                ir_data = {
                    "name": remote.get("name"),
                    "device_id": code_set.get("id"),
                }
                self._ir_codesets.append(ir_data.copy())
        return self._ir_codesets

    async def get_docks(self) -> []:
        """Get list of docks defined."""
        dock_data = {}
        async with self.client() as session, session.get(
            self.url("ir/emitters")
        ) as response:
            await self.raise_on_error(response)
            docks = await response.json()
            for dock in docks:
                if dock.get("active") is True:
                    dock_data = {
                        "name": dock.get("name"),
                        "device_id": dock.get("device_id"),
                    }
                    self._docks.append(dock_data.copy())
            return self._docks

    async def send_remote_command(
        self, device="", command="", repeat=0, **kwargs
    ) -> bool:
        """Send a remote command to the dock kwargs: code,format,dock,port."""
        body_port = {}
        body_repeat = {}
        if "code" in kwargs and "format" in kwargs:
            # Send an IR command (HEX/PRONTO)
            body = {"code": kwargs.get("code"), "format": kwargs.get("format")}
        if device != "" and command != "":
            # Send a predefined code
            ir_code = next(
                (code for code in self._ir_codesets if code.get("name") == device),
                dict,
            )
            body = {"codeset_id": ir_code.get("device_id"), "cmd_id": command}
        else:
            raise InvalidIRFormat("Supply (code and format) or (device and command)")

        if repeat > 0:
            body_repeat = {"repeat": repeat}

        if "port" in kwargs:
            body_port = {"port_id": kwargs.get("port")}

        if "dock" in kwargs:
            dock_name = kwargs.get("dock")
            emitter = next(
                (dock for dock in self._docks if dock.get("name") == dock_name), None
            )
        else:
            emitter = self._docks[0].get("device_id")

        if emitter is None:
            raise NoEmitterFound("No emitter could be found with the supplied criteria")

        body_merged = {**body, **body_repeat, **body_port}

        async with self.client() as session, session.put(
            self.url("ir/emitters/" + emitter + "/send"), json=body_merged
        ) as response:
            await self.raise_on_error(response)
            response = await response.json()
            return response == 200

    async def update(self) -> dict[str, Any]:
        """Retrivies all information about the remote."""
        group = asyncio.gather(
            self.get_remote_battery_information(),
            self.get_remote_ambient_light_information(),
            self.get_remote_update_information(),
            self.get_remote_configuration(),
            self.get_remote_information(),
            self.get_stats(),
        )
        await group

        for activity in self.activities:
            await activity.update()

class Activity:
    """Class representing a Unfolded Circle Remote Activity."""

    def __init__(self, activity: str, remote: Remote) -> None:
        """Create activity."""
        self._name = activity["name"]["en"]
        self._id = activity["entity_id"]
        self._remote = remote
        self._state = activity.get("attributes").get("state")

    @property
    def name(self):
        """Name of the Activity."""
        return self._name

    @property
    def id(self):
        """ID of the Activity."""
        return self._id

    @property
    def state(self):
        """State of the Activity."""
        return self._state

    @property
    def remote(self):
        """Remote Object."""
        return self._remote

    async def turn_on(self) -> None:
        """Turn on an Activity."""
        body = {"entity_id": self._id, "cmd_id": "activity.on"}

        async with self._remote.client() as session, session.put(
            self._remote.url("entities/" + self._id + "/command"), json=body
        ) as response:
            await self._remote.raise_on_error(response)
            self._state = "ON"

    async def turn_off(self) -> None:
        """Turn off an Activity."""
        body = {"entity_id": self._id, "cmd_id": "activity.off"}

        async with self._remote.client() as session, session.put(
            self._remote.url("entities/" + self._id + "/command"), json=body
        ) as response:
            await self._remote.raise_on_error(response)
            self._state = "OFF"

    def is_on(self) -> bool:
        """Is Activity Running."""
        return self._state == "ON"

    async def update(self) -> None:
        """Update activity state information."""
        self._state = await self._remote.get_activity_state(self._id)
        # await self._remote.update()


def discover_devices(apikey):
    """Zero Conf class."""

    class DeviceListener:
        """Zeroconf Device Listener."""

        def __init__(self) -> None:
            """Discover devices."""
            self.apikey = apikey
            self.devices = []

        def add_service(self, zconf, type_, name):
            """Is Called by zeroconf when something is found."""
            info = zconf.get_service_info(type_, name)
            host = socket.inet_ntoa(info.addresses[0])
            endpoint = f"http://{host}:{info.port}/api/"
            self.devices.append(Remote(endpoint, self.apikey))

        def update_service(self, zconf, type_, name):
            """Nothing."""

        def remove_service(self, zconf, type_, name):
            """Nothing."""

    zconf = zeroconf.Zeroconf(interfaces=zeroconf.InterfaceChoice.Default)
    listener = DeviceListener()
    zeroconf.ServiceBrowser(zconf, ZEROCONF_SERVICE_TYPE, listener)
    try:
        time.sleep(ZEROCONF_TIMEOUT)
    finally:
        zconf.close()
    return RemoteGroup(copy.deepcopy(listener.devices))
