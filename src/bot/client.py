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
        try:
            if config.DISCORD_GUILD_ID:
                guild_obj = discord.Object(id=config.DISCORD_GUILD_ID)
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                logger.info("Synced %d guild slash command(s) to guild %s", len(synced), config.DISCORD_GUILD_ID)
            else:
                synced = await self.tree.sync()
                logger.info("Synced %d global slash command(s)", len(synced))
        except Exception as e:
            logger.warning("Error syncing slash commands: %s", e)

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

        # Auto-post the Check PnL panel to the specified channel if configured
        if config.PNL_CHANNEL_ID:
            await self.auto_post_panel(config.PNL_CHANNEL_ID)

    async def on_guild_join(self, guild: discord.Guild):
        logger.info("Joined new guild: %s (ID: %s)", guild.name, guild.id)
        if config.PNL_CHANNEL_ID:
            await self.auto_post_panel(config.PNL_CHANNEL_ID)

    async def auto_post_panel(self, channel_id: int):
        try:
            channel = self.get_channel(channel_id)
            if channel is None:
                try:
                    channel = await self.fetch_channel(channel_id)
                except Exception:
                    channel = None

            if isinstance(channel, (discord.TextChannel, discord.Thread)):
                # Check recent messages to avoid duplicate panel posting
                async for msg in channel.history(limit=10):
                    if msg.author == self.user and msg.components:
                        logger.info("Check PnL panel already active in channel %s", channel_id)
                        return

                embed = discord.Embed(
                    title="NFT PnL Tracker",
                    description=(
                        "Calculate your NFT collection PnL, ROI %, and trade statistics across multiple chains.\n\n"
                        "Click **Check PnL** below to open the form and generate your custom card."
                    ),
                    color=discord.Color.from_rgb(47, 230, 149),
                )
                embed.add_field(
                    name="Supported Chains",
                    value="ETH, Base, SOL, BTC (Ordinals), Robinhood, Polygon, Arbitrum, Optimism, Blast, Zora, ApeChain",
                    inline=False,
                )
                embed.set_footer(text="Multi-Chain NFT PnL Tracker")

                view = PnLLauncherView()
                await channel.send(embed=embed, view=view)
                logger.info("Successfully posted Check PnL panel to channel %s", channel_id)
        except Exception as e:
            logger.warning(
                "Could not auto-post panel to channel %s: %s (You can also run /setup manually in the channel)",
                channel_id,
                e,
            )


def create_bot() -> NFTPnLBot:
    return NFTPnLBot()
