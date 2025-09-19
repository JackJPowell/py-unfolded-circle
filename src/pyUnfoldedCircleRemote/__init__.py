"""pyUnfoldedCircleRemote - A Python library to interact with Unfolded Circle Remote Two."""

from .remote import Remote, RemoteGroup, Activity, ActivityGroup, UCMediaPlayerEntity, discover_devices
from .dock import Dock
from .const import RemotePowerModes, RemoteUpdateType, SYSTEM_COMMANDS

__version__ = "0.15.0"
__all__ = [
    "Remote",
    "RemoteGroup", 
    "Activity",
    "ActivityGroup",
    "UCMediaPlayerEntity",
    "Dock",
    "discover_devices",
    "RemotePowerModes",
    "RemoteUpdateType", 
    "SYSTEM_COMMANDS",
]