import discord
from typing import Optional


class PnLLauncherView(discord.ui.View):
    """
    Persistent Discord panel view.
    Selecting any blockchain from the dropdown opens the modal IMMEDIATELY.
    Clicking 'Check PnL' also opens the modal directly.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Check PnL",
        style=discord.ButtonStyle.success,
        custom_id="nft_pnl_check_launcher_btn",
        row=0,
    )
    async def check_pnl_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        from src.bot.modals import PnLModal

        # Defaults to Ethereum on direct button click
        modal = PnLModal(selected_chain="ethereum")
        await interaction.response.send_modal(modal)

    @discord.ui.select(
        placeholder="Select Blockchain Network...",
        custom_id="nft_pnl_chain_select_menu",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Ethereum", value="ethereum", description="Ethereum Mainnet (ETH)"),
            discord.SelectOption(label="Base", value="base", description="Base L2 (ETH)"),
            discord.SelectOption(label="Solana", value="solana", description="Solana Network (SOL)"),
            discord.SelectOption(label="Bitcoin", value="bitcoin", description="Bitcoin Ordinals (BTC)"),
            discord.SelectOption(label="Robinhood", value="robinhood", description="Robinhood / Arbitrum (ETH)"),
            discord.SelectOption(label="Polygon", value="polygon", description="Polygon Network (POL)"),
            discord.SelectOption(label="Arbitrum", value="arbitrum", description="Arbitrum One (ETH)"),
            discord.SelectOption(label="Optimism", value="optimism", description="Optimism L2 (ETH)"),
            discord.SelectOption(label="Blast", value="blast", description="Blast L2 (ETH)"),
            discord.SelectOption(label="Zora", value="zora", description="Zora Network (ETH)"),
            discord.SelectOption(label="ApeChain", value="apechain", description="ApeChain (APE)"),
        ],
        row=1,
    )
    async def select_chain(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ):
        from src.bot.modals import PnLModal

        chosen = select.values[0]
        # Open modal immediately for the chosen chain in 1 click!
        modal = PnLModal(selected_chain=chosen)
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
