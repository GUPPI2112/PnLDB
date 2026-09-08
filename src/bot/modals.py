import discord
from discord import ui
from src.config import config


class PnLModal(ui.Modal, title="Check NFT PnL"):
    """
    Form modal allowing user to submit their wallet address,
    NFT contract address, and select their blockchain from a dropdown.
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

    chain_select = ui.Select(
        placeholder="Select Blockchain (Base, Ethereum, Polygon, Arbitrum...)",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Base",
                value="base",
                description="Base L2 (Coinbase)",
                default=True,
            ),
            discord.SelectOption(
                label="Ethereum",
                value="ethereum",
                description="Ethereum Mainnet",
            ),
            discord.SelectOption(
                label="Polygon",
                value="polygon",
                description="Polygon PoS Network",
            ),
            discord.SelectOption(
                label="Arbitrum",
                value="arbitrum",
                description="Arbitrum One L2",
            ),
            discord.SelectOption(
                label="Optimism",
                value="optimism",
                description="Optimism Mainnet L2",
            ),
            discord.SelectOption(
                label="Blast",
                value="blast",
                description="Blast Network",
            ),
            discord.SelectOption(
                label="Zora",
                value="zora",
                description="Zora Network",
            ),
            discord.SelectOption(
                label="ApeChain",
                value="apechain",
                description="ApeChain Network",
            ),
        ],
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer interaction immediately to prevent 3-second timeout
        await interaction.response.defer(thinking=True)

        selected_chain = self.chain_select.values[0] if self.chain_select.values else "base"

        from src.bot.commands.pnl import execute_pnl_check

        await execute_pnl_check(
            interaction=interaction,
            wallet_str=self.wallet_input.value.strip(),
            contract_str=self.contract_input.value.strip(),
            chain_str=selected_chain,
        )
