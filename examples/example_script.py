#!/usr/bin/env python3
"""
Example script showing how to use pyUnfoldedCircleRemote with the CLI functionality.

This script demonstrates basic usage patterns for automating Unfolded Circle Remote Two.
"""

import asyncio
import sys
from pyUnfoldedCircleRemote import Remote, discover_devices


async def example_basic_usage():
    """Example of basic remote control usage."""

    # First, discover remotes on the network
    print("🔍 Discovering remotes...")
    try:
        devices = discover_devices(None)
        if not devices:
            print("❌ No remotes found on the network")
            return

        remote_device = devices[0]  # Use the first discovered remote
        print(f"✅ Found remote: {remote_device.name} at {remote_device.ip_address}")

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return

    # Connect to the remote (you'll need to provide your API key or PIN)
    # For initial setup, you can use PIN authentication
    api_url = f"http://{remote_device.ip_address}:8080/api/"

    # Option 1: Use API key authentication (recommended for scripts)
    # api_key = "your-api-key-here"  # Get this from create_api_key CLI command
    # remote = Remote(api_url, apikey=api_key)

    # Option 2: Use PIN authentication (for initial setup)
    pin = "1234"  # Replace with your remote's PIN
    remote = Remote(api_url, pin=pin)

    # For this example, we'll assume you have an API key
    print("⚠️  Please set your API key or PIN in this script before running")
    # return

    try:
        # Initialize connection and get remote information
        print("🔗 Connecting to remote...")
        await remote.init()

        print(f"📱 Remote Name: {remote.name}")
        print(f"🔋 Battery Level: {remote.battery_level}%")
        print(f"⚡ Is Charging: {remote.is_charging}")
        print(f"🌐 IP Address: {remote.ip_address}")

        # List activities
        print(f"\n🎬 Activities ({len(remote.activities)}):")
        for activity in remote.activities:
            print(f"  • {activity.name} ({activity.id}) - {activity.state}")

        # Example: Start the first activity (if any exist)
        if remote.activities:
            first_activity = remote.activities[0]
            print(f"\n▶️  Starting activity: {first_activity.name}")
            await first_activity.turn_on()

            # Wait a bit
            await asyncio.sleep(2)

            # Send a button command in the activity context
            print("🎮 Sending VOLUME_UP button command...")
            await remote.send_button_command(
                command="VOLUME_UP", activity=first_activity.id
            )

            # Stop the activity
            print(f"⏹️  Stopping activity: {first_activity.name}")
            await first_activity.turn_off()

        # Example: Send an IR command (if you have IR devices configured)
        if remote._remotes:  # Check if any IR remotes are configured
            print("\n📡 Sending IR command example...")
            try:
                await remote.send_remote_command(
                    device="TV",  # Replace with your device name
                    command="power",  # Replace with your command
                )
                print("✅ IR command sent successfully")
            except Exception as e:
                print(f"⚠️  IR command failed: {e}")

        # Get battery status
        print(f"\n🔋 Final battery level: {remote.battery_level}%")

    except Exception as e:
        print(f"❌ Remote operation failed: {e}")


async def example_create_api_key():
    """Example of creating an API key programmatically."""

    print("🔑 Creating API key example...")

    # You need the remote's IP and PIN for this
    remote_ip = "192.168.1.100"  # Replace with your remote's IP
    pin = "1234"  # Replace with your remote's PIN

    api_url = f"http://{remote_ip}:8080/api/"
    remote = Remote(api_url, pin=pin)

    try:
        # Create API key
        api_key = await remote.create_api_key()
        print(f"✅ API Key created: {api_key}")
        print("💾 Save this key securely - you won't see it again!")

        # Now you can use this API key for future connections
        # remote = Remote(api_url, apikey=api_key)

    except Exception as e:
        print(f"❌ Failed to create API key: {e}")


async def example_monitoring():
    """Example of monitoring remote status."""

    print("📊 Remote monitoring example...")

    # Replace with your remote details
    api_url = "http://192.168.1.100:8080/api/"
    api_key = "your-api-key-here"

    remote = Remote(api_url, apikey=api_key)

    try:
        await remote.init()

        print("🔍 Monitoring remote status for 30 seconds...")

        for i in range(6):  # Monitor for 30 seconds (6 x 5 second intervals)
            await remote.update()  # Refresh remote status

            print(f"\n📊 Status Update #{i + 1}:")
            print(f"  🔋 Battery: {remote.battery_level}% ({remote.battery_status})")
            print(f"  ⚡ Charging: {remote.is_charging}")
            print(f"  🌟 Power Mode: {remote.power_mode}")
            print(f"  💡 Ambient Light: {remote.ambient_light_intensity}")

            # Check if any activities are running
            running_activities = [a for a in remote.activities if a.state == "ON"]
            if running_activities:
                print(f"  🎬 Active Activities: {[a.name for a in running_activities]}")
            else:
                print("  🎬 No activities running")

            if i < 5:  # Don't sleep after the last iteration
                await asyncio.sleep(5)

    except Exception as e:
        print(f"❌ Monitoring failed: {e}")


def main():
    """Main function to demonstrate CLI usage."""
    print("🚀 pyUnfoldedCircleRemote CLI Example Script")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python example_script.py basic     - Basic usage example")
        print("  python example_script.py apikey    - Create API key example")
        print("  python example_script.py monitor   - Monitoring example")
        return

    mode = sys.argv[1].lower()

    if mode == "basic":
        asyncio.run(example_basic_usage())
    elif mode == "apikey":
        asyncio.run(example_create_api_key())
    elif mode == "monitor":
        asyncio.run(example_monitoring())
    else:
        print(f"❌ Unknown mode: {mode}")


if __name__ == "__main__":
    main()
