import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")


@dataclass(frozen=True)
class ChainConfig:
    name: str
    reservoir_host: str
    currency_symbol: str
    color_hex: str
    display_name: str


CHAIN_CONFIGS: Dict[str, ChainConfig] = {
    # Ethereum
    "ethereum": ChainConfig(name="ethereum", reservoir_host="api.reservoir.tools", currency_symbol="ETH", color_hex="#627EEA", display_name="Ethereum"),
    "eth": ChainConfig(name="ethereum", reservoir_host="api.reservoir.tools", currency_symbol="ETH", color_hex="#627EEA", display_name="Ethereum"),
    "mainnet": ChainConfig(name="ethereum", reservoir_host="api.reservoir.tools", currency_symbol="ETH", color_hex="#627EEA", display_name="Ethereum"),
    
    # Base
    "base": ChainConfig(name="base", reservoir_host="api-base.reservoir.tools", currency_symbol="ETH", color_hex="#0052FF", display_name="Base"),
    
    # Solana
    "solana": ChainConfig(name="solana", reservoir_host="api-polygon.reservoir.tools", currency_symbol="SOL", color_hex="#14F195", display_name="Solana"),
    "sol": ChainConfig(name="solana", reservoir_host="api-polygon.reservoir.tools", currency_symbol="SOL", color_hex="#14F195", display_name="Solana"),

    # Bitcoin / Ordinals
    "bitcoin": ChainConfig(name="bitcoin", reservoir_host="api.reservoir.tools", currency_symbol="BTC", color_hex="#F7931A", display_name="Bitcoin"),
    "btc": ChainConfig(name="bitcoin", reservoir_host="api.reservoir.tools", currency_symbol="BTC", color_hex="#F7931A", display_name="Bitcoin"),
    "ordinals": ChainConfig(name="bitcoin", reservoir_host="api.reservoir.tools", currency_symbol="BTC", color_hex="#F7931A", display_name="Bitcoin"),

    # Robinhood
    "robinhood": ChainConfig(name="robinhood", reservoir_host="api-arbitrum.reservoir.tools", currency_symbol="ETH", color_hex="#00C805", display_name="Robinhood Chain"),
    "rh": ChainConfig(name="robinhood", reservoir_host="api-arbitrum.reservoir.tools", currency_symbol="ETH", color_hex="#00C805", display_name="Robinhood Chain"),

    # Polygon
    "polygon": ChainConfig(name="polygon", reservoir_host="api-polygon.reservoir.tools", currency_symbol="POL", color_hex="#8247E5", display_name="Polygon"),
    "matic": ChainConfig(name="polygon", reservoir_host="api-polygon.reservoir.tools", currency_symbol="POL", color_hex="#8247E5", display_name="Polygon"),
    "pol": ChainConfig(name="polygon", reservoir_host="api-polygon.reservoir.tools", currency_symbol="POL", color_hex="#8247E5", display_name="Polygon"),

    # Arbitrum
    "arbitrum": ChainConfig(name="arbitrum", reservoir_host="api-arbitrum.reservoir.tools", currency_symbol="ETH", color_hex="#28A0F0", display_name="Arbitrum"),
    "arb": ChainConfig(name="arbitrum", reservoir_host="api-arbitrum.reservoir.tools", currency_symbol="ETH", color_hex="#28A0F0", display_name="Arbitrum"),

    # Optimism
    "optimism": ChainConfig(name="optimism", reservoir_host="api-optimism.reservoir.tools", currency_symbol="ETH", color_hex="#FF0420", display_name="Optimism"),
    "op": ChainConfig(name="optimism", reservoir_host="api-optimism.reservoir.tools", currency_symbol="ETH", color_hex="#FF0420", display_name="Optimism"),

    # Blast
    "blast": ChainConfig(name="blast", reservoir_host="api-blast.reservoir.tools", currency_symbol="ETH", color_hex="#FCFC03", display_name="Blast"),

    # Zora
    "zora": ChainConfig(name="zora", reservoir_host="api-zora.reservoir.tools", currency_symbol="ETH", color_hex="#2C2C2C", display_name="Zora"),

    # ApeChain
    "apechain": ChainConfig(name="apechain", reservoir_host="api-apechain.reservoir.tools", currency_symbol="APE", color_hex="#0054F7", display_name="ApeChain"),
    "ape": ChainConfig(name="apechain", reservoir_host="api-apechain.reservoir.tools", currency_symbol="APE", color_hex="#0054F7", display_name="ApeChain"),

    # Linea
    "linea": ChainConfig(name="linea", reservoir_host="api-linea.reservoir.tools", currency_symbol="ETH", color_hex="#121212", display_name="Linea"),

    # Scroll
    "scroll": ChainConfig(name="scroll", reservoir_host="api-scroll.reservoir.tools", currency_symbol="ETH", color_hex="#FFEEDB", display_name="Scroll"),

    # Avalanche
    "avalanche": ChainConfig(name="avalanche", reservoir_host="api-avalanche.reservoir.tools", currency_symbol="AVAX", color_hex="#E84142", display_name="Avalanche"),
    "avax": ChainConfig(name="avalanche", reservoir_host="api-avalanche.reservoir.tools", currency_symbol="AVAX", color_hex="#E84142", display_name="Avalanche"),

    # BNB Chain
    "bsc": ChainConfig(name="bsc", reservoir_host="api-bsc.reservoir.tools", currency_symbol="BNB", color_hex="#F3BA2F", display_name="BNB Chain"),
    "binance": ChainConfig(name="bsc", reservoir_host="api-bsc.reservoir.tools", currency_symbol="BNB", color_hex="#F3BA2F", display_name="BNB Chain"),

    # Sonic / Fantom
    "sonic": ChainConfig(name="sonic", reservoir_host="api.reservoir.tools", currency_symbol="S", color_hex="#1969FF", display_name="Sonic"),
    "fantom": ChainConfig(name="sonic", reservoir_host="api.reservoir.tools", currency_symbol="FTM", color_hex="#1969FF", display_name="Fantom"),
    "ftm": ChainConfig(name="sonic", reservoir_host="api.reservoir.tools", currency_symbol="FTM", color_hex="#1969FF", display_name="Fantom"),

    # Berachain
    "berachain": ChainConfig(name="berachain", reservoir_host="api.reservoir.tools", currency_symbol="BERA", color_hex="#8B4513", display_name="Berachain"),
    "bera": ChainConfig(name="berachain", reservoir_host="api.reservoir.tools", currency_symbol="BERA", color_hex="#8B4513", display_name="Berachain"),

    # Monad
    "monad": ChainConfig(name="monad", reservoir_host="api.reservoir.tools", currency_symbol="MON", color_hex="#836EF9", display_name="Monad"),

    # Sei
    "sei": ChainConfig(name="sei", reservoir_host="api-sei.reservoir.tools", currency_symbol="SEI", color_hex="#9B1C2E", display_name="Sei"),

    # Abstract
    "abstract": ChainConfig(name="abstract", reservoir_host="api.reservoir.tools", currency_symbol="ETH", color_hex="#00FF00", display_name="Abstract"),
}


class Config:
    ROOT_DIR: Path = ROOT_DIR
    TEMPLATES_DIR: Path = ROOT_DIR / "assets" / "templates"
    PROFIT_TEMPLATE_PATH: Path = TEMPLATES_DIR / "profit_card.png"
    LOSS_TEMPLATE_PATH: Path = TEMPLATES_DIR / "loss_card.png"

    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    DISCORD_GUILD_ID: Optional[int] = (
        int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    )
    PNL_CHANNEL_ID: Optional[int] = (
        int(os.getenv("PNL_CHANNEL_ID")) if os.getenv("PNL_CHANNEL_ID") else 1546728305833672725
    )
    RESERVOIR_API_KEY: str = os.getenv("RESERVOIR_API_KEY", "").strip()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def get_chain_config(cls, chain_input: str) -> Optional[ChainConfig]:
        normalized = chain_input.lower().strip()
        return CHAIN_CONFIGS.get(normalized)

    @classmethod
    def supported_chains_display(cls) -> str:
        return "ETH, Base, SOL, BTC, Robinhood, Polygon, Arbitrum, Optimism, Blast, Zora, ApeChain, Linea, Scroll, Avalanche, BSC, Sonic, Berachain, Monad, Sei, Abstract"


config = Config()
