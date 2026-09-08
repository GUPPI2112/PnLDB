import pytest
from PIL import Image
from src.core.models import CollectionMeta, PnLResult
from src.renderer.card_renderer import render_pnl_card


@pytest.mark.asyncio
async def test_render_profit_card_exact_format():
    collection = CollectionMeta(
        contract_address="0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
        name="WIF Outlaws",
        symbol="WIF",
        image_url=None,
        floor_price_native=0.237,
        native_price_usd=2500.0,
        chain="Ethereum",
    )
    pnl = PnLResult(
        wallet_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        contract_address="0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
        chain="ethereum",
        currency_symbol="ETH",
        minted_count=1,
        minted_native=0.016,
        bought_count=0,
        bought_native=0.0,
        sold_count=0,
        sold_native=0.0,
        held_count=1,
        held_value_native=0.237,
        total_invested=0.016,
        total_received=0.0,
        net_pnl_native=0.221,
        net_pnl_usd=550.0,
        roi_percentage=1383.0,
        is_profit=True,
        ens_name="srabon.eth",
        collection_name="WIF Outlaws",
    )

    buf = await render_pnl_card(pnl, collection)
    assert buf is not None
    img = Image.open(buf)
    assert img.size == (1024, 576)
    assert img.format == "PNG"


@pytest.mark.asyncio
async def test_render_loss_card():
    collection = CollectionMeta(
        contract_address="0x0000000000000000000000000000000000000002",
        name="Loss Collection",
        symbol="LOSS",
        image_url=None,
        floor_price_native=0.5,
        native_price_usd=2000.0,
        chain="Base",
    )
    pnl = PnLResult(
        wallet_address="0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        contract_address="0x0000000000000000000000000000000000000002",
        chain="base",
        currency_symbol="ETH",
        minted_count=0,
        minted_native=0.0,
        bought_count=2,
        bought_native=3.0,
        sold_count=2,
        sold_native=1.0,
        held_count=0,
        held_value_native=0.0,
        total_invested=3.0,
        total_received=1.0,
        net_pnl_native=-2.0,
        net_pnl_usd=-4000.0,
        roi_percentage=-66.67,
        is_profit=False,
    )

    buf = await render_pnl_card(pnl, collection)
    assert buf is not None
    img = Image.open(buf)
    assert img.size == (1024, 576)
    assert img.format == "PNG"
