# CLI Usage Examples

This document provides examples of how to use the `uc-remote` command-line interface.

## Installation

First, install the package with CLI dependencies:

```bash
pip install pyUnfoldedCircleRemote[cli]
# or if you're using poetry:
poetry install --extras cli
```

## Basic Commands

### Discovery
Find remotes on your network:
```bash
uc-remote discover
```

### Get Remote Information
```bash
uc-remote info --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Create API Key
First-time setup (requires PIN):
```bash
uc-remote create-api-key --url http://192.168.1.100:8080/api/ --pin 1234
```

## Activity Management

### List Activities
```bash
uc-remote activities --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Start an Activity
```bash
uc-remote start-activity activity-id --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Stop an Activity  
```bash
uc-remote stop-activity activity-id --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

## Control Commands

### Send Button Commands
```bash
# Simple button press
uc-remote button HOME --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Button with activity context
uc-remote button VOLUME_UP --activity activity-id --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Hold button
uc-remote button POWER --hold --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Repeat button
uc-remote button CHANNEL_UP --repeat 3 --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Send IR Commands
```bash
# Basic IR command
uc-remote ir "Samsung TV" "power" --url http://192.168.1.100:8080/api/ --apikey your-api-key

# IR command with dock specification
uc-remote ir "Samsung TV" "power" --dock "Living Room Dock" --url http://192.168.1.100:8080/api/ --apikey your-api-key

# IR command with port specification
uc-remote ir "Samsung TV" "volume_up" --port 1 --repeat 3 --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### System Commands
```bash
# Available commands: STANDBY, REBOOT, POWER_OFF, RESTART, RESTART_UI, RESTART_CORE
uc-remote system STANDBY --url http://192.168.1.100:8080/api/ --apikey your-api-key
uc-remote system REBOOT --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

## Status and Information

### Battery Status
```bash
uc-remote battery --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Full Status
```bash
# Table format (default)
uc-remote status --url http://192.168.1.100:8080/api/ --apikey your-api-key

# JSON format
uc-remote status --format json --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### List Integrations
```bash
uc-remote integrations --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### List Docks
```bash
uc-remote docks --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

## Power Management

### Wake Remote
```bash
uc-remote wake --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### Wireless Charging Control
```bash
# Enable wireless charging
uc-remote wireless-charging --enabled --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Disable wireless charging  
uc-remote wireless-charging --disabled --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

## Configuration Management

### API Key Management
```bash
# Create new API key (requires PIN)
uc-remote create-api-key --url http://192.168.1.100:8080/api/ --pin 1234

# Revoke API key (requires PIN)
uc-remote revoke-api-key --url http://192.168.1.100:8080/api/ --pin 1234 --name "pyUnfoldedCircle"
```

## Environment Variables

You can set environment variables to avoid repeating common parameters:

```bash
export UC_REMOTE_URL="http://192.168.1.100:8080/api/"
export UC_REMOTE_API_KEY="your-api-key-here"

# Then you can use shorter commands:
uc-remote info
uc-remote activities
uc-remote battery
```

## Output Formats

Most commands support different output formats:
- **Table format**: Human-readable tables (default)
- **JSON format**: Machine-readable JSON output

## Verbose Mode

Add `--verbose` or `-v` to any command for detailed logging:

```bash
uc-remote info --verbose --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

## Common Use Cases

### 1. Initial Setup
```bash
# 1. Discover your remote
uc-remote discover

# 2. Create API key (use your remote's PIN)
uc-remote create-api-key --url http://YOUR_REMOTE_IP:8080/api/ --pin YOUR_PIN

# 3. Test connection
uc-remote info --url http://YOUR_REMOTE_IP:8080/api/ --apikey YOUR_API_KEY
```

### 2. Daily Control
```bash
# Turn on TV activity
uc-remote start-activity tv-activity-id --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Send volume up command
uc-remote button VOLUME_UP --activity tv-activity-id --url http://192.168.1.100:8080/api/ --apikey your-api-key

# Check battery level
uc-remote battery --url http://192.168.1.100:8080/api/ --apikey your-api-key
```

### 3. Automation & Scripting
```bash
#!/bin/bash
# Example automation script

UC_URL="http://192.168.1.100:8080/api/"
UC_KEY="your-api-key"

# Morning routine
uc-remote start-activity morning-routine --url $UC_URL --apikey $UC_KEY
uc-remote ir "Coffee Machine" "power" --url $UC_URL --apikey $UC_KEY

# Evening routine  
uc-remote system STANDBY --url $UC_URL --apikey $UC_KEY
```
