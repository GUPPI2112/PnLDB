import logging
import discord
from discord.ext import commands
from src.config import config
from src.bot.views import PnLLauncherView
from src.bot.commands.pnl import pnl_command
from src.bot.commands.setup import setup_command

logger = logging.getLogger(__name__)


class NFTPnLBot(commands.Bot):
    """
    NFT PnL Discord Bot client.
    """

    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):
        # Register persistent launcher view for the "Check PnL" button
        self.add_view(PnLLauncherView())

        # Register slash commands
        self.tree.add_command(pnl_command)
        self.tree.add_command(setup_command)

        # Sync application commands
        if config.DISCORD_GUILD_ID:
            guild_obj = discord.Object(id=config.DISCORD_GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            synced = await self.tree.sync(guild=guild_obj)
            logger.info("Synced %d guild slash command(s) to guild %s", len(synced), config.DISCORD_GUILD_ID)
        else:
            synced = await self.tree.sync()
            logger.info("Synced %d global slash command(s)", len(synced))

    async def on_ready(self):
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "Unknown")
        logger.info("Bot is active in %d guild(s)", len(self.guilds))
        if self.user:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="NFT PnLs | Click Check PnL",
                )
            )


def create_bot() -> NFTPnLBot:
    return NFTPnLBot()
