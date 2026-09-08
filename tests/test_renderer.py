import pytest
from PIL import Image
from src.core.models import CollectionMeta, PnLResult
from src.renderer.card_renderer import render_pnl_card


@pytest.mark.asyncio
async def test_render_profit_card():
    collection = CollectionMeta(
        contract_address="0x0000000000000000000000000000000000000001",
        name="CryptoPunks",
        symbol="PUNK",
        image_url=None,
        chain="Ethereum",
    )
    pnl = PnLResult(
        wallet_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        contract_address="0x0000000000000000000000000000000000000001",
        chain="ethereum",
        currency_symbol="ETH",
        total_invested=10.0,
        total_received=25.0,
        net_pnl=15.0,
        realized_pnl=15.0,
        roi_percentage=150.0,
        bought_count=2,
        sold_count=1,
        held_count=1,
        transfers_in_count=0,
        transfers_out_count=0,
        is_profit=True,
    )

    buf = await render_pnl_card(pnl, collection)
    assert buf is not None
    img = Image.open(buf)
    assert img.size == (1200, 675)
    assert img.format == "PNG"


@pytest.mark.asyncio
async def test_render_loss_card():
    collection = CollectionMeta(
        contract_address="0x0000000000000000000000000000000000000002",
        name="Loss Collection",
        symbol="LOSS",
        image_url=None,
        chain="Base",
    )
    pnl = PnLResult(
        wallet_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        contract_address="0x0000000000000000000000000000000000000002",
        chain="base",
        currency_symbol="ETH",
        total_invested=4.0,
        total_received=1.5,
        net_pnl=-2.5,
        realized_pnl=-2.5,
        roi_percentage=-62.5,
        bought_count=4,
        sold_count=2,
        held_count=2,
        transfers_in_count=0,
        transfers_out_count=0,
        is_profit=False,
    )

    buf = await render_pnl_card(pnl, collection)
    assert buf is not None
    img = Image.open(buf)
    assert img.size == (1200, 675)
    assert img.format == "PNG"
