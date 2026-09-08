# NFT PnL Discord Bot

A modular, multi-chain Discord bot that generates visual NFT Profit & Loss (PnL) cards from on-chain marketplace activity and mints.

Supports **Base, Ethereum, Polygon, Arbitrum, Optimism, Blast, Zora, and ApeChain**.

---

## Features

- **Interactive Discord UI**:
  - Single **"Check PnL"** button (no emojis) that opens an interactive modal form.
  - Form prompts for **Wallet Address**, **NFT Contract Address**, and **Blockchain Network**.
  - Generated PnL cards include a **"Download Card"** button for full-resolution download.
  - Also supports direct `/pnl` slash command and `/setup` channel panel deployment.
- **Dynamic Template Switching**:
  - **Green Card** template (`assets/templates/profit_card.png`) for profits ($PnL \ge 0$).
  - **Red Card** template (`assets/templates/loss_card.png`) for losses ($PnL < 0$).
  - Easily replace template backgrounds with your own custom designs.
- **Accurate On-Chain Analytics**:
  - Powered by Reservoir multi-chain NFT indexer (indexes OpenSea, Blur, MagicEden, LooksRare, Seaport fills & direct mints).
  - FIFO token cost-basis tracking, total invested (buys + mints), total received (sales), net realized PnL, ROI %, and currently held inventory.
- **Fast Image Generation**:
  - Pure Python Pillow engine rendering high-resolution ($1200 \times 675$) PNG cards in under 50ms with zero heavy browser dependencies (no Puppeteer/Chromium required).

---

## Project Architecture

The bot follows a 4-tier decoupled architecture:

```
nft-pnl-bot/
├── assets/
│   ├── fonts/                    # Bundled TrueType fonts for cross-platform rendering
│   └── templates/
│       ├── profit_card.png       # Green card template for profit
│       └── loss_card.png         # Red card template for loss
├── src/
│   ├── config.py                 # Multi-chain configs & environment settings
│   ├── bot/                      # Layer 1: Discord Bot Interface
│   │   ├── client.py             # Bot client & command synchronization
│   │   ├── modals.py             # PnLModal form (Wallet, Contract, Chain)
│   │   ├── views.py              # PnLLauncherView & PnLResultView
│   │   └── commands/
│   │       ├── pnl.py            # Slash command & modal execution handler
│   │       └── setup.py          # /setup command to post the Check PnL panel
│   ├── services/                 # Layer 2: Multi-Chain Data Provider
│   │   ├── base_provider.py      # Abstract DataProvider interface
│   │   └── reservoir.py          # Reservoir API client (sales, mints, metadata)
│   ├── core/                     # Layer 3: Pure Domain Logic (No I/O)
│   │   ├── models.py             # Strongly-typed data models
│   │   └── calculator.py         # FIFO PnL, ROI %, and inventory math
│   └── renderer/                 # Layer 4: Image Generator
│       ├── card_renderer.py      # Dynamic card renderer overlaying template
│       └── template_generator.py # Baseline template generator
├── tests/
│   ├── test_calculator.py        # Unit tests for PnL & ROI edge cases
│   ├── test_reservoir.py         # Unit tests for API activity parsing
│   └── test_renderer.py          # Unit tests for image generation
├── .env.example                  # Environment configuration template
├── requirements.txt              # Project dependencies
└── main.py                       # Application entry point
```

---

## Quickstart & Setup Guide

### 1. Prerequisites
- Python 3.10+
- A Discord Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications)

### 2. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-username/nft-pnl-bot.git
cd nft-pnl-bot

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Open `.env` and configure your credentials:

```env
# Discord Bot Credentials (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Optional: Specific Guild ID for instant slash command synchronization in development
DISCORD_GUILD_ID=

# Reservoir API Key (Optional but recommended for higher rate limits)
RESERVOIR_API_KEY=

# Log Level
LOG_LEVEL=INFO
```

---

## Setting Up Your Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a **New Application**.
2. Navigate to the **Bot** tab:
   - Click **Reset Token** and copy your token into `DISCORD_BOT_TOKEN` in `.env`.
   - Ensure **Message Content Intent** and default bot permissions are enabled if needed.
3. Navigate to **OAuth2 > URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Use Slash Commands`
   - Copy the generated URL and open it in your browser to invite the bot to your Discord server.

---

## Running the Bot

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the bot
python3 main.py
```

---

## How to Use in Discord

### Method 1: Interactive Button & Modal (Recommended)
1. In your Discord server, run `/setup` in any channel.
2. The bot will post a clean panel with a **Check PnL** button.
3. Users click **Check PnL** to open the modal form:
   - **Wallet Address**: e.g., `0xd8da6bf26964af9d7eed9e03e53415d37aa96045`
   - **NFT Contract Address**: e.g., `0xbd3531da5cf5857e7cfaa92426877b022e612cf8`
   - **Blockchain**: `base`, `ethereum`, `polygon`, `arbitrum`, `optimism`, `blast`, `zora`, or `apechain`
4. The bot computes the PnL and sends the generated card image with a **Download Card** button.

### Method 2: Slash Command
Users can also trigger PnL checks directly via slash command:
```
/pnl wallet:0x1234... contract:0xabcd... chain:base
```

---

## Customizing Card Templates

To use your own custom card designs:
1. Create two $1200 \times 675$ PNG images:
   - `profit_card.png` (Green / profit theme)
   - `loss_card.png` (Red / loss theme)
2. Place or overwrite them in `assets/templates/`:
   - `assets/templates/profit_card.png`
   - `assets/templates/loss_card.png`
3. The bot will automatically use your custom background images and overlay the collection logo, collection name, wallet tag, chain, hero PnL, ROI %, and stats grid.

---

## Running Tests

Run the full automated test suite with `pytest`:

```bash
pytest -v
```

All 13 unit tests cover:
- Profitable trades and ROI calculation
- Loss trades and negative ROI
- Free mints and zero-cost airdrop flips
- Unsold holding inventory
- Token transfers and gifts
- Case-insensitive address normalization
- Multi-chain activity parsing from Reservoir API
- In-memory PNG rendering validation
