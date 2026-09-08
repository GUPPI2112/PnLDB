import discord
from typing import Optional


class PnLLauncherView(discord.ui.View):
    """
    Persistent Discord view containing the 'Check PnL' button.
    Clicking this opens the PnLModal form.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Check PnL",
        style=discord.ButtonStyle.primary,
        custom_id="nft_pnl_check_launcher_btn",
    )
    async def check_pnl_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Lazy import to avoid circular dependency
        from src.bot.modals import PnLModal

        modal = PnLModal()
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
