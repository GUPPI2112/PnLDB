import logging
from typing import List, Optional
import aiohttp
from src.config import config
from src.core.models import ActivityEvent, ActivityType, CollectionMeta
from src.services.base_provider import NFTDataProvider

logger = logging.getLogger(__name__)


class ReservoirProvider(NFTDataProvider):
    """
    Data provider using Reservoir's decentralized multi-chain NFT API.
    Indexes decentralized marketplace sales (OpenSea, Blur, MagicEden, LooksRare, Seaport, etc.)
    and direct mints across Ethereum, Base, Polygon, Arbitrum, Optimism, etc.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.RESERVOIR_API_KEY
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Accept": "*/*",
                "User-Agent": "NFT-PnL-Bot/1.0",
            }
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_collection_metadata(
        self, contract_address: str, chain: str
    ) -> CollectionMeta:
        chain_cfg = config.get_chain_config(chain)
        if not chain_cfg:
            raise ValueError(
                f"Unsupported chain: '{chain}'. Supported: {config.supported_chains_display()}"
            )

        url = f"https://{chain_cfg.reservoir_host}/collections/v7"
        params = {"id": contract_address.lower()}

        session = await self._get_session()
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    collections = data.get("collections", [])
                    if collections:
                        col = collections[0]
                        name = col.get("name") or f"Collection ({contract_address[:6]}...)"
                        symbol = col.get("symbol") or ""
                        image = col.get("image")
                        if not image and col.get("sampleImages"):
                            image = col.get("sampleImages")[0]
                        
                        floor_obj = col.get("floorAsk", {}).get("price", {}).get("amount", {})
                        floor_native = floor_obj.get("native") or floor_obj.get("decimal")
                        floor_usd = floor_obj.get("usd")

                        native_usd_rate = None
                        if floor_native and floor_usd and float(floor_native) > 0:
                            native_usd_rate = float(floor_usd) / float(floor_native)

                        return CollectionMeta(
                            contract_address=contract_address.lower(),
                            name=name,
                            symbol=symbol,
                            image_url=image,
                            floor_price_native=float(floor_native) if floor_native is not None else 0.0,
                            native_price_usd=native_usd_rate,
                            chain=chain_cfg.display_name,
                        )
        except Exception as e:
            logger.error("Error fetching collection metadata for %s on %s: %s", contract_address, chain, e)

        return CollectionMeta(
            contract_address=contract_address.lower(),
            name=f"Collection ({contract_address[:6]}...{contract_address[-4:]})",
            symbol="NFT",
            image_url=None,
            floor_price_native=0.0,
            native_price_usd=2500.0,
            chain=chain_cfg.display_name,
        )

    async def get_user_activity(
        self, wallet_address: str, contract_address: str, chain: str
    ) -> List[ActivityEvent]:
        chain_cfg = config.get_chain_config(chain)
        if not chain_cfg:
            raise ValueError(
                f"Unsupported chain: '{chain}'. Supported: {config.supported_chains_display()}"
            )

        norm_wallet = wallet_address.lower().strip()
        norm_contract = contract_address.lower().strip()

        url = f"https://{chain_cfg.reservoir_host}/users/{norm_wallet}/activity/v6"
        params = [
            ("collection", norm_contract),
            ("types", "sale"),
            ("types", "mint"),
            ("types", "transfer"),
            ("limit", "50"),
        ]

        session = await self._get_session()
        events: List[ActivityEvent] = []

        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    activities = data.get("activities", [])
                    for act in activities:
                        event = self._parse_activity_item(act, norm_wallet)
                        if event:
                            events.append(event)
        except Exception as e:
            logger.error("Error fetching user activity for %s: %s", norm_wallet, e)
            raise

        return events

    def _parse_activity_item(
        self, act: dict, user_wallet: str
    ) -> Optional[ActivityEvent]:
        raw_type = str(act.get("type", "")).lower()
        from_addr = str(act.get("fromAddress", "")).lower()
        to_addr = str(act.get("toAddress", "")).lower()
        token_info = act.get("token", {}) or {}
        token_id = str(token_info.get("tokenId") or act.get("tokenId") or "")
        tx_hash = str(act.get("txHash") or "")
        timestamp = int(act.get("timestamp") or 0)

        # Price parsing
        price_obj = act.get("price") or {}
        amount_obj = price_obj.get("amount") or {}
        price_native = (
            amount_obj.get("native")
            or amount_obj.get("decimal")
            or price_obj.get("native")
            or 0.0
        )
        price_usd = amount_obj.get("usd") or price_obj.get("usd")
        source = (act.get("order") or {}).get("source", {}).get("name")

        activity_type: Optional[ActivityType] = None

        if raw_type == "mint":
            activity_type = ActivityType.MINT
        elif raw_type == "sale":
            if to_addr == user_wallet:
                activity_type = ActivityType.BUY
            elif from_addr == user_wallet:
                activity_type = ActivityType.SELL
            else:
                activity_type = ActivityType.BUY if to_addr == user_wallet else ActivityType.SELL
        elif raw_type == "transfer":
            if from_addr == "0x0000000000000000000000000000000000000000" and to_addr == user_wallet:
                activity_type = ActivityType.MINT
            elif to_addr == user_wallet:
                activity_type = ActivityType.TRANSFER_IN
            elif from_addr == user_wallet:
                activity_type = ActivityType.TRANSFER_OUT

        if not activity_type:
            return None

        return ActivityEvent(
            tx_hash=tx_hash,
            timestamp=timestamp,
            token_id=token_id,
            activity_type=activity_type,
            from_address=from_addr,
            to_address=to_addr,
            price_native=float(price_native or 0.0),
            price_usd=float(price_usd) if price_usd is not None else None,
            order_source=source,
        )
