import asyncio
import logging
from typing import Optional
import discord
from discord import app_commands
from src.config import config
from src.core.calculator import calculate_nft_pnl
from src.renderer.card_renderer import render_pnl_card
from src.services.chain_provider import MultiChainProvider
from src.bot.views import PnLResultView

logger = logging.getLogger(__name__)


def is_valid_address(address: str) -> bool:
    addr = address.strip()
    return len(addr) >= 2


async def execute_pnl_check(
    interaction: discord.Interaction,
    wallet_str: str,
    contract_str: str,
    chain_str: str,
):
    """
    Main processing handler for both Modal submission and Slash Command.
    Sends an ephemeral response so only the user sees it and can dismiss it.
    """
    wallet = wallet_str.strip()
    contract = contract_str.strip()
    chain_key = chain_str.lower().strip()

    # 1. Validation
    if not is_valid_address(wallet):
        await interaction.followup.send(
            f"Invalid wallet address: `{wallet}`. Please provide a valid address.",
            ephemeral=True,
        )
        return

    if not is_valid_address(contract):
        await interaction.followup.send(
            f"Invalid NFT contract address: `{contract}`. Please provide a valid contract address.",
            ephemeral=True,
        )
        return

    if chain_str in ("auto", "", None) or not config.get_chain_config(chain_key):
        if wallet.startswith("0x"):
            chain_cfg = config.get_chain_config("ethereum")
        elif wallet.startswith(("bc1", "1", "3")) and len(wallet) >= 26:
            chain_cfg = config.get_chain_config("bitcoin")
        else:
            chain_cfg = config.get_chain_config("solana")
    else:
        chain_cfg = config.get_chain_config(chain_key)

    if not chain_cfg:
        chain_cfg = config.get_chain_config("ethereum")

    # User profile data from Discord
    user_name = (
        getattr(interaction.user, "global_name", None)
        or getattr(interaction.user, "display_name", None)
        or getattr(interaction.user, "name", None)
        or "User"
    )
    avatar_url = interaction.user.display_avatar.url if interaction.user.display_avatar else None
    logger.info("Executing PnL check for %s (wallet: %s, contract: %s, chain: %s)", user_name, wallet, contract, chain_key)

    # 2. Fetch data via MultiChainProvider
    provider = MultiChainProvider()
    try:
        resolved_chain_name = chain_cfg.name
        
        # Step A: Resolve OpenSea URL / slug / contract into actual contract & collection metadata
        res_contract, res_chain, res_name, res_img, res_floor = await provider.resolve_nft_target(
            contract, default_chain=resolved_chain_name
        )
        target_contract = res_contract
        resolved_chain_name = res_chain
        resolved_chain_cfg = config.get_chain_config(resolved_chain_name) or chain_cfg

        # Step B: Get collection metadata
        collection_meta = await provider.get_collection_metadata(target_contract, resolved_chain_cfg.name)
        if res_name and (collection_meta.name.startswith("NFT (0x") or collection_meta.name.startswith("http")):
            collection_meta.name = res_name
        if res_img and not collection_meta.image_url:
            collection_meta.image_url = res_img
        if res_floor > 0 and collection_meta.floor_price_native <= 0:
            collection_meta.floor_price_native = res_floor

        # Step C: Get user activity
        activities = await provider.get_user_activity(wallet, target_contract, resolved_chain_cfg.name)

        # Cross-Chain Auto-Detection: If 0 activities on resolved chain, scan other EVM chains concurrently
        if not activities and target_contract.startswith("0x") and len(target_contract) == 42:
            candidate_chains = ["robinhood", "base", "ethereum", "arbitrum", "polygon", "optimism", "blast", "zora", "apechain"]
            targets = [c for c in candidate_chains if c != resolved_chain_cfg.name and config.get_chain_config(c)]

            async def probe_chain(c_name: str):
                try:
                    c_acts = await provider.get_user_activity(wallet, target_contract, c_name)
                    c_meta = await provider.get_collection_metadata(target_contract, c_name)
                    return c_name, c_acts, c_meta
                except Exception:
                    return c_name, [], None

            probe_results = await asyncio.gather(*[probe_chain(t) for t in targets])
            for c_name, c_acts, c_meta in probe_results:
                if c_acts:
                    activities = c_acts
                    resolved_chain_cfg = config.get_chain_config(c_name) or resolved_chain_cfg
                    if c_meta and not c_meta.name.startswith("NFT (0x"):
                        collection_meta = c_meta
                    logger.info("Auto-detected active chain %s with %d activities for contract %s", c_name, len(c_acts), target_contract)
                    break
                elif collection_meta.name.startswith("NFT (0x") and c_meta and not c_meta.name.startswith("NFT (0x"):
                    resolved_chain_cfg = config.get_chain_config(c_name) or resolved_chain_cfg
                    collection_meta = c_meta

        # 3. Calculate PnL matching reference template
        pnl_result = calculate_nft_pnl(
            events=activities,
            wallet_address=wallet,
            contract_address=target_contract,
            chain=resolved_chain_cfg.name,
            currency_symbol=resolved_chain_cfg.currency_symbol,
            floor_price_native=collection_meta.floor_price_native,
            native_price_usd=collection_meta.native_price_usd,
            user_display_name=user_name,
            user_avatar_url=avatar_url,
            ens_name=None,
            collection_name=collection_meta.name,
            collection_image_url=collection_meta.image_url,
        )

        # 4. Render PnL Card with Discord User Avatar & Name
        image_buffer = await render_pnl_card(pnl_result, collection_meta)

        # 5. Send ephemeral Discord response with image and Download Card button
        file = discord.File(fp=image_buffer, filename="nft_pnl.png")
        
        sent_msg = await interaction.followup.send(
            file=file,
            ephemeral=True,
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


@app_commands.command(name="pnl", description="Generate an NFT PnL card (Auto-detects blockchain)")
@app_commands.describe(
    wallet="Your wallet address (0x... or SOL/BTC)",
    contract="The NFT contract address or collection ID",
    chain="Optional blockchain network (Auto-detected if omitted)",
)
@app_commands.choices(
    chain=[
        app_commands.Choice(name="Auto-Detect", value="auto"),
        app_commands.Choice(name="Ethereum", value="ethereum"),
        app_commands.Choice(name="Base", value="base"),
        app_commands.Choice(name="Solana", value="solana"),
        app_commands.Choice(name="Bitcoin (Ordinals)", value="bitcoin"),
        app_commands.Choice(name="Robinhood", value="robinhood"),
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
    chain: Optional[app_commands.Choice[str]] = None,
):
    await interaction.response.defer(thinking=True, ephemeral=True)
    chain_val = chain.value if chain else "auto"
    await execute_pnl_check(
        interaction=interaction,
        wallet_str=wallet,
        contract_str=contract,
        chain_str=chain_val,
    )
