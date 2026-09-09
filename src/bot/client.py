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
                embed = discord.Embed(
                    title="NFT PnL Tracker",
                    description=(
                        "Calculate your NFT collection PnL, ROI %, and trade statistics across all blockchains.\n\n"
                        "Click **Check PnL** below and enter your wallet and contract address — the network will be **auto-detected automatically**."
                    ),
                    color=discord.Color.from_rgb(47, 230, 149),
                )
                embed.add_field(
                    name="Supported Networks",
                    value="Ethereum, Base, Arbitrum, Polygon, Optimism, Blast, Zora, ApeChain, Solana, Bitcoin",
                    inline=False,
                )
                embed.set_footer(text="Obsidian Multi-Chain NFT Analytics")

                view = PnLLauncherView()

                # Update existing message if present, or post a new clean panel
                updated_existing = False
                async for msg in channel.history(limit=10):
                    if msg.author == self.user and msg.components:
                        try:
                            await msg.edit(embed=embed, view=view)
                            logger.info("Updated existing Check PnL panel in channel %s", channel_id)
                            updated_existing = True
                            break
                        except Exception:
                            pass

                if not updated_existing:
                    await channel.send(embed=embed, view=view)
                    logger.info("Successfully posted Check PnL panel to channel %s", channel_id)
        except Exception as e:
            logger.warning(
                "Could not post/update panel in channel %s: %s",
                channel_id,
                e,
            )


def create_bot() -> NFTPnLBot:
    return NFTPnLBot()
