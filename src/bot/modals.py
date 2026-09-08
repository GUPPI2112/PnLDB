import discord
from discord import ui
from src.config import config


class PnLModal(ui.Modal, title="Check NFT PnL"):
    """
    Form modal allowing user to submit their wallet address,
    NFT contract address, and blockchain.
    """

    def __init__(self, selected_chain: str = "base"):
        super().__init__()
        self.selected_chain = selected_chain

        self.wallet_input = ui.TextInput(
            label="Wallet Address",
            placeholder="0x1234...5678",
            style=discord.TextStyle.short,
            required=True,
            min_length=10,
            max_length=64,
        )
        self.add_item(self.wallet_input)

        self.contract_input = ui.TextInput(
            label="NFT Contract Address",
            placeholder="0xabcd...ef01",
            style=discord.TextStyle.short,
            required=True,
            min_length=10,
            max_length=64,
        )
        self.add_item(self.contract_input)

        self.chain_input = ui.TextInput(
            label="Blockchain (Base, Ethereum, Polygon, Arbitrum...)",
            placeholder="base, ethereum, polygon, arbitrum, optimism, blast, zora",
            default=selected_chain,
            style=discord.TextStyle.short,
            required=True,
            max_length=32,
        )
        self.add_item(self.chain_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Defer interaction immediately to prevent 3-second timeout
        await interaction.response.defer(thinking=True)

        from src.bot.commands.pnl import execute_pnl_check

        await execute_pnl_check(
            interaction=interaction,
            wallet_str=self.wallet_input.value.strip(),
            contract_str=self.contract_input.value.strip(),
            chain_str=self.chain_input.value.strip(),
        )
