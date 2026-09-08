import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# Load .env file from project root
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
    "base": ChainConfig(
        name="base",
        reservoir_host="api-base.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#0052FF",
        display_name="Base",
    ),
    "ethereum": ChainConfig(
        name="ethereum",
        reservoir_host="api.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#627EEA",
        display_name="Ethereum",
    ),
    "eth": ChainConfig(
        name="ethereum",
        reservoir_host="api.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#627EEA",
        display_name="Ethereum",
    ),
    "mainnet": ChainConfig(
        name="ethereum",
        reservoir_host="api.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#627EEA",
        display_name="Ethereum",
    ),
    "polygon": ChainConfig(
        name="polygon",
        reservoir_host="api-polygon.reservoir.tools",
        currency_symbol="POL",
        color_hex="#8247E5",
        display_name="Polygon",
    ),
    "matic": ChainConfig(
        name="polygon",
        reservoir_host="api-polygon.reservoir.tools",
        currency_symbol="POL",
        color_hex="#8247E5",
        display_name="Polygon",
    ),
    "pol": ChainConfig(
        name="polygon",
        reservoir_host="api-polygon.reservoir.tools",
        currency_symbol="POL",
        color_hex="#8247E5",
        display_name="Polygon",
    ),
    "arbitrum": ChainConfig(
        name="arbitrum",
        reservoir_host="api-arbitrum.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#28A0F0",
        display_name="Arbitrum",
    ),
    "arb": ChainConfig(
        name="arbitrum",
        reservoir_host="api-arbitrum.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#28A0F0",
        display_name="Arbitrum",
    ),
    "optimism": ChainConfig(
        name="optimism",
        reservoir_host="api-optimism.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#FF0420",
        display_name="Optimism",
    ),
    "op": ChainConfig(
        name="optimism",
        reservoir_host="api-optimism.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#FF0420",
        display_name="Optimism",
    ),
    "zora": ChainConfig(
        name="zora",
        reservoir_host="api-zora.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#2C2C2C",
        display_name="Zora",
    ),
    "blast": ChainConfig(
        name="blast",
        reservoir_host="api-blast.reservoir.tools",
        currency_symbol="ETH",
        color_hex="#FCFC03",
        display_name="Blast",
    ),
    "apechain": ChainConfig(
        name="apechain",
        reservoir_host="api-apechain.reservoir.tools",
        currency_symbol="APE",
        color_hex="#0054F7",
        display_name="ApeChain",
    ),
    "ape": ChainConfig(
        name="apechain",
        reservoir_host="api-apechain.reservoir.tools",
        currency_symbol="APE",
        color_hex="#0054F7",
        display_name="ApeChain",
    ),
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
        return ", ".join(sorted(list(set(c.display_name for c in CHAIN_CONFIGS.values()))))


config = Config()
