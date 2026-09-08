import pytest
from src.core.models import ActivityEvent, ActivityType
from src.core.calculator import calculate_nft_pnl

WALLET = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"
CONTRACT = "0xbd3531da5cf5857e7cfaa92426877b022e612cf8"


def test_profitable_trades():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="101",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=1.0,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="102",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=1.0,
        ),
        ActivityEvent(
            tx_hash="0x3",
            timestamp=3000,
            token_id="101",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=3.0,
        ),
    ]

    res = calculate_nft_pnl(events, WALLET, CONTRACT, "base", "ETH")

    assert res.total_invested == 2.0
    assert res.total_received == 3.0
    assert res.net_pnl == 1.0
    assert res.roi_percentage == 50.0
    assert res.bought_count == 2
    assert res.sold_count == 1
    assert res.held_count == 1
    assert res.is_profit is True
    assert res.formatted_pnl == "+1.0000 ETH"
    assert res.formatted_roi == "+50.00%"


def test_loss_trades():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="10",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=2.5,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="10",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=1.0,
        ),
    ]

    res = calculate_nft_pnl(events, WALLET, CONTRACT, "ethereum", "ETH")

    assert res.total_invested == 2.5
    assert res.total_received == 1.0
    assert res.net_pnl == -1.5
    assert res.roi_percentage == -60.0
    assert res.bought_count == 1
    assert res.sold_count == 1
    assert res.held_count == 0
    assert res.is_profit is False
    assert res.formatted_pnl == "-1.5000 ETH"
    assert res.formatted_roi == "-60.00%"


def test_free_mint_or_airdrop_flip():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="42",
            activity_type=ActivityType.MINT,
            from_address="0x0000000000000000000000000000000000000000",
            to_address=WALLET,
            price_native=0.0,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="42",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=1.2,
        ),
    ]

    res = calculate_nft_pnl(events, WALLET, CONTRACT, "base", "ETH")

    assert res.total_invested == 0.0
    assert res.total_received == 1.2
    assert res.net_pnl == 1.2
    assert res.roi_percentage == 100.0
    assert res.bought_count == 1
    assert res.sold_count == 1
    assert res.held_count == 0
    assert res.is_profit is True


def test_only_buys_held_inventory():
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="1",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=0.5,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="2",
            activity_type=ActivityType.BUY,
            from_address="0xseller",
            to_address=WALLET,
            price_native=0.7,
        ),
    ]

    res = calculate_nft_pnl(events, WALLET, CONTRACT, "base", "ETH")

    assert res.total_invested == 1.2
    assert res.total_received == 0.0
    assert res.net_pnl == -1.2
    assert res.bought_count == 2
    assert res.sold_count == 0
    assert res.held_count == 2
    assert res.is_profit is False


def test_transfers_and_gifts():
    events = [
        # Transferred in 2 NFTs (gift / airdrop)
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="5",
            activity_type=ActivityType.TRANSFER_IN,
            from_address="0xfriend",
            to_address=WALLET,
            price_native=0.0,
        ),
        ActivityEvent(
            tx_hash="0x2",
            timestamp=2000,
            token_id="6",
            activity_type=ActivityType.TRANSFER_IN,
            from_address="0xfriend",
            to_address=WALLET,
            price_native=0.0,
        ),
        # Sold 1 of the gifted NFTs
        ActivityEvent(
            tx_hash="0x3",
            timestamp=3000,
            token_id="5",
            activity_type=ActivityType.SELL,
            from_address=WALLET,
            to_address="0xbuyer",
            price_native=0.8,
        ),
        # Transferred out the other to cold storage
        ActivityEvent(
            tx_hash="0x4",
            timestamp=4000,
            token_id="6",
            activity_type=ActivityType.TRANSFER_OUT,
            from_address=WALLET,
            to_address="0xcoldwallet",
            price_native=0.0,
        ),
    ]

    res = calculate_nft_pnl(events, WALLET, CONTRACT, "polygon", "POL")

    assert res.total_invested == 0.0
    assert res.total_received == 0.8
    assert res.net_pnl == 0.8
    assert res.bought_count == 0
    assert res.sold_count == 1
    assert res.transfers_in_count == 2
    assert res.transfers_out_count == 1
    assert res.held_count == 0
    assert res.is_profit is True


def test_empty_events():
    res = calculate_nft_pnl([], WALLET, CONTRACT, "arbitrum", "ETH")

    assert res.total_invested == 0.0
    assert res.total_received == 0.0
    assert res.net_pnl == 0.0
    assert res.roi_percentage == 0.0
    assert res.bought_count == 0
    assert res.sold_count == 0
    assert res.held_count == 0
    assert res.is_profit is True


def test_address_normalization():
    upper_wallet = "0xD8DA6BF26964AF9D7EED9E03E53415D37AA96045"
    events = [
        ActivityEvent(
            tx_hash="0x1",
            timestamp=1000,
            token_id="1",
            activity_type=ActivityType.BUY,
            from_address="0xSELLER",
            to_address=upper_wallet,
            price_native=1.0,
        ),
    ]

    res = calculate_nft_pnl(events, upper_wallet, CONTRACT, "base", "ETH")
    assert res.wallet_address == upper_wallet.lower()
    assert res.bought_count == 1
