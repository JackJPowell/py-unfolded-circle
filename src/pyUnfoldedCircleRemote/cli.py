"""Command Line Interface for pyUnfoldedCircleRemote."""

import asyncio
import sys
import logging
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.json import JSON
    from rich.tree import Tree
except ImportError as e:
    print("CLI dependencies not installed. Please install with:")
    print("pip install pyUnfoldedCircleRemote[cli]")
    print(f"Missing dependency: {e}")
    sys.exit(1)

from .remote import Remote, discover_devices
from .const import SYSTEM_COMMANDS

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


async def connect_remote(
    url: str, apikey: Optional[str] = None, pin: Optional[str] = None
) -> Remote:
    """Connect to a remote and initialize it."""
    remote = Remote(url, apikey=apikey, pin=pin)
    try:
        await remote.init()
        return remote
    except Exception as e:
        console.print(f"[red]Failed to connect to remote: {e}[/red]")
        sys.exit(1)


def print_json_data(data, title: str = "Data"):
    """Print JSON data in a nice format."""
    console.print(Panel(JSON.from_data(data), title=title))


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """Command line interface for Unfolded Circle Remote Two."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@cli.command()
def discover():
    """Discover Unfolded Circle remotes on the network."""
    console.print("[blue]Discovering remotes...[/blue]")

    try:
        devices = discover_devices(None)

        if not devices:
            console.print("[yellow]No remotes found[/yellow]")
            return

        table = Table(title="Discovered Remotes")
        table.add_column("Name", style="cyan")
        table.add_column("IP Address", style="green")
        table.add_column("MAC Address", style="yellow")
        table.add_column("API URL", style="blue")

        for device in devices:
            table.add_row(
                getattr(device, "name", "Unknown") or "Unknown",
                getattr(device, "ip_address", "Unknown") or "Unknown",
                getattr(device, "mac_address", "Unknown") or "Unknown",
                getattr(device, "endpoint", "Unknown") or "Unknown",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Discovery failed: {e}[/red]")


@cli.command()
@click.option(
    "--url",
    "-u",
    required=True,
    help="Remote API URL (e.g., http://192.168.1.100:8080/api/)",
)
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def info(url, apikey, pin):
    """Get remote information and status."""

    async def get_info():
        remote = await connect_remote(url, apikey, pin)

        # Basic info
        info_table = Table(title="Remote Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="green")

        info_data = [
            ("Name", remote.name),
            ("Model", remote.model_name),
            ("Serial Number", remote.serial_number),
            ("Software Version", remote.sw_version),
            ("IP Address", remote.ip_address),
            ("MAC Address", remote.mac_address),
            ("Battery Level", f"{remote.battery_level}%"),
            ("Battery Status", remote.battery_status),
            ("Is Charging", str(remote.is_charging)),
            ("Power Mode", remote.power_mode),
            ("Online", str(remote.online)),
        ]

        for prop, value in info_data:
            info_table.add_row(prop, str(value) if value is not None else "Unknown")

        console.print(info_table)

        # Activities
        if remote.activities:
            activities_table = Table(title="Activities")
            activities_table.add_column("Name", style="cyan")
            activities_table.add_column("ID", style="yellow")
            activities_table.add_column("State", style="green")

            for activity in remote.activities:
                activities_table.add_row(activity.name, activity.id, activity.state)

            console.print(activities_table)
        else:
            console.print("[yellow]No activities found[/yellow]")

    asyncio.run(get_info())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def activities(url, apikey, pin):
    """List all activities."""

    async def list_activities():
        remote = await connect_remote(url, apikey, pin)

        if not remote.activities:
            console.print("[yellow]No activities found[/yellow]")
            return

        tree = Tree("Activities")

        # Activities in groups
        if remote.activity_groups:
            for group in remote.activity_groups:
                group_node = tree.add(
                    f"[bold cyan]{group.name}[/bold cyan] ({group.state})"
                )
                for activity in group.activities:
                    activity_node = group_node.add(f"[green]{activity.name}[/green]")
                    activity_node.add(f"ID: {activity.id}")
                    activity_node.add(f"State: {activity.state}")

        # Activities not in groups
        ungrouped_activities = [
            a
            for a in remote.activities
            if not any(g.is_activity_in_group(a.id) for g in remote.activity_groups)
        ]

        if ungrouped_activities:
            ungrouped_node = tree.add("[bold yellow]Ungrouped Activities[/bold yellow]")
            for activity in ungrouped_activities:
                activity_node = ungrouped_node.add(f"[green]{activity.name}[/green]")
                activity_node.add(f"ID: {activity.id}")
                activity_node.add(f"State: {activity.state}")

        console.print(tree)

    asyncio.run(list_activities())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.argument("activity_id")
def start_activity(url, apikey, pin, activity_id):
    """Start an activity by ID."""

    async def start():
        remote = await connect_remote(url, apikey, pin)

        try:
            activity = remote.get_activity_by_id(activity_id)
            if activity:
                await activity.turn_on()
                console.print(f"[green]Started activity: {activity.name}[/green]")
            else:
                console.print(f"[red]Activity not found: {activity_id}[/red]")
        except Exception as e:
            console.print(f"[red]Failed to start activity: {e}[/red]")

    asyncio.run(start())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.argument("activity_id")
def stop_activity(url, apikey, pin, activity_id):
    """Stop an activity by ID."""

    async def stop():
        remote = await connect_remote(url, apikey, pin)

        try:
            activity = remote.get_activity_by_id(activity_id)
            if activity:
                await activity.turn_off()
                console.print(f"[green]Stopped activity: {activity.name}[/green]")
            else:
                console.print(f"[red]Activity not found: {activity_id}[/red]")
        except Exception as e:
            console.print(f"[red]Failed to stop activity: {e}[/red]")

    asyncio.run(stop())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.argument("command", type=click.Choice(SYSTEM_COMMANDS))
def system(url, apikey, pin, command):
    """Send system command to remote."""

    async def send_command():
        remote = await connect_remote(url, apikey, pin)

        try:
            await remote.post_system_command(command)
            console.print(f"[green]System command sent: {command}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to send system command: {e}[/red]")

    asyncio.run(send_command())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.argument("button_name")
@click.option("--activity", help="Activity context for button command")
@click.option("--repeat", "-r", default=1, help="Number of times to repeat")
@click.option("--hold", is_flag=True, help="Hold the button")
def send_button(url, apikey, pin, button_name, activity, repeat, hold):
    """Send button command to remote."""

    async def send_button():
        remote = await connect_remote(url, apikey, pin)

        try:
            await remote.send_button_command(
                command=button_name, repeat=repeat, activity=activity, hold=hold
            )
            console.print(f"[green]Button command sent: {button_name}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to send button command: {e}[/red]")

    asyncio.run(send_button())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.argument("device")
@click.argument("command")
@click.option("--repeat", "-r", default=1, help="Number of times to repeat")
@click.option("--dock", help="Dock name")
@click.option("--port", type=int, help="IR port")
def ir(url, apikey, pin, device, command, repeat, dock, port):
    """Send IR command to remote."""

    async def send_ir():
        remote = await connect_remote(url, apikey, pin)

        try:
            kwargs = {}
            if dock:
                kwargs["dock"] = dock
            if port:
                kwargs["port"] = port

            await remote.send_remote_command(
                device=device, command=command, repeat=repeat, **kwargs
            )
            console.print(f"[green]IR command sent: {device} -> {command}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to send IR command: {e}[/red]")

    asyncio.run(send_ir())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option(
    "--pin", "-p", help="PIN for authentication (required for API key operations)"
)
def create_api_key(url, pin):
    """Create a new API key."""
    if not pin:
        console.print("[red]PIN is required for API key creation[/red]")
        sys.exit(1)

    async def create_key():
        remote = Remote(url, pin=pin)

        try:
            api_key = await remote.create_api_key()
            console.print(
                Panel(
                    f"[green]API Key created successfully![/green]\n\n"
                    f"[bold]API Key:[/bold] {api_key}\n\n"
                    f"[yellow]Save this key securely - it won't be shown again![/yellow]",
                    title="API Key Created",
                )
            )
        except Exception as e:
            console.print(f"[red]Failed to create API key: {e}[/red]")

    asyncio.run(create_key())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option(
    "--pin", "-p", help="PIN for authentication (required for API key operations)"
)
@click.option("--name", default="pyUnfoldedCircle", help="API key name to revoke")
def revoke_api_key(url, pin, name):
    """Revoke an existing API key."""
    if not pin:
        console.print("[red]PIN is required for API key operations[/red]")
        sys.exit(1)

    async def revoke_key():
        remote = Remote(url, pin=pin)

        try:
            await remote.revoke_api_key(name)
            console.print(f"[green]API key '{name}' revoked successfully![/green]")
        except Exception as e:
            console.print(f"[red]Failed to revoke API key: {e}[/red]")

    asyncio.run(revoke_key())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def integrations(url, apikey, pin):
    """List integrations."""

    async def list_integrations():
        remote = await connect_remote(url, apikey, pin)

        try:
            integrations_data = await remote.get_integrations()

            if not integrations_data:
                console.print("[yellow]No integrations found[/yellow]")
                return

            table = Table(title="Integrations")
            table.add_column("Name", style="cyan")
            table.add_column("Driver ID", style="yellow")
            table.add_column("Instance ID", style="green")
            table.add_column("State", style="blue")

            for integration in integrations_data:
                table.add_row(
                    integration.get("name", "Unknown"),
                    integration.get("driver_id", "Unknown"),
                    integration.get("instance_id", "Unknown"),
                    integration.get("state", "Unknown"),
                )

            console.print(table)

        except Exception as e:
            console.print(f"[red]Failed to list integrations: {e}[/red]")

    asyncio.run(list_integrations())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def battery(url, apikey, pin):
    """Get battery information."""

    async def get_battery():
        remote = await connect_remote(url, apikey, pin)

        battery_table = Table(title="Battery Information")
        battery_table.add_column("Property", style="cyan")
        battery_table.add_column("Value", style="green")

        battery_data = [
            ("Battery Level", f"{remote.battery_level}%"),
            ("Battery Status", remote.battery_status),
            ("Is Charging", str(remote.is_charging)),
            ("Is Wireless Charging", str(remote.is_wireless_charging)),
            ("Wireless Charging Enabled", str(remote.is_wireless_charging_enabled)),
        ]

        for prop, value in battery_data:
            battery_table.add_row(prop, value)

        console.print(battery_table)

    asyncio.run(get_battery())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def status(url, apikey, pin, output_format):
    """Get comprehensive remote status."""

    async def get_status():
        remote = await connect_remote(url, apikey, pin)

        if output_format == "json":
            status_data = {
                "name": remote.name,
                "model": remote.model_name,
                "software_version": remote.sw_version,
                "ip_address": remote.ip_address,
                "mac_address": remote.mac_address,
                "battery_level": remote.battery_level,
                "battery_status": remote.battery_status,
                "is_charging": remote.is_charging,
                "power_mode": remote.power_mode,
                "online": remote.online,
                "activities": [
                    {"name": activity.name, "id": activity.id, "state": activity.state}
                    for activity in remote.activities
                ],
            }
            print_json_data(status_data, "Remote Status")
        else:
            # Create a status table
            info_table = Table(title="Remote Status")
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="green")

            info_data = [
                ("Name", remote.name),
                ("Model", remote.model_name),
                ("Software Version", remote.sw_version),
                ("IP Address", remote.ip_address),
                ("MAC Address", remote.mac_address),
                ("Battery Level", f"{remote.battery_level}%"),
                ("Battery Status", remote.battery_status),
                ("Is Charging", str(remote.is_charging)),
                ("Power Mode", remote.power_mode),
                ("Online", str(remote.online)),
            ]

            for prop, value in info_data:
                info_table.add_row(prop, str(value) if value is not None else "Unknown")

            console.print(info_table)

    asyncio.run(get_status())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def wake(url, apikey, pin):
    """Wake up the remote using Wake-on-LAN."""

    async def wake_remote():
        remote = await connect_remote(url, apikey, pin)

        try:
            success = await remote.wake()
            if success:
                console.print("[green]Remote woken up successfully![/green]")
            else:
                console.print(
                    "[yellow]Wake command sent, but remote may not have responded[/yellow]"
                )
        except Exception as e:
            console.print(f"[red]Failed to wake remote: {e}[/red]")

    asyncio.run(wake_remote())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
@click.option(
    "--enabled/--disabled", default=True, help="Enable or disable wireless charging"
)
def wireless_charging(url, apikey, pin, enabled):
    """Enable or disable wireless charging."""

    async def set_wireless_charging():
        remote = await connect_remote(url, apikey, pin)

        try:
            await remote.set_remote_wireless_charging(enabled)
            charging_status = "enabled" if enabled else "disabled"
            console.print(f"[green]Wireless charging {charging_status}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to set wireless charging: {e}[/red]")

    asyncio.run(set_wireless_charging())


@cli.command()
@click.option("--url", "-u", required=True, help="Remote API URL")
@click.option("--apikey", "-k", help="API key for authentication")
@click.option("--pin", "-p", help="PIN for authentication")
def docks(url, apikey, pin):
    """List available docks."""

    async def list_docks():
        remote = await connect_remote(url, apikey, pin)

        if not remote.docks:
            console.print("[yellow]No docks found[/yellow]")
            return

        table = Table(title="Docks")
        table.add_column("Name", style="cyan")
        table.add_column("ID", style="yellow")
        table.add_column("Model", style="green")
        table.add_column("Active", style="blue")

        for dock in remote.docks:
            table.add_row(
                getattr(dock, "name", "Unknown"),
                getattr(dock, "id", "Unknown"),
                getattr(dock, "model", "Unknown"),
                str(getattr(dock, "active", False)),
            )

        console.print(table)

    asyncio.run(list_docks())
