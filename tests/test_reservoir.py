from src.core.models import ActivityType
from src.services.reservoir import ReservoirProvider

WALLET = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"


def test_parse_buy_activity():
    provider = ReservoirProvider()
    raw_act = {
        "type": "sale",
        "fromAddress": "0x1111111111111111111111111111111111111111",
        "toAddress": WALLET,
        "token": {"tokenId": "420"},
        "txHash": "0xabc123",
        "timestamp": 1690000000,
        "price": {
            "amount": {
                "native": 0.45,
                "usd": 900.0,
            }
        },
        "order": {"source": {"name": "OpenSea"}},
    }

    event = provider._parse_activity_item(raw_act, WALLET)
    assert event is not None
    assert event.activity_type == ActivityType.BUY
    assert event.price_native == 0.45
    assert event.token_id == "420"
    assert event.order_source == "OpenSea"


def test_parse_sell_activity():
    provider = ReservoirProvider()
    raw_act = {
        "type": "sale",
        "fromAddress": WALLET,
        "toAddress": "0x2222222222222222222222222222222222222222",
        "token": {"tokenId": "420"},
        "txHash": "0xdef456",
        "timestamp": 1690005000,
        "price": {
            "amount": {
                "native": 1.25,
                "usd": 2500.0,
            }
        },
        "order": {"source": {"name": "Blur"}},
    }

    event = provider._parse_activity_item(raw_act, WALLET)
    assert event is not None
    assert event.activity_type == ActivityType.SELL
    assert event.price_native == 1.25
    assert event.token_id == "420"
    assert event.order_source == "Blur"


def test_parse_mint_activity():
    provider = ReservoirProvider()
    raw_act = {
        "type": "mint",
        "fromAddress": "0x0000000000000000000000000000000000000000",
        "toAddress": WALLET,
        "token": {"tokenId": "1"},
        "txHash": "0xmint123",
        "timestamp": 1690000000,
        "price": {
            "amount": {
                "native": 0.05,
            }
        },
    }

    event = provider._parse_activity_item(raw_act, WALLET)
    assert event is not None
    assert event.activity_type == ActivityType.MINT
    assert event.price_native == 0.05
    assert event.token_id == "1"


def test_parse_transfer_in_and_out():
    provider = ReservoirProvider()
    # Transfer In
    act_in = {
        "type": "transfer",
        "fromAddress": "0x9999999999999999999999999999999999999999",
        "toAddress": WALLET,
        "tokenId": "777",
        "txHash": "0xtx1",
        "timestamp": 1690000000,
    }
    event_in = provider._parse_activity_item(act_in, WALLET)
    assert event_in is not None
    assert event_in.activity_type == ActivityType.TRANSFER_IN
    assert event_in.token_id == "777"
    assert event_in.price_native == 0.0

    # Transfer Out
    act_out = {
        "type": "transfer",
        "fromAddress": WALLET,
        "toAddress": "0x9999999999999999999999999999999999999999",
        "tokenId": "777",
        "txHash": "0xtx2",
        "timestamp": 1690001000,
    }
    event_out = provider._parse_activity_item(act_out, WALLET)
    assert event_out is not None
    assert event_out.activity_type == ActivityType.TRANSFER_OUT
