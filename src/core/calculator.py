from typing import List, Optional
from src.core.models import ActivityEvent, ActivityType, PnLResult


def calculate_nft_pnl(
    events: List[ActivityEvent],
    wallet_address: str,
    contract_address: str,
    chain: str,
    currency_symbol: str = "ETH",
    floor_price_native: Optional[float] = None,
    native_price_usd: Optional[float] = None,
    ens_name: Optional[str] = None,
    collection_name: Optional[str] = None,
    collection_image_url: Optional[str] = None,
) -> PnLResult:
    """
    Calculates NFT portfolio PnL, ROI %, and inventory matching the template metrics:
    - Minted (Count & Total Native Spent)
    - Bought (Count & Total Native Spent)
    - Sold (Count & Total Native Received)
    - Holding (Count & Estimated Native Floor Value)
    - PNL (Net USD & Native PnL, ROI %)
    """
    norm_wallet = wallet_address.lower().strip()
    norm_contract = contract_address.lower().strip()

    minted_count = 0
    minted_native = 0.0
    bought_count = 0
    bought_native = 0.0
    sold_count = 0
    sold_native = 0.0
    transfers_in_count = 0
    transfers_out_count = 0

    for event in sorted(events, key=lambda e: e.timestamp):
        price = max(0.0, float(event.price_native or 0.0))

        if event.activity_type == ActivityType.MINT:
            minted_count += 1
            minted_native += price

        elif event.activity_type == ActivityType.BUY:
            bought_count += 1
            bought_native += price

        elif event.activity_type == ActivityType.SELL:
            sold_count += 1
            sold_native += price

        elif event.activity_type == ActivityType.TRANSFER_IN:
            transfers_in_count += 1

        elif event.activity_type == ActivityType.TRANSFER_OUT:
            transfers_out_count += 1

    held_count = max(0, (minted_count + bought_count + transfers_in_count) - (sold_count + transfers_out_count))
    
    floor = float(floor_price_native or 0.0)
    held_value_native = round(held_count * floor, 6)

    total_invested = round(minted_native + bought_native, 6)
    total_received = round(sold_native, 6)

    # Net PnL = Total Realized Sales + Current Unrealized Holding Value - Total Cost
    net_pnl_native = round((sold_native + held_value_native) - total_invested, 6)

    # Calculate ROI %
    if total_invested > 0:
        roi_percentage = round((net_pnl_native / total_invested) * 100.0, 2)
    elif total_invested == 0 and (sold_native + held_value_native) > 0:
        roi_percentage = 100.0
    else:
        roi_percentage = 0.0

    usd_rate = float(native_price_usd or 2500.0)
    net_pnl_usd = round(net_pnl_native * usd_rate, 2)

    is_profit = (net_pnl_native >= 0)

    return PnLResult(
        wallet_address=norm_wallet,
        contract_address=norm_contract,
        chain=chain.lower(),
        currency_symbol=currency_symbol,
        minted_count=minted_count,
        minted_native=round(minted_native, 6),
        bought_count=bought_count,
        bought_native=round(bought_native, 6),
        sold_count=sold_count,
        sold_native=round(sold_native, 6),
        held_count=held_count,
        held_value_native=held_value_native,
        total_invested=total_invested,
        total_received=total_received,
        net_pnl_native=net_pnl_native,
        net_pnl_usd=net_pnl_usd,
        roi_percentage=roi_percentage,
        is_profit=is_profit,
        ens_name=ens_name,
        collection_name=collection_name,
        collection_image_url=collection_image_url,
    )
