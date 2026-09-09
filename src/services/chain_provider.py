import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple
import aiohttp
from src.config import config
from src.core.models import ActivityEvent, ActivityType, CollectionMeta
from src.services.base_provider import NFTDataProvider

logger = logging.getLogger(__name__)

CHAIN_API_MAP: Dict[str, List[str]] = {
    "ethereum": [
        "https://eth.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/1/etherscan/api",
    ],
    "base": [
        "https://base.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/8453/etherscan/api",
    ],
    "arbitrum": [
        "https://arbitrum.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/42161/etherscan/api",
    ],
    "robinhood": [
        "https://arbitrum.blockscout.com/api",
    ],
    "polygon": [
        "https://polygon.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/137/etherscan/api",
    ],
    "optimism": [
        "https://optimism.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/10/etherscan/api",
    ],
    "blast": [
        "https://blast.blockscout.com/api",
        "https://api.routescan.io/v2/network/mainnet/evm/81457/etherscan/api",
    ],
    "zora": [
        "https://zora.blockscout.com/api",
        "https://explorer.zora.energy/api",
    ],
    "apechain": [
        "https://apechain.calderaexplorer.xyz/api",
    ],
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


BLOCKSCOUT_DOMAINS: Dict[str, str] = {
    "ethereum": "eth.blockscout.com",
    "eth": "eth.blockscout.com",
    "mainnet": "eth.blockscout.com",
    "base": "base.blockscout.com",
    "arbitrum": "arbitrum.blockscout.com",
    "arb": "arbitrum.blockscout.com",
    "robinhood": "arbitrum.blockscout.com",
    "polygon": "polygon.blockscout.com",
    "matic": "polygon.blockscout.com",
    "pol": "polygon.blockscout.com",
    "optimism": "optimism.blockscout.com",
    "op": "optimism.blockscout.com",
    "blast": "blast.blockscout.com",
    "zora": "zora.blockscout.com",
}


OPENSEA_CHAIN_MAP: Dict[str, str] = {
    "ethereum": "ethereum",
    "eth": "ethereum",
    "mainnet": "ethereum",
    "base": "base",
    "arbitrum": "arbitrum",
    "arb": "arbitrum",
    "robinhood": "arbitrum",
    "polygon": "matic",
    "matic": "matic",
    "pol": "matic",
    "optimism": "optimism",
    "op": "optimism",
    "blast": "blast",
    "zora": "zora",
    "apechain": "apechain",
}


RPC_MAP: Dict[str, List[str]] = {
    "ethereum": ["https://eth.llamarpc.com", "https://rpc.ankr.com/eth"],
    "base": ["https://mainnet.base.org", "https://rpc.ankr.com/base"],
    "arbitrum": ["https://arb1.arbitrum.io/rpc", "https://rpc.ankr.com/arbitrum"],
    "polygon": ["https://polygon-rpc.com", "https://rpc.ankr.com/polygon"],
    "optimism": ["https://mainnet.optimism.io", "https://rpc.ankr.com/optimism"],
    "blast": ["https://rpc.blast.io"],
    "zora": ["https://rpc.zora.energy"],
    "apechain": ["https://rpc.apechain.com"],
}


def decode_abi_string(hex_str: str) -> str:
    if not hex_str or hex_str == "0x" or len(hex_str) < 130:
        return ""
    try:
        raw = bytes.fromhex(hex_str[2:])
        length = int.from_bytes(raw[32:64], "big")
        return raw[64 : 64 + length].decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


class MultiChainProvider(NFTDataProvider):
    """
    Robust Multi-chain NFT data provider supporting ERC-721 and ERC-1155,
    exact mint & sale prices from tx values, internal transactions, WETH transfers,
    OpenSea collection metadata & avatars, onchain RPC contract inspection,
    and real-time floor prices across all chains.
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
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

    async def _fetch_opensea_metadata(
        self, contract: str, chain: str
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Fetches official collection name, avatar image, and floor price from OpenSea.
        """
        chain_slug = OPENSEA_CHAIN_MAP.get(chain.lower(), "ethereum")
        session = await self._get_session()
        
        urls = [
            f"https://opensea.io/assets/{chain_slug}/{contract}",
            f"https://opensea.io/item/{chain_slug}/{contract}/1",
        ]

        for url in urls:
            try:
                async with session.get(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        html = await resp.text()

                        # 1. Extract collection title
                        title_match = re.search(r'<meta\s+property=[\"\']og:title[\"\']\s+content=[\"\']([^\"\']+)[\"\']', html, re.I)
                        name = None
                        floor_price = 0.0

                        if title_match:
                            raw_title = title_match.group(1)

                            # Extract floor price if present: e.g. '0.0005 ETH'
                            floor_match = re.search(r'([\d\.]+)\s+(?:ETH|MATIC|POL|WETH|SOL)', raw_title, re.I)
                            if floor_match:
                                try:
                                    floor_price = float(floor_match.group(1))
                                except Exception:
                                    pass

                            clean = re.sub(r'(\s+[\d\.]+\s+[A-Za-z]+)?\s*-\s*Collection\s*\|\s*OpenSea.*', '', raw_title, flags=re.I).strip()
                            clean = re.sub(r'\s*\|\s*OpenSea.*', '', clean, flags=re.I).strip()
                            if ' - ' in clean and '#' in clean.split(' - ')[0]:
                                clean = clean.split(' - ', 1)[1].strip()
                            if clean and not clean.lower().startswith('opensea') and not clean.startswith('0x'):
                                name = clean

                        # 2. Extract collection avatar / logo image
                        image_url = None
                        imgs = re.findall(r'<img[^>]+src=[\"\']([^\"\']*(?:image_type_logo|image_type_avatar|h=250|/image/)[^\"\']*)[\"\']', html)
                        if imgs:
                            image_url = imgs[0].replace('&amp;', '&').split('?')[0]

                        if not image_url:
                            og_img = re.search(r'<meta\s+property=[\"\']og:image[\"\']\s+content=[\"\']([^\"\']+)[\"\']', html, re.I)
                            if og_img and ('opengraph-image' in og_img.group(1) or 'seadn.io' in og_img.group(1)):
                                image_url = og_img.group(1)

                        if name or image_url:
                            return name, image_url, floor_price
            except Exception as e:
                logger.debug("OpenSea metadata lookup error for %s on %s: %s", contract, url, e)

        return None, None, 0.0

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
        session = await self._get_session()

        if norm_contract.startswith("0x") and len(norm_contract) == 42:
            # 1. Primary: Try OpenSea collection & avatar resolution
            os_name, os_img, os_floor = await self._fetch_opensea_metadata(norm_contract, chain)
            if os_name:
                display_name = os_name
            if os_img:
                image_url = os_img
            if os_floor > 0:
                floor_price = os_floor

            # 2. Fallback / Secondary: Blockscout Token API
            domain = BLOCKSCOUT_DOMAINS.get(chain.lower(), "eth.blockscout.com")
            if not image_url or display_name.startswith("NFT (0x"):
                url_token = f"https://{domain}/api/v2/tokens/{norm_contract}"
                try:
                    async with session.get(url_token, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                        if resp.status == 200:
                            tdata = await resp.json()
                            if tdata.get("name") and display_name.startswith("NFT (0x"):
                                display_name = tdata["name"]
                            if tdata.get("icon_url") and not image_url:
                                image_url = tdata["icon_url"]
                except Exception as e:
                    logger.debug("Blockscout token lookup error: %s", e)

            # 3. Fallback / Tertiary: Blockscout NFT instance image
            if not image_url:
                url_inst = f"https://{domain}/api/v2/tokens/{norm_contract}/instances"
                try:
                    async with session.get(url_inst, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                        if resp.status == 200:
                            idata = await resp.json()
                            items = idata.get("items", [])
                            if items:
                                if display_name.startswith("NFT (0x") and items[0].get("metadata", {}).get("name"):
                                    item_nm = items[0]["metadata"]["name"]
                                    # Strip '#...' from item name
                                    clean_item_nm = re.sub(r'\s*#\d+.*', '', item_nm).strip()
                                    if clean_item_nm:
                                        display_name = clean_item_nm
                                img = items[0].get("image_url") or items[0].get("metadata", {}).get("image")
                                if img:
                                    if img.startswith("ipfs://"):
                                        img = "https://ipfs.io/ipfs/" + img[7:]
                                    image_url = img
                except Exception as e:
                    logger.debug("Blockscout instance lookup error: %s", e)

            # 4. Fallback / Quaternary: Direct Onchain RPC Call (ERC-721 name() & tokenURI())
            if display_name.startswith("NFT (0x") or not image_url:
                rpcs = RPC_MAP.get(chain.lower(), ["https://eth.llamarpc.com"])
                for rpc in rpcs:
                    # Query onchain name()
                    if display_name.startswith("NFT (0x"):
                        try:
                            payload = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "eth_call",
                                "params": [{"to": norm_contract, "data": "0x06fdde03"}, "latest"],
                            }
                            async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    onchain_name = decode_abi_string(data.get("result", ""))
                                    if onchain_name:
                                        display_name = onchain_name
                        except Exception:
                            pass

                    # Query onchain tokenURI()
                    if not image_url:
                        for tid in [1, 0, 2]:
                            try:
                                token_hex = hex(tid)[2:].zfill(64)
                                payload = {
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "eth_call",
                                    "params": [{"to": norm_contract, "data": "0xc87b56dd" + token_hex}, "latest"],
                                }
                                async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                                    if resp.status == 200:
                                        data = await resp.json()
                                        uri = decode_abi_string(data.get("result", ""))
                                        if uri:
                                            if uri.startswith("ipfs://"):
                                                uri = "https://ipfs.io/ipfs/" + uri[7:]
                                            async with session.get(uri, timeout=aiohttp.ClientTimeout(total=3)) as meta_r:
                                                if meta_r.status == 200:
                                                    mjson = await meta_r.json()
                                                    if display_name.startswith("NFT (0x") and mjson.get("collection_name"):
                                                        display_name = mjson["collection_name"]
                                                    img = mjson.get("image") or mjson.get("image_url")
                                                    if img:
                                                        if img.startswith("ipfs://"):
                                                            img = "https://ipfs.io/ipfs/" + img[7:]
                                                        image_url = img
                                                        break
                            except Exception:
                                pass
                        if image_url:
                            break

        # 5. If user entered a collection name directly, preserve it
        if not norm_contract.startswith("0x"):
            display_name = norm_contract

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
        norm_wallet = wallet_address.lower().strip()
        norm_contract = contract_address.lower().strip()

        session = await self._get_session()
        raw_transfers: List[dict] = []

        api_bases = CHAIN_API_MAP.get(chain.lower(), ["https://eth.blockscout.com/api"])
        actions = ["tokennfttx", "token1155tx"]

        for api_base in api_bases:
            chain_transfers = []
            seen_tokens = set()

            for act in actions:
                # 1. Fetch wallet transfers
                urls = [
                    f"{api_base}?module=account&action={act}&address={norm_wallet}&page=1&offset=100&sort=desc",
                ]
                if norm_contract.startswith("0x") and len(norm_contract) == 42:
                    urls.append(
                        f"{api_base}?module=account&action={act}&address={norm_wallet}&contractaddress={norm_contract}&page=1&offset=100&sort=desc"
                    )

                for u in urls:
                    try:
                        async with session.get(u, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                res = data.get("result")
                                if isinstance(res, list):
                                    for item in res:
                                        key = (item.get("hash"), item.get("contractAddress", "").lower(), item.get("tokenID"))
                                        if key not in seen_tokens:
                                            seen_tokens.add(key)
                                            chain_transfers.append(item)
                    except Exception as e:
                        logger.debug("Transfer fetch error from %s: %s", u, e)

            if chain_transfers:
                raw_transfers = chain_transfers
                break

        # Filter matching transfers
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
                if (
                    norm_contract in t_name
                    or norm_contract in t_sym
                    or norm_contract in c_addr
                    or not norm_contract
                    or norm_contract == "all"
                ):
                    matched_transfers.append(item)

        if not matched_transfers and raw_transfers and not is_exact_contract:
            first_contract = raw_transfers[0].get("contractAddress", "").lower()
            matched_transfers = [t for t in raw_transfers if t.get("contractAddress", "").lower() == first_contract]

        # Parse transfers into ActivityEvents with accurate mint & sale prices
        events: List[ActivityEvent] = []
        tx_price_cache: Dict[str, float] = {}

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

            total_tx_val = 0.0
            if tx_hash in tx_price_cache:
                total_tx_val = tx_price_cache[tx_hash]
            else:
                total_tx_val = await self._fetch_tx_value_comprehensive(tx_hash, norm_wallet, chain)
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
        self, tx_hash: str, user_wallet: str, chain: str
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
        api_bases = CHAIN_API_MAP.get(chain.lower(), ["https://eth.blockscout.com/api"])

        for api_base in api_bases:
            # 1. Main transaction value
            url_tx = f"{api_base}?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}"
            try:
                async with session.get(url_tx, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result", {})
                        if isinstance(res, dict):
                            wei_str = res.get("value", "0x0")
                            wei_val = int(wei_str, 16) if wei_str.startswith("0x") else int(wei_str or "0")
                            if wei_val > 0:
                                return wei_val / 1e18
            except Exception as e:
                logger.debug("Error in eth_getTransactionByHash: %s", e)

            # 2. Check internal transactions (e.g. Seaport marketplace payouts)
            url_internal = f"{api_base}?module=account&action=txlistinternal&txhash={tx_hash}"
            try:
                async with session.get(url_internal, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result", [])
                        if isinstance(res, list) and len(res) > 0:
                            total_internal_wei = 0
                            for itx in res:
                                to_internal = str(itx.get("to", "")).lower()
                                val_str = str(itx.get("value", "0"))
                                if to_internal == norm_user or len(res) == 1:
                                    total_internal_wei += int(val_str)
                            if total_internal_wei > 0:
                                return total_internal_wei / 1e18
            except Exception as e:
                logger.debug("Error in txlistinternal: %s", e)

            # 3. Check WETH / ERC-20 transfers for that wallet in the tx
            url_tokens = f"{api_base}?module=account&action=tokentx&address={norm_user}&page=1&offset=20&sort=desc"
            try:
                async with session.get(url_tokens, timeout=aiohttp.ClientTimeout(total=4)) as resp:
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

