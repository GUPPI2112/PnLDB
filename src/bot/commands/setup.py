import discord
from discord import app_commands
from src.bot.views import PnLLauncherView


@app_commands.command(name="setup", description="Post the interactive Check PnL button panel in this channel")
@app_commands.default_permissions(manage_guild=True)
async def setup_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="NFT PnL Tracker",
        description=(
            "Calculate your NFT collection PnL, ROI %, and trade statistics across multiple chains.\n\n"
            "Click **Check PnL** below to open the form and generate your custom card."
        ),
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Supported Chains",
        value="Base, Ethereum, Polygon, Arbitrum, Optimism, Blast, Zora, ApeChain",
        inline=False,
    )
    embed.set_footer(text="Powered by Reservoir Multi-Chain API")

    view = PnLLauncherView()
    await interaction.response.send_message(embed=embed, view=view)
