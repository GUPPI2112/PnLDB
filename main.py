import logging
import sys
from src.config import config
from src.bot.client import create_bot


def setup_logging():
    log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    setup_logging()
    logger = logging.getLogger("main")

    if not config.DISCORD_BOT_TOKEN:
        logger.error(
            "DISCORD_BOT_TOKEN is not set in environment or .env file.\n"
            "Please copy .env.example to .env and add your Discord Bot Token."
        )
        sys.exit(1)

    logger.info("Starting NFT PnL Discord Bot...")
    bot = create_bot()
    bot.run(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
