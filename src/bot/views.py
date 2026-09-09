import discord
from typing import Optional


class PnLLauncherView(discord.ui.View):
    """
    Persistent Discord panel view.
    Clean single-click 'Check PnL' button that auto-detects the blockchain.
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

        modal = PnLModal(selected_chain="auto")
        await interaction.response.send_modal(modal)


class PnLResultView(discord.ui.View):
    """
    Action view accompanying the generated PnL card.
    Contains 'Download Card' link button and a 'Dismiss' button.
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

    @discord.ui.button(
        label="Dismiss",
        style=discord.ButtonStyle.secondary,
        custom_id="nft_pnl_dismiss_btn",
    )
    async def dismiss_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except Exception:
            pass

