# Telegram bot with LazAI: Your new AI Agent with easiest steps

Create a powerful Telegram bot that can handle token management on Metis Sepolia and respond intelligently to messages using LazAI's Alith SDK. This tutorial will guide you through the process step by step.

## Quick Start Guide

### 1. Set Up Your Environment

```bash
# Create a new project folder and navigate to it
mkdir my-telegram-bot
cd my-telegram-bot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install alith python-telegram-bot python-dotenv web3
```

### 2. Get Your API Keys

1. **Telegram Bot Token**:
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow prompts to name your bot
   - Save the bot token you receive

2. **OpenAI API Key**:
   - Visit [OpenAI](https://platform.openai.com)
   - Create an account or log in
   - Generate an API key

3. **Create `.env` file**:
```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
PRIVATE_KEY=your_wallet_private_key  # Metis Sepolia wallet private key
```

### 3. Create Your Bot

Create `tg-bot.py` with the following code:

```python
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from alith import Agent
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Alith Agent
agent = Agent(
    name="Telegram Bot Agent",
    model="gpt-4",
    preamble="""You are an advanced AI assistant.""",
)

# Initialize basic message handler
async def handle_message(update: Update, context: CallbackContext) -> None:
    response = agent.prompt(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def main():
    # Initialize bot
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Start bot
    print("🤖 Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
```

### 4. Add Token Management Features
Check the tg-bot.py file for full code reference.

Add these functions to your bot for token management:

```python
async def check_balance(contract_address: str, wallet_address: str) -> dict:
    """Check token balance"""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ERC20_ABI
    )
    balance = contract.functions.balanceOf(
        Web3.to_checksum_address(wallet_address)
    ).call()
    return balance

async def transfer_token(contract_address: str, to_address: str, amount: float) -> str:
    """Transfer tokens"""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=ERC20_ABI
    )
    
    # Build transaction
    transfer_txn = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount
    ).build_transaction({
        'chainId': 59902,  # Metis Sepolia
        'gas': 100000,
        'nonce': w3.eth.get_transaction_count(WALLET_ADDRESS),
    })
    
    # Sign and send
    signed_txn = w3.eth.account.sign_transaction(transfer_txn, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    
    return tx_hash.hex()
```

### 5. Run Your Bot

```bash
python tg-bot.py
```

## Available Commands

Once your bot is running, you can use these commands in Telegram:

```
/balance <contract_address> <wallet_address>
Check token balance

/transfer <contract_address> <to_address> <amount>
Transfer tokens

Or use natural language:
"Check balance for contract 0x... wallet 0x..."
"Transfer 100 tokens from contract 0x... to 0x..."
```

## Features

- AI-powered chat responses
- Token balance checking
- Token transfers
- Natural language command processing

## Deployment Tips

1. **Local Testing**:
   - Keep your `.env` file secure
   - Test all features before deployment

2. **Production Deployment**:
   - Deploy to AWS Lambda, Heroku, or your preferred platform
   - Set environment variables in your deployment platform
   - Monitor bot performance and errors

## Troubleshooting

Common issues and solutions:

1. **Bot not responding**:
   - Check if your bot token is correct
   - Ensure your bot is running
   - Verify internet connection

2. **Token operations failing**:
   - Confirm wallet has enough balance
   - Verify contract addresses are correct
   - Check Metis Sepolia network status

## Need Help?

- Check [python-telegram-bot docs](https://python-telegram-bot.readthedocs.io/)
- Visit [LazAI GitHub](https://github.com/0xLazAI/alith) for SDK updates
- Join Telegram development community

