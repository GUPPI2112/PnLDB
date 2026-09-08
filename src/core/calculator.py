from collections import defaultdict, deque
from typing import Dict, List, Optional
from src.core.models import ActivityEvent, ActivityType, PnLResult


def calculate_nft_pnl(
    events: List[ActivityEvent],
    wallet_address: str,
    contract_address: str,
    chain: str,
    currency_symbol: str = "ETH",
) -> PnLResult:
    """
    Calculates NFT PnL, ROI %, cash flows, and inventory counts for a wallet
    and specific NFT contract.

    Handles buys, mints, sales, and transfers with FIFO cost-basis tracking.
    """
    norm_wallet = wallet_address.lower().strip()
    norm_contract = contract_address.lower().strip()

    # Sort events chronologically (oldest first)
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    total_invested = 0.0
    total_received = 0.0
    bought_count = 0
    sold_count = 0
    transfers_in_count = 0
    transfers_out_count = 0

    # Token inventory tracking for FIFO cost basis: token_id -> deque of prices
    token_cost_basis: Dict[str, deque] = defaultdict(deque)
    realized_cost_basis_sold = 0.0
    realized_proceeds_sold = 0.0

    for event in sorted_events:
        price = max(0.0, float(event.price_native or 0.0))
        token_id = str(event.token_id) if event.token_id is not None else ""

        if event.activity_type == ActivityType.MINT:
            total_invested += price
            bought_count += 1
            if token_id:
                token_cost_basis[token_id].append(price)

        elif event.activity_type == ActivityType.BUY:
            total_invested += price
            bought_count += 1
            if token_id:
                token_cost_basis[token_id].append(price)

        elif event.activity_type == ActivityType.SELL:
            total_received += price
            sold_count += 1
            realized_proceeds_sold += price

            # Resolve FIFO cost basis for this token
            if token_id and len(token_cost_basis[token_id]) > 0:
                cost = token_cost_basis[token_id].popleft()
                realized_cost_basis_sold += cost
            else:
                # Gifted / airdropped or unindexed previous buy -> 0 cost basis
                pass

        elif event.activity_type == ActivityType.TRANSFER_IN:
            transfers_in_count += 1
            if token_id:
                # Transfer in without purchase price = 0 cost basis
                token_cost_basis[token_id].append(0.0)

        elif event.activity_type == ActivityType.TRANSFER_OUT:
            transfers_out_count += 1
            if token_id and len(token_cost_basis[token_id]) > 0:
                token_cost_basis[token_id].popleft()

    net_pnl = total_received - total_invested
    realized_pnl = realized_proceeds_sold - realized_cost_basis_sold

    # Held count cannot be negative
    held_count = max(0, (bought_count + transfers_in_count) - (sold_count + transfers_out_count))

    # Calculate ROI %
    if total_invested > 0:
        roi_percentage = (net_pnl / total_invested) * 100.0
    elif total_invested == 0 and total_received > 0:
        # Free mint / gifted flip -> 100% gain
        roi_percentage = 100.0
    else:
        roi_percentage = 0.0

    return PnLResult(
        wallet_address=norm_wallet,
        contract_address=norm_contract,
        chain=chain.lower(),
        currency_symbol=currency_symbol,
        total_invested=round(total_invested, 6),
        total_received=round(total_received, 6),
        net_pnl=round(net_pnl, 6),
        realized_pnl=round(realized_pnl, 6),
        roi_percentage=round(roi_percentage, 2),
        bought_count=bought_count,
        sold_count=sold_count,
        held_count=held_count,
        transfers_in_count=transfers_in_count,
        transfers_out_count=transfers_out_count,
        is_profit=(net_pnl >= 0),
    )
