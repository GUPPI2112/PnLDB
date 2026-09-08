import discord
from typing import Optional


class PnLLauncherView(discord.ui.View):
    """
    Persistent Discord panel view with blockchain dropdown selection
    and the green 'Check PnL' button.
    """

    def __init__(self):
        super().__init__(timeout=None)
        self.selected_chain = "base"

    @discord.ui.select(
        placeholder="Select Blockchain (Default: Base)",
        custom_id="nft_pnl_chain_select_menu",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Base", value="base", description="Base L2 (ETH)"),
            discord.SelectOption(label="Ethereum", value="ethereum", description="Ethereum Mainnet (ETH)"),
            discord.SelectOption(label="Polygon", value="polygon", description="Polygon Network (POL)"),
            discord.SelectOption(label="Arbitrum", value="arbitrum", description="Arbitrum One (ETH)"),
            discord.SelectOption(label="Optimism", value="optimism", description="Optimism L2 (ETH)"),
            discord.SelectOption(label="Blast", value="blast", description="Blast L2 (ETH)"),
            discord.SelectOption(label="Zora", value="zora", description="Zora Network (ETH)"),
            discord.SelectOption(label="ApeChain", value="apechain", description="ApeChain (APE)"),
        ],
        row=0,
    )
    async def select_chain(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        self.selected_chain = select.values[0]
        # Acknowledge selection
        await interaction.response.send_message(
            f"Selected **{select.values[0].capitalize()}**! Now click **Check PnL** below to open the form.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Check PnL",
        style=discord.ButtonStyle.success,
        custom_id="nft_pnl_check_launcher_btn",
        row=1,
    )
    async def check_pnl_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        from src.bot.modals import PnLModal

        modal = PnLModal(selected_chain=self.selected_chain)
        await interaction.response.send_modal(modal)


class PnLResultView(discord.ui.View):
    """
    Action view accompanying the generated PnL card.
    Contains a direct 'Download Card' button with zero emojis.
    """

    def __init__(self, download_url: Optional[str] = None):
        super().__init__(timeout=None)
        if download_url:
            self.add_item(
                discord.ui.Button(
                    label="Download Card",
                    style=discord.ButtonStyle.link,
                    url=download_url,
                )
            )
