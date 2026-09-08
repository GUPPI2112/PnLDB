import logging
import re
import discord
from discord import app_commands
from src.config import config
from src.core.calculator import calculate_nft_pnl
from src.renderer.card_renderer import render_pnl_card
from src.services.reservoir import ReservoirProvider
from src.bot.views import PnLResultView

logger = logging.getLogger(__name__)

ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


def is_valid_address(address: str) -> bool:
    return bool(ETH_ADDRESS_PATTERN.match(address.strip()))


async def execute_pnl_check(
    interaction: discord.Interaction,
    wallet_str: str,
    contract_str: str,
    chain_str: str,
):
    """
    Main processing handler for both Modal submission and Slash Command.
    """
    wallet = wallet_str.strip()
    contract = contract_str.strip()
    chain_key = chain_str.lower().strip()

    # 1. Validation
    if not is_valid_address(wallet):
        await interaction.followup.send(
            f"Invalid wallet address: `{wallet}`. Please provide a valid 42-character EVM address (e.g. `0x1234...`).",
            ephemeral=True,
        )
        return

    if not is_valid_address(contract):
        await interaction.followup.send(
            f"Invalid NFT contract address: `{contract}`. Please provide a valid 42-character EVM address (e.g. `0xabcd...`).",
            ephemeral=True,
        )
        return

    chain_cfg = config.get_chain_config(chain_key)
    if not chain_cfg:
        supported = config.supported_chains_display()
        await interaction.followup.send(
            f"Unsupported chain: `{chain_str}`.\nSupported chains: {supported}",
            ephemeral=True,
        )
        return

    # 2. Fetch data from Reservoir
    provider = ReservoirProvider()
    try:
        collection_meta = await provider.get_collection_metadata(contract, chain_cfg.name)
        activities = await provider.get_user_activity(wallet, contract, chain_cfg.name)

        if not activities:
            short_w = f"{wallet[:6]}...{wallet[-4:]}"
            await interaction.followup.send(
                f"No transaction or trading activity found for wallet `{short_w}` in collection **{collection_meta.name}** on **{chain_cfg.display_name}**.",
                ephemeral=False,
            )
            return

        # 3. Calculate PnL matching reference template
        pnl_result = calculate_nft_pnl(
            events=activities,
            wallet_address=wallet,
            contract_address=contract,
            chain=chain_cfg.name,
            currency_symbol=chain_cfg.currency_symbol,
            floor_price_native=collection_meta.floor_price_native,
            native_price_usd=collection_meta.native_price_usd,
            ens_name=None,
            collection_name=collection_meta.name,
            collection_image_url=collection_meta.image_url,
        )

        # 4. Render PnL Card
        image_buffer = await render_pnl_card(pnl_result, collection_meta)

        # 5. Send Discord response with image and Download Card button
        file = discord.File(fp=image_buffer, filename="nft_pnl.png")
        
        sent_msg = await interaction.followup.send(
            file=file,
            wait=True,
        )

        # Add Download Card button linking to the full-resolution image CDN
        if sent_msg.attachments:
            cdn_url = sent_msg.attachments[0].url
            result_view = PnLResultView(download_url=cdn_url)
            await sent_msg.edit(view=result_view)

    except Exception as e:
        logger.exception("Failed to generate NFT PnL for %s (%s) on %s", wallet, contract, chain_key)
        await interaction.followup.send(
            f"An error occurred while generating the PnL card: {str(e)}",
            ephemeral=True,
        )
    finally:
        await provider.close()


@app_commands.command(name="pnl", description="Generate an NFT PnL card for a wallet and collection")
@app_commands.describe(
    wallet="Your EVM wallet address (0x...)",
    contract="The NFT contract address (0x...)",
    chain="The blockchain network (base, ethereum, polygon, arbitrum, optimism)",
)
@app_commands.choices(
    chain=[
        app_commands.Choice(name="Base", value="base"),
        app_commands.Choice(name="Ethereum", value="ethereum"),
        app_commands.Choice(name="Polygon", value="polygon"),
        app_commands.Choice(name="Arbitrum", value="arbitrum"),
        app_commands.Choice(name="Optimism", value="optimism"),
        app_commands.Choice(name="Blast", value="blast"),
        app_commands.Choice(name="Zora", value="zora"),
        app_commands.Choice(name="ApeChain", value="apechain"),
    ]
)
async def pnl_command(
    interaction: discord.Interaction,
    wallet: str,
    contract: str,
    chain: app_commands.Choice[str],
):
    await interaction.response.defer(thinking=True)
    await execute_pnl_check(
        interaction=interaction,
        wallet_str=wallet,
        contract_str=contract,
        chain_str=chain.value,
    )
