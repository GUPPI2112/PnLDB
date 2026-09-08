import discord
from src.config import config


class PnLModal(discord.ui.Modal, title="Check NFT PnL"):
    """
    Form modal allowing user to submit their wallet address,
    NFT contract address, and blockchain.
    """

    wallet_input = discord.ui.TextInput(
        label="Wallet Address",
        placeholder="0x1234...5678",
        style=discord.TextStyle.short,
        required=True,
        min_length=10,
        max_length=64,
    )

    contract_input = discord.ui.TextInput(
        label="NFT Contract Address",
        placeholder="0xabcd...ef01",
        style=discord.TextStyle.short,
        required=True,
        min_length=10,
        max_length=64,
    )

    chain_input = discord.ui.TextInput(
        label="Blockchain",
        placeholder="base, ethereum, polygon, arbitrum, optimism",
        default="base",
        style=discord.TextStyle.short,
        required=True,
        max_length=24,
    )

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
