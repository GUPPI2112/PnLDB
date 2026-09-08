import discord
from discord import ui


class PnLModal(ui.Modal):
    """
    Clean 2-field form modal for Wallet and Contract address.
    Displays the selected blockchain in the title.
    """

    def __init__(self, selected_chain: str = "ethereum"):
        display_chain = selected_chain.capitalize()
        super().__init__(title=f"Check NFT PnL ({display_chain})")
        self.selected_chain = selected_chain

        self.wallet_input = ui.TextInput(
            label="Wallet Address",
            placeholder="0x1234...5678 (or SOL/BTC address)",
            style=discord.TextStyle.short,
            required=True,
            min_length=3,
            max_length=80,
        )
        self.add_item(self.wallet_input)

        self.contract_input = ui.TextInput(
            label="NFT Contract Address / Collection ID",
            placeholder="0xabcd...ef01 (or collection name e.g. MV3)",
            style=discord.TextStyle.short,
            required=True,
            min_length=2,
            max_length=80,
        )
        self.add_item(self.contract_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Defer ephemerally so the result is private and has 'Dismiss message'
        await interaction.response.defer(thinking=True, ephemeral=True)

        from src.bot.commands.pnl import execute_pnl_check

        await execute_pnl_check(
            interaction=interaction,
            wallet_str=self.wallet_input.value.strip(),
            contract_str=self.contract_input.value.strip(),
            chain_str=self.selected_chain,
        )
