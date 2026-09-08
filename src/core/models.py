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
    native_price_usd: Optional[float] = None
    chain: str = "base"


@dataclass
class PnLResult:
    wallet_address: str
    contract_address: str
    chain: str
    currency_symbol: str
    
    # Counts
    minted_count: int
    minted_native: float
    bought_count: int
    bought_native: float
    sold_count: int
    sold_native: float
    held_count: int
    held_value_native: float
    
    # Financials
    total_invested: float
    total_received: float
    net_pnl_native: float
    net_pnl_usd: float
    roi_percentage: float
    is_profit: bool
    
    # User Profile Info
    user_display_name: Optional[str] = None
    user_avatar_url: Optional[str] = None
    ens_name: Optional[str] = None
    collection_name: Optional[str] = None
    collection_image_url: Optional[str] = None

    @property
    def shortened_wallet(self) -> str:
        if self.ens_name:
            return self.ens_name
        w = self.wallet_address
        if len(w) >= 10:
            return f"{w[:6]}...{w[-4:]}"
        return w

    @property
    def display_user(self) -> str:
        return self.user_display_name or self.ens_name or self.shortened_wallet

    @property
    def formatted_usd_pnl(self) -> str:
        sign = "+" if self.net_pnl_usd >= 0 else "-"
        return f"{sign}${abs(self.net_pnl_usd):,.0f}"

    @property
    def formatted_native_pnl(self) -> str:
        sign = "+" if self.net_pnl_native >= 0 else "-"
        return f"{sign}{abs(self.net_pnl_native):.3f}"
