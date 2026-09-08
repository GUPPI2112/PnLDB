import discord
from discord import ui


class PnLModal(ui.Modal, title="Check NFT PnL"):
    """
    Clean 2-field form modal for Wallet and Contract address.
    Blockchain network is selected from the dropdown beforehand.
    """

    def __init__(self, selected_chain: str):
        super().__init__()
        self.selected_chain = selected_chain

        self.wallet_input = ui.TextInput(
            label="Wallet Address",
            placeholder="0x1234...5678 (or SOL/BTC address)",
            style=discord.TextStyle.short,
            required=True,
            min_length=4,
            max_length=80,
        )
        self.add_item(self.wallet_input)

        self.contract_input = ui.TextInput(
            label="NFT Contract Address / Collection ID",
            placeholder="0xabcd...ef01 (or collection name)",
            style=discord.TextStyle.short,
            required=True,
            min_length=4,
            max_length=80,
        )
        self.add_item(self.contract_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Defer interaction immediately to prevent 3-second timeout
        await interaction.response.defer(thinking=True)

        from src.bot.commands.pnl import execute_pnl_check

        await execute_pnl_check(
            interaction=interaction,
            wallet_str=self.wallet_input.value.strip(),
            contract_str=self.contract_input.value.strip(),
            chain_str=self.selected_chain,
        )
