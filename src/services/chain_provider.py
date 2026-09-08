import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import aiohttp
from src.config import config
from src.core.models import ActivityEvent, ActivityType, CollectionMeta
from src.services.base_provider import NFTDataProvider

logger = logging.getLogger(__name__)

# Transfer(address,address,uint256) event topic
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Public reliable RPC endpoints for multi-chain queries
RPC_ENDPOINTS: Dict[str, List[str]] = {
    "base": [
        "https://mainnet.base.org",
        "https://base.publicnode.com",
    ],
    "ethereum": [
        "https://ethereum.publicnode.com",
        "https://eth.drpc.org",
    ],
    "polygon": [
        "https://polygon-bor.publicnode.com",
        "https://polygon.drpc.org",
    ],
    "arbitrum": [
        "https://arbitrum-one.publicnode.com",
        "https://arbitrum.drpc.org",
    ],
    "optimism": [
        "https://optimism.publicnode.com",
        "https://optimism.drpc.org",
    ],
    "blast": [
        "https://blast.blockpi.network/v1/rpc/public",
    ],
    "zora": [
        "https://rpc.zora.energy",
    ],
    "apechain": [
        "https://apechain.calderachain.xyz/http",
    ],
}


def pad_address(address: str) -> str:
    cleaned = address.lower().replace("0x", "")
    return "0x" + cleaned.rjust(64, "0")


def unpad_address(topic: str) -> str:
    cleaned = topic.replace("0x", "")
    if len(cleaned) == 64:
        return "0x" + cleaned[24:].lower()
    return "0x" + cleaned.lower()


class MultiChainProvider(NFTDataProvider):
    """
    Direct multi-chain provider querying reliable public RPCs
    and price APIs without single-point-of-failure DNS issues.
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": "NFT-PnL-Bot/1.0", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_native_usd_price(self, chain: str) -> float:
        """Fetch current USD rate for native token."""
        chain_key = chain.lower()
        coin_id = "ethereum"
        if "polygon" in chain_key or "matic" in chain_key:
            coin_id = "matic-network"
        elif "sol" in chain_key:
            coin_id = "solana"
        elif "btc" in chain_key or "bitcoin" in chain_key:
            coin_id = "bitcoin"

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return float(data.get(coin_id, {}).get("usd", 2500.0))
        except Exception as e:
            logger.warning("Could not fetch USD price from CoinGecko for %s: %s", chain, e)

        # Fallback reasonable defaults
        if coin_id == "matic-network":
            return 0.50
        elif coin_id == "solana":
            return 135.0
        elif coin_id == "bitcoin":
            return 60000.0
        return 2500.0

    async def get_collection_metadata(
        self, contract_address: str, chain: str
    ) -> CollectionMeta:
        chain_cfg = config.get_chain_config(chain)
        if not chain_cfg:
            chain_name = chain.capitalize()
        else:
            chain_name = chain_cfg.display_name

        norm_contract = contract_address.lower().strip()
        usd_price = await self.get_native_usd_price(chain)

        # 1. Try on-chain name() call
        name = await self._fetch_onchain_name(norm_contract, chain)
        if not name:
            short_c = f"{norm_contract[:6]}...{norm_contract[-4:]}"
            name = f"NFT Collection ({short_c})"

        # 2. Try OpenSea collection metadata
        image_url = None
        floor_price = 0.0
        try:
            opensea_info = await self._fetch_opensea_meta(norm_contract, chain)
            if opensea_info:
                if opensea_info.get("name"):
                    name = opensea_info["name"]
                image_url = opensea_info.get("image_url")
                floor_price = float(opensea_info.get("floor_price", 0.0))
        except Exception:
            pass

        return CollectionMeta(
            contract_address=norm_contract,
            name=name,
            symbol="NFT",
            image_url=image_url,
            floor_price_native=floor_price,
            native_price_usd=usd_price,
            chain=chain_name,
        )

    async def _fetch_onchain_name(self, contract: str, chain: str) -> Optional[str]:
        rpcs = RPC_ENDPOINTS.get(chain.lower(), RPC_ENDPOINTS.get("ethereum", []))
        session = await self._get_session()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [{"to": contract, "data": "0x06fdde03"}, "latest"],
        }
        for rpc in rpcs:
            try:
                async with session.post(rpc, json=payload) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        raw = res.get("result", "")
                        if raw and len(raw) > 130:
                            decoded = bytes.fromhex(raw[130:]).rstrip(b"\x00").decode("utf-8", errors="ignore")
                            if decoded.strip():
                                return decoded.strip()
            except Exception:
                continue
        return None

    async def _fetch_opensea_meta(self, contract: str, chain: str) -> Optional[dict]:
        chain_map = {"ethereum": "ethereum", "base": "base", "polygon": "matic", "arbitrum": "arbitrum"}
        os_chain = chain_map.get(chain.lower(), "ethereum")
        url = f"https://api.opensea.io/api/v2/chain/{os_chain}/contract/{contract}"
        session = await self._get_session()
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "name": data.get("name"),
                        "image_url": data.get("image_url"),
                    }
        except Exception:
            pass
        return None

    async def get_user_activity(
        self, wallet_address: str, contract_address: str, chain: str
    ) -> List[ActivityEvent]:
        rpcs = RPC_ENDPOINTS.get(chain.lower(), RPC_ENDPOINTS.get("ethereum", []))
        norm_wallet = wallet_address.lower().strip()
        norm_contract = contract_address.lower().strip()
        padded_wallet = pad_address(norm_wallet)

        session = await self._get_session()
        events: List[ActivityEvent] = []

        # Query incoming (buys / mints) and outgoing (sells / transfers)
        incoming_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getLogs",
            "params": [{
                "address": norm_contract,
                "topics": [TRANSFER_TOPIC, None, padded_wallet],
                "fromBlock": "0x0",
                "toBlock": "latest",
            }],
        }
        outgoing_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_getLogs",
            "params": [{
                "address": norm_contract,
                "topics": [TRANSFER_TOPIC, padded_wallet, None],
                "fromBlock": "0x0",
                "toBlock": "latest",
            }],
        }

        raw_logs = []
        for rpc in rpcs:
            try:
                async with session.post(rpc, json=incoming_payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_logs.extend(data.get("result", []))
                async with session.post(rpc, json=outgoing_payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_logs.extend(data.get("result", []))
                if raw_logs:
                    break
            except Exception as e:
                logger.warning("Error fetching logs from %s: %s", rpc, e)
                continue

        # Deduplicate and parse logs
        seen_txs = set()
        for log in raw_logs:
            tx_hash = log.get("transactionHash", "")
            topics = log.get("topics", [])
            data_field = log.get("data", "0x0")

            if len(topics) < 3:
                continue

            from_addr = unpad_address(topics[1])
            to_addr = unpad_address(topics[2])

            token_id = ""
            if len(topics) >= 4:
                try:
                    token_id = str(int(topics[3], 16))
                except Exception:
                    token_id = ""
            elif data_field and data_field != "0x":
                try:
                    token_id = str(int(data_field, 16))
                except Exception:
                    token_id = ""

            # Classify event
            activity_type = None
            if from_addr == "0x0000000000000000000000000000000000000000" and to_addr == norm_wallet:
                activity_type = ActivityType.MINT
            elif to_addr == norm_wallet:
                activity_type = ActivityType.BUY
            elif from_addr == norm_wallet:
                activity_type = ActivityType.SELL

            if not activity_type:
                continue

            # Estimate / fetch price
            price_native = 0.0
            events.append(
                ActivityEvent(
                    tx_hash=tx_hash,
                    timestamp=int(log.get("blockNumber", "0x0"), 16),
                    token_id=token_id,
                    activity_type=activity_type,
                    from_address=from_addr,
                    to_address=to_addr,
                    price_native=price_native,
                )
            )

        return events
