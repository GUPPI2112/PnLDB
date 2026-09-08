import discord
from typing import Dict, Optional


class PnLLauncherView(discord.ui.View):
    """
    Persistent Discord panel view with:
    - Green 'Check PnL' button
    - Blockchain dropdown selection below it (silent selection, no popup messages)
    """

    # Track selection per user
    user_selected_chains: Dict[int, str] = {}

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
        user_id = interaction.user.id
        selected_chain = self.user_selected_chains.get(user_id)

        if not selected_chain:
            await interaction.response.send_message(
                "Please select a blockchain network from the dropdown below first!",
                ephemeral=True,
            )
            return

        from src.bot.modals import PnLModal

        modal = PnLModal(selected_chain=selected_chain)
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
        # Save user selection silently without sending any confirmation popup
        self.user_selected_chains[interaction.user.id] = select.values[0]
        await interaction.response.defer()


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
