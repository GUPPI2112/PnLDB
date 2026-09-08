import discord
from discord import ui
from src.config import config


class PnLModal(ui.Modal, title="Check NFT PnL"):
    """
    Simple form modal for submitting wallet address, NFT contract, and chain.
    """

    wallet_input = ui.TextInput(
        label="Wallet Address",
        placeholder="0x1234...5678",
        style=discord.TextStyle.short,
        required=True,
        min_length=10,
        max_length=64,
    )

    contract_input = ui.TextInput(
        label="NFT Contract Address",
        placeholder="0xabcd...ef01",
        style=discord.TextStyle.short,
        required=True,
        min_length=10,
        max_length=64,
    )

    chain_input = ui.TextInput(
        label="Blockchain Network",
        placeholder="ethereum, base, polygon, arbitrum, optimism (default: ethereum)",
        style=discord.TextStyle.short,
        required=False,
        max_length=32,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer interaction immediately to prevent 3-second timeout
        await interaction.response.defer(thinking=True)

        chain_val = self.chain_input.value.strip() if self.chain_input.value else "ethereum"

        from src.bot.commands.pnl import execute_pnl_check

        await execute_pnl_check(
            interaction=interaction,
            wallet_str=self.wallet_input.value.strip(),
            contract_str=self.contract_input.value.strip(),
            chain_str=chain_val,
        )
