from __future__ import annotations

import logging

import tabulate
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config, Group
from redbot.core.utils.chat_formatting import box
from wakeonlan import send_magic_packet

from .vexutils import format_help, format_info

log = logging.getLogger("red.vex.wol")


def humanize_mac(mac: str):
    # https://stackoverflow.com/a/3258612/15605599
    return ":".join(mac[i : i + 2] for i in range(0, len(mac), 2))


class WOL(commands.Cog):
    """
    Send a magic packet (Wake on LAN) to a computer on the local network.

    Get started by adding your computer with `[p]wolset add <friendly_name> <mac>`.
    Then you can wake it with `[p]wol <friendly_name>`.

    For example, `[p]wolset add main_pc 11:22:33:44:55:66` then you can use
    `[p]wol main_pc`
    """

    __version__ = "1.0.5"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(addresses={})

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        # lets assume the owner wont run this.....
        return

    @commands.command(hidden=True)
    async def wolinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    @commands.is_owner()
    @commands.command()
    async def wol(self, ctx: commands.Context, machine: str):
        """
        Wake a local computer.

        You can set up a short name with `[p]wolset add` so you don't need to
        write out the MAC each time, or just send the MAC.

        **Examples:**
            - `[p]wol main_pc`
            - `[p]wol 11:22:33:44:55:66`
        """
        if len(machine) in (12, 17):  # could be a MAC address
            try:
                send_magic_packet(machine)
            except ValueError:  # okay it's not a valid format
                pass
            else:
                return await ctx.send("I've woken that machine.")

        data = await self.config.addresses()
        machine = machine.lower()
        if machine.lower() in data:
            send_magic_packet(data[machine.lower()])
            return await ctx.send(f"I've woken {machine}.")

        await ctx.send(
            "I can't find that machine. You can add it with "
            if data
            else "You haven't added any machines yet. Get started with"
            + f"`{ctx.clean_prefix}wolset add <friendly_name> <mac>`."
        )

    @commands.group()
    @commands.is_owner()
    async def wolset(self, ctx: commands.Context):
        """Manage your saved computer/MAC aliases for easy access."""

    @wolset.command()
    async def add(self, ctx: commands.Context, friendly_name: str, mac: str):
        """
        Add a machine for easy use with `[p]wol`.

        `<friendly_name>` **cannot** include spaces.

        **Examples:**
            - `wolset add main_pc 11:22:33:44:55:66`
            - `wolset add main_pc 11-22-33-44-55-66`
        """
        if len(mac) == 17:
            mac = mac.replace(mac[2], "")
        elif len(mac) != 12:
            return await ctx.send("That doesn't look like a valid MAC.")

        assert isinstance(self.config.addresses, Group)
        await self.config.addresses.set_raw(friendly_name.lower(), value=mac)
        await ctx.send(f"{friendly_name} added as an alias for `{mac}`")

    @wolset.command(aliases=["del", "delete"])
    async def remove(self, ctx: commands.Context, friendly_name: str):
        """
        Remove a machine from my list of machines.

        **Examples:**
            - `wolset remove main_pc`
        """
        conf: dict[str, str]
        async with self.config.addresses() as conf:
            try:
                conf.pop(friendly_name.lower())
            except KeyError:
                await ctx.send(
                    f"That's not a valid name. Check out `{ctx.clean_prefix}wolset list`."
                )
            else:
                await ctx.send("Removed.")

    @wolset.command()
    async def list(self, ctx: commands.Context):
        """
        See your added addresses.

        This will send your MAC addresses to the current channel.
        """
        conf: dict[str, str] = await self.config.addresses()
        if not conf:
            return await ctx.send("You haven't added any machines yet.")

        data = [[f"[{name}]", humanize_mac(mac)] for name, mac in conf.items()]
        table = tabulate.tabulate(data, headers=["Name", "MAC"])

        # god i hope no-one hits 2k chars
        await ctx.send("Here is are your added computers:" + box(table, "ini"))
