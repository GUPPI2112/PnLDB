from src.core.models import ActivityEvent, ActivityType
from src.core.calculator import calculate_nft_pnl

WALLET = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
CONTRACT = "0xbd3531da5cf5857e7cfaa92426877b022e612cf8"


def test_profitable_mint_and_hold():
    # Mint 1 at 0.016 ETH, holding 1 with floor 0.237 ETH
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="101",
            activity_type=ActivityType.MINT,
            from_address="0x0000000000000000000000000000000000000000",
            to_address=WALLET,
            price_native=0.016,
        ),
    ]

    res = calculate_nft_pnl(
        events=events,
        wallet_address=WALLET,
        contract_address=CONTRACT,
        chain="ethereum",
        currency_symbol="ETH",
        floor_price_native=0.237,
        native_price_usd=2500.0,
        ens_name="srabon.eth",
        collection_name="WIF Outlaws",
    )

    assert res.minted_count == 1
    assert res.minted_native == 0.016
    assert res.bought_count == 0
    assert res.bought_native == 0.0
    assert res.sold_count == 0
    assert res.sold_native == 0.0
    assert res.held_count == 1
    assert res.held_value_native == 0.237
    assert res.net_pnl_native == 0.221
    assert res.roi_percentage == 1381.25
    assert res.net_pnl_usd == 552.5
    assert res.is_profit is True
    assert res.display_user == "srabon.eth"


def test_profitable_buy_and_sell():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="1",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=1.0,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="1",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=2.5,
        ),
    ]

    res = calculate_nft_pnl(
        events=events,
        wallet_address=WALLET,
        contract_address=CONTRACT,
        chain="base",
        currency_symbol="ETH",
        floor_price_native=1.2,
        native_price_usd=2000.0,
    )

    assert res.bought_count == 1
    assert res.bought_native == 1.0
    assert res.sold_count == 1
    assert res.sold_native == 2.5
    assert res.held_count == 0
    assert res.net_pnl_native == 1.5
    assert res.roi_percentage == 150.0
    assert res.net_pnl_usd == 3000.0
    assert res.is_profit is True


def test_loss_scenario():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="5",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=3.0,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="5",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=1.2,
        ),
    ]

    res = calculate_nft_pnl(
        events=events,
        wallet_address=WALLET,
        contract_address=CONTRACT,
        chain="base",
        currency_symbol="ETH",
        floor_price_native=1.0,
        native_price_usd=2000.0,
    )

    assert res.bought_count == 1
    assert res.sold_count == 1
    assert res.held_count == 0
    assert res.net_pnl_native == -1.8
    assert res.roi_percentage == -60.0
    assert res.net_pnl_usd == -3600.0
    assert res.is_profit is False
    assert res.formatted_usd_pnl == "-$3,600"


def test_free_airdrop():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="99",
            activity_type=ActivityType.TRANSFER_IN,
            from_address="0xaura",
            to_address=WALLET,
            price_native=0.0,
        ),
    ]

    res = calculate_nft_pnl(
        events=events,
        wallet_address=WALLET,
        contract_address=CONTRACT,
        chain="polygon",
        currency_symbol="POL",
        floor_price_native=0.5,
        native_price_usd=1.0,
    )

    assert res.held_count == 1
    assert res.held_value_native == 0.5
    assert res.net_pnl_native == 0.5
    assert res.roi_percentage == 100.0
    assert res.is_profit is True
