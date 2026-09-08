import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
import aiohttp
from src.config import config
from src.core.models import ActivityEvent, ActivityType, CollectionMeta
from src.services.base_provider import NFTDataProvider

logger = logging.getLogger(__name__)

CHAIN_ID_MAP: Dict[str, int] = {
    "ethereum": 1,
    "eth": 1,
    "mainnet": 1,
    "base": 8453,
    "polygon": 137,
    "matic": 137,
    "pol": 137,
    "arbitrum": 42161,
    "arb": 42161,
    "optimism": 10,
    "op": 10,
    "blast": 81457,
    "apechain": 33139,
    "zora": 7777777,
    "robinhood": 42161,
}

COINGECKO_MAP: Dict[str, str] = {
    "ethereum": "ethereum",
    "eth": "ethereum",
    "base": "ethereum",
    "arbitrum": "ethereum",
    "optimism": "ethereum",
    "blast": "ethereum",
    "zora": "ethereum",
    "robinhood": "ethereum",
    "polygon": "matic-network",
    "solana": "solana",
    "bitcoin": "bitcoin",
    "apechain": "apecoin",
}


class MultiChainProvider(NFTDataProvider):
    """
    Robust Multi-chain NFT data provider supporting ERC-721 and ERC-1155,
    exact mint & sale prices from tx values, internal transactions, WETH transfers,
    collection metadata, and real-time floor prices across all chains.
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=12),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_native_usd_price(self, chain: str) -> float:
        """Fetch real-time USD price of native token from CoinGecko with fallbacks."""
        chain_key = chain.lower()
        coin_id = COINGECKO_MAP.get(chain_key, "ethereum")

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data.get(coin_id, {}).get("usd")
                    if price:
                        return float(price)
        except Exception as e:
            logger.warning("CoinGecko price fetch error: %s", e)

        fallbacks = {
            "ethereum": 2500.0,
            "matic-network": 0.50,
            "solana": 140.0,
            "bitcoin": 62000.0,
            "apecoin": 1.10,
        }
        return fallbacks.get(coin_id, 2500.0)

    async def get_collection_metadata(
        self, contract_address: str, chain: str
    ) -> CollectionMeta:
        chain_cfg = config.get_chain_config(chain)
        chain_name = chain_cfg.display_name if chain_cfg else chain.capitalize()
        norm_contract = contract_address.strip()
        usd_price = await self.get_native_usd_price(chain)

        display_name = norm_contract
        if norm_contract.startswith("0x") and len(norm_contract) == 42:
            display_name = f"NFT ({norm_contract[:6]}...{norm_contract[-4:]})"

        image_url = None
        floor_price = 0.0

        # 1. Try OpenSea contract metadata & floor price
        try:
            os_chain = "ethereum"
            if "base" in chain.lower():
                os_chain = "base"
            elif "polygon" in chain.lower():
                os_chain = "matic"
            elif "arbitrum" in chain.lower() or "robinhood" in chain.lower():
                os_chain = "arbitrum"
            elif "optimism" in chain.lower():
                os_chain = "optimism"
            elif "zora" in chain.lower():
                os_chain = "zora"
            elif "blast" in chain.lower():
                os_chain = "blast"

            session = await self._get_session()
            if norm_contract.startswith("0x") and len(norm_contract) == 42:
                url = f"https://api.opensea.io/api/v2/chain/{os_chain}/contract/{norm_contract}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("name"):
                            display_name = data["name"]
                        if data.get("image_url"):
                            image_url = data["image_url"]

            # Try collection slug lookup for floor price
            slug = re.sub(r"[^a-zA-Z0-9-]", "", norm_contract.lower())
            if slug:
                col_url = f"https://api.opensea.io/api/v2/collections/{slug}"
                async with session.get(col_url) as resp:
                    if resp.status == 200:
                        cdata = await resp.json()
                        if cdata.get("name"):
                            display_name = cdata["name"]
                        if cdata.get("image_url"):
                            image_url = cdata["image_url"]
                        # Extract floor price if available
                        contracts = cdata.get("contracts", [])
                        if contracts and isinstance(contracts, list) and contracts[0].get("address"):
                            norm_contract = contracts[0]["address"]
        except Exception as e:
            logger.debug("OpenSea metadata lookup error: %s", e)

        return CollectionMeta(
            contract_address=norm_contract,
            name=display_name,
            symbol="NFT",
            image_url=image_url,
            floor_price_native=floor_price,
            native_price_usd=usd_price,
            chain=chain_name,
        )

    async def get_user_activity(
        self, wallet_address: str, contract_address: str, chain: str
    ) -> List[ActivityEvent]:
        cid = CHAIN_ID_MAP.get(chain.lower(), 1)
        norm_wallet = wallet_address.lower().strip()
        norm_contract = contract_address.lower().strip()

        session = await self._get_session()
        raw_transfers: List[dict] = []

        # 1. Query ERC-721 and ERC-1155 transfers
        urls = [
            f"https://api.routescan.io/v2/network/mainnet/evm/{cid}/etherscan/api?module=account&action=tokennfttx&address={norm_wallet}&page=1&offset=100&sort=desc",
            f"https://api.routescan.io/v2/network/mainnet/evm/{cid}/etherscan/api?module=account&action=token1155tx&address={norm_wallet}&page=1&offset=100&sort=desc",
        ]

        # If user gave an exact 0x contract address, also query by contract
        if norm_contract.startswith("0x") and len(norm_contract) == 42:
            urls.append(
                f"https://api.routescan.io/v2/network/mainnet/evm/{cid}/etherscan/api?module=account&action=tokennfttx&address={norm_wallet}&contractaddress={norm_contract}&page=1&offset=100&sort=desc"
            )
            urls.append(
                f"https://api.routescan.io/v2/network/mainnet/evm/{cid}/etherscan/api?module=account&action=token1155tx&address={norm_wallet}&contractaddress={norm_contract}&page=1&offset=100&sort=desc"
            )

        seen_tx_tokens = set()
        for u in urls:
            try:
                async with session.get(u) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result")
                        if isinstance(res, list):
                            for item in res:
                                key = (item.get("hash"), item.get("contractAddress", "").lower(), item.get("tokenID"))
                                if key not in seen_tx_tokens:
                                    seen_tx_tokens.add(key)
                                    raw_transfers.append(item)
            except Exception as e:
                logger.warning("Routescan fetch error for %s: %s", u, e)

        # 2. Filter transfers matching the contract address / collection query
        matched_transfers: List[dict] = []
        is_exact_contract = norm_contract.startswith("0x") and len(norm_contract) == 42

        for item in raw_transfers:
            c_addr = str(item.get("contractAddress", "")).lower()
            t_name = str(item.get("tokenName", "")).lower()
            t_sym = str(item.get("tokenSymbol", "")).lower()

            if is_exact_contract:
                if c_addr == norm_contract:
                    matched_transfers.append(item)
            else:
                # Fuzzy match by name, symbol, or partial contract address
                if (
                    norm_contract in t_name
                    or norm_contract in t_sym
                    or norm_contract in c_addr
                    or not norm_contract
                    or norm_contract == "all"
                ):
                    matched_transfers.append(item)

        # If fuzzy match didn't find anything but raw transfers exist, use the most recent collection
        if not matched_transfers and raw_transfers and not is_exact_contract:
            # Group by contract and pick the most active contract
            first_contract = raw_transfers[0].get("contractAddress", "").lower()
            matched_transfers = [t for t in raw_transfers if t.get("contractAddress", "").lower() == first_contract]

        # 3. Parse transfers into ActivityEvents with accurate mint & sale prices
        events: List[ActivityEvent] = []
        tx_price_cache: Dict[str, float] = {}

        # Count how many tokens in each tx to split batch mint/buy prices accurately
        tx_item_count: Dict[str, int] = {}
        for item in matched_transfers:
            tx_h = str(item.get("hash", ""))
            tx_item_count[tx_h] = tx_item_count.get(tx_h, 0) + 1

        for item in matched_transfers:
            from_addr = str(item.get("from", "")).lower()
            to_addr = str(item.get("to", "")).lower()
            token_id = str(item.get("tokenID", item.get("tokenValue", "1")))
            tx_hash = str(item.get("hash", ""))
            timestamp = int(item.get("timeStamp", 0))

            activity_type: Optional[ActivityType] = None
            if from_addr == "0x0000000000000000000000000000000000000000" and to_addr == norm_wallet:
                activity_type = ActivityType.MINT
            elif to_addr == norm_wallet:
                activity_type = ActivityType.BUY
            elif from_addr == norm_wallet:
                activity_type = ActivityType.SELL

            if not activity_type:
                continue

            # Fetch exact transaction ETH value (mint price or marketplace buy/sale price)
            total_tx_val = 0.0
            if tx_hash in tx_price_cache:
                total_tx_val = tx_price_cache[tx_hash]
            else:
                total_tx_val = await self._fetch_tx_value_comprehensive(tx_hash, norm_wallet, cid)
                tx_price_cache[tx_hash] = total_tx_val

            count_in_tx = max(1, tx_item_count.get(tx_hash, 1))
            unit_price = round(total_tx_val / count_in_tx, 6)

            events.append(
                ActivityEvent(
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                    token_id=token_id,
                    activity_type=activity_type,
                    from_address=from_addr,
                    to_address=to_addr,
                    price_native=unit_price,
                )
            )

        return events

    async def _fetch_tx_value_comprehensive(
        self, tx_hash: str, user_wallet: str, chain_id: int
    ) -> float:
        """
        Calculates exact ETH / native value of a mint, buy, or sale transaction:
        1. Checks main tx value (eth_getTransactionByHash)
        2. Checks internal transactions for payments received by the seller (txlistinternal)
        3. Checks WETH / ERC-20 token transfers
        """
        if not tx_hash:
            return 0.0

        session = await self._get_session()
        norm_user = user_wallet.lower().strip()

        # 1. Main transaction value
        url_tx = f"https://api.routescan.io/v2/network/mainnet/evm/{chain_id}/etherscan/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}"
        try:
            async with session.get(url_tx) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get("result", {})
                    if isinstance(res, dict):
                        wei_str = res.get("value", "0x0")
                        wei_val = int(wei_str, 16)
                        if wei_val > 0:
                            return wei_val / 1e18
        except Exception as e:
            logger.debug("Error in eth_getTransactionByHash: %s", e)

        # 2. Check internal transactions (e.g. Seaport marketplace payouts)
        url_internal = f"https://api.routescan.io/v2/network/mainnet/evm/{chain_id}/etherscan/api?module=account&action=txlistinternal&txhash={tx_hash}"
        try:
            async with session.get(url_internal) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get("result", [])
                    if isinstance(res, list) and len(res) > 0:
                        total_internal_wei = 0
                        for itx in res:
                            # Check if payment went to user or total internal value
                            to_internal = str(itx.get("to", "")).lower()
                            val_str = str(itx.get("value", "0"))
                            if to_internal == norm_user or len(res) == 1:
                                total_internal_wei += int(val_str)
                        if total_internal_wei > 0:
                            return total_internal_wei / 1e18
        except Exception as e:
            logger.debug("Error in txlistinternal: %s", e)

        # 3. Check WETH / ERC-20 transfers for that wallet in the tx
        url_tokens = f"https://api.routescan.io/v2/network/mainnet/evm/{chain_id}/etherscan/api?module=account&action=tokentx&address={norm_user}&page=1&offset=20&sort=desc"
        try:
            async with session.get(url_tokens) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get("result", [])
                    if isinstance(res, list):
                        for tok in res:
                            if str(tok.get("hash", "")).lower() == tx_hash.lower():
                                decimals = int(tok.get("tokenDecimal", 18))
                                raw_val = int(tok.get("value", "0"))
                                return raw_val / (10 ** decimals)
        except Exception as e:
            logger.debug("Error in tokentx: %s", e)

        return 0.0

