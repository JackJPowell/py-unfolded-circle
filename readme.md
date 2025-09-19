# pyUnfoldedCircleRemote

A Python library and command-line interface for interacting with [Unfolded Circle Remote Two](https://www.unfoldedcircle.com/) devices.

## Features

- 🌐 **Device Discovery** - Automatically discover remotes on your network
- 🔑 **Authentication** - Support for both PIN and API key authentication  
- 🎬 **Activity Control** - Start, stop, and manage activities
- 🎮 **Button Commands** - Send button presses and remote commands
- 📡 **IR Control** - Send infrared commands to devices
- 🔋 **Status Monitoring** - Get battery, power, and system information
- 🏠 **Integration Management** - Manage Home Assistant and other integrations
- 🖥️ **CLI Interface** - Full command-line interface for automation
- 📊 **Rich Output** - Beautiful table and JSON output formats

## Installation

### Basic Installation
```bash
pip install pyUnfoldedCircleRemote
```

### With CLI Support
```bash
pip install pyUnfoldedCircleRemote[cli]
```

### Development Installation
```bash
git clone https://github.com/jackjpowell/py-unfolded-circle.git
cd py-unfolded-circle
poetry install --extras cli
```

## Quick Start

### Python Library Usage

```python
import asyncio
from pyUnfoldedCircleRemote import Remote, discover_devices

async def main():
    # Discover remotes on network
    devices = discover_devices(None)
    if devices:
        remote_device = devices[0]
        print(f"Found: {remote_device.name} at {remote_device.ip_address}")
    
    # Connect to remote
    remote = Remote("http://192.168.1.100:8080/api/", apikey="your-api-key")
    await remote.init()
    
    # Get remote info
    print(f"Remote: {remote.name}")
    print(f"Battery: {remote.battery_level}%")
    
    # List activities  
    for activity in remote.activities:
        print(f"Activity: {activity.name} ({activity.state})")
    
    # Start an activity
    if remote.activities:
        await remote.activities[0].turn_on()

asyncio.run(main())
```

### Command Line Usage

```bash
# Discover remotes
uc-remote discover

# Get remote information  
uc-remote info --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY

# List activities
uc-remote activities --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY

# Start an activity
uc-remote start-activity ACTIVITY_ID --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY

# Send button command
uc-remote button VOLUME_UP --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY

# Send IR command
uc-remote ir "Samsung TV" "power" --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY

# Get battery status
uc-remote battery --url http://192.168.1.100:8080/api/ --apikey YOUR_API_KEY
```

## Authentication

### First Time Setup (Create API Key)

```bash
# Create API key using PIN
uc-remote create-api-key --url http://192.168.1.100:8080/api/ --pin YOUR_PIN
```

### Environment Variables

Set these to avoid repeating connection details:

```bash
export UC_REMOTE_URL="http://192.168.1.100:8080/api/"
export UC_REMOTE_API_KEY="your-api-key-here"

# Then use shorter commands:
uc-remote info
uc-remote activities
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `discover` | Find remotes on network |
| `info` | Get remote information |
| `activities` | List all activities |
| `start-activity` | Start an activity |
| `stop-activity` | Stop an activity |
| `button` | Send button command |
| `ir` | Send IR command |
| `system` | Send system command |
| `battery` | Get battery information |
| `status` | Get comprehensive status |
| `integrations` | List integrations |
| `docks` | List docks |
| `wake` | Wake remote with WOL |
| `wireless-charging` | Control wireless charging |
| `create-api-key` | Create new API key |
| `revoke-api-key` | Revoke API key |

## Python API

### Core Classes

- **`Remote`** - Main interface to the remote device
- **`Activity`** - Represents an activity that can be started/stopped
- **`ActivityGroup`** - Group of related activities
- **`UCMediaPlayerEntity`** - Media player entity within activities
- **`Dock`** - Charging dock information

### Key Methods

```python
# Connection and setup
remote = Remote(api_url, apikey=api_key)
await remote.init()  # Initialize connection and load data
await remote.update()  # Refresh current status

# Activity control
await remote.get_activities()
activity = remote.get_activity_by_id(activity_id)
await activity.turn_on()
await activity.turn_off()

# Commands
await remote.send_button_command("VOLUME_UP", activity="activity_id")
await remote.send_remote_command("TV", "power")
await remote.post_system_command("STANDBY")

# Information
battery_level = remote.battery_level
is_charging = remote.is_charging
activities = remote.activities
```

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- **`example_script.py`** - Comprehensive examples showing basic usage, API key creation, and monitoring

See [`CLI_USAGE.md`](CLI_USAGE.md) for detailed CLI documentation and examples.

## System Commands

Available system commands:
- `STANDBY` - Put remote to standby
- `REBOOT` - Reboot the remote
- `POWER_OFF` - Power off the remote  
- `RESTART` - Restart the remote software
- `RESTART_UI` - Restart the UI only
- `RESTART_CORE` - Restart the core service only

## Requirements

- Python 3.8+
- aiohttp
- wakeonlan
- packaging
- zeroconf

### CLI Additional Requirements
- click
- rich

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Unfolded Circle Remote Two](https://www.unfoldedcircle.com/) - The hardware this library controls
- [Home Assistant Integration](https://github.com/jackjpowell/hass-unfoldedcircle) - Home Assistant integration using this library

## Disclaimer

This is an unofficial library and is not affiliated with Unfolded Circle. Use at your own risk.