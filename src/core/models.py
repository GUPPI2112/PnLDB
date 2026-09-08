from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ActivityType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    MINT = "mint"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


@dataclass
class ActivityEvent:
    tx_hash: str
    timestamp: int
    token_id: str
    activity_type: ActivityType
    from_address: str
    to_address: str
    price_native: float
    price_usd: Optional[float] = None
    order_source: Optional[str] = None


@dataclass
class CollectionMeta:
    contract_address: str
    name: str
    symbol: str
    image_url: Optional[str] = None
    floor_price_native: Optional[float] = None
    chain: str = "base"


@dataclass
class PnLResult:
    wallet_address: str
    contract_address: str
    chain: str
    currency_symbol: str
    total_invested: float
    total_received: float
    net_pnl: float
    realized_pnl: float
    roi_percentage: float
    bought_count: int
    sold_count: int
    held_count: int
    transfers_in_count: int
    transfers_out_count: int
    is_profit: bool

    @property
    def shortened_wallet(self) -> str:
        w = self.wallet_address
        if len(w) >= 10:
            return f"{w[:6]}...{w[-4:]}"
        return w

    @property
    def shortened_contract(self) -> str:
        c = self.contract_address
        if len(c) >= 10:
            return f"{c[:6]}...{c[-4:]}"
        return c

    @property
    def formatted_pnl(self) -> str:
        sign = "+" if self.net_pnl >= 0 else ""
        return f"{sign}{self.net_pnl:.4f} {self.currency_symbol}"

    @property
    def formatted_roi(self) -> str:
        sign = "+" if self.roi_percentage >= 0 else ""
        return f"{sign}{self.roi_percentage:.2f}%"

    @property
    def formatted_invested(self) -> str:
        return f"{self.total_invested:.4f} {self.currency_symbol}"

    @property
    def formatted_received(self) -> str:
        return f"{self.total_received:.4f} {self.currency_symbol}"
