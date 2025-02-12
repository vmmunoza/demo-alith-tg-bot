import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
from alith import Agent
from web3 import Web3
from eth_account import Account
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def is_valid_address(address: str) -> bool:
    """Validate Ethereum address format"""
    if not address:
        return False
    # Check if address starts with '0x' and is 42 characters long
    if not isinstance(address, str) or not address.startswith('0x') or len(address) != 42:
        return False
    # Check if the address contains only valid hexadecimal characters after '0x'
    try:
        int(address[2:], 16)  # Try to convert the address (without '0x') to int
        return True
    except ValueError:
        return False

# Get private key from environment variable
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY not found in environment variables")

# Metis Sepolia Configuration
METIS_SEPOLIA_CONFIG = {
    'chain_id': 59902,
    'rpc_url': 'https://sepolia.metisdevops.link',
    'explorer_url': 'https://sepolia-explorer.metisdevops.link',
    'name': 'Metis Sepolia'
}

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(METIS_SEPOLIA_CONFIG['rpc_url']))

# Get the wallet address from private key
WALLET_ADDRESS = Account.from_key(PRIVATE_KEY).address

# ERC20 ABI with transfer function
ERC20_ABI = '''[
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "name",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "symbol",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "initialSupply",
                "type": "uint256"
            },
            {
                "internalType": "address",
                "name": "owner",
                "type": "address"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address"
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "to",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "transfer",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]'''

# Initialize Alith Agent
agent = Agent(
    name="Telegram Bot Agent",
    model="gpt-4",
    preamble="""You are an advanced AI assistant built by [Alith](https://github.com/0xLazAI/alith).""",
)

async def get_token_info(contract_address: str) -> dict:
    """Get comprehensive token information"""
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=json.loads(ERC20_ABI)
        )
        
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call()
        
        return {
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "total_supply": total_supply,
            "formatted_supply": total_supply / (10 ** decimals)
        }
    except Exception as e:
        raise Exception(f"Error getting token info: {str(e)}")

async def check_token_balance(contract_address: str, wallet_address: str) -> tuple:
    """Check token balance and return balance with decimals"""
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=json.loads(ERC20_ABI)
    )
    
    token_info = await get_token_info(contract_address)
    balance = contract.functions.balanceOf(
        Web3.to_checksum_address(wallet_address)
    ).call()
    
    return balance, token_info["decimals"], token_info["symbol"]

async def transfer_token(contract_address: str, to_address: str, amount: float) -> str:
    """Transfer tokens using the private key from .env"""
    try:
        if not is_valid_address(contract_address) or not is_valid_address(to_address):
            return "❌ Invalid address format. Addresses should be 42 characters long and start with '0x'"

        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=json.loads(ERC20_ABI)
        )

        # Get token info
        token_info = await get_token_info(contract_address)
        decimals = token_info["decimals"]

        # Convert amount to token units
        amount_in_units = int(amount * (10 ** decimals))

        # Check balance before transfer
        balance_raw = contract.functions.balanceOf(WALLET_ADDRESS).call()
        formatted_balance = balance_raw / (10 ** decimals)
        
        # Build transfer transaction
        nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
        gas_price = w3.eth.gas_price

        transfer_txn = contract.functions.transfer(
            Web3.to_checksum_address(to_address),
            amount_in_units
        ).build_transaction({
            'chainId': METIS_SEPOLIA_CONFIG['chain_id'],
            'gas': 100000,  # Estimate gas limit
            'gasPrice': gas_price,
            'nonce': nonce,
            'from': WALLET_ADDRESS,
        })

        # Sign and send transaction
        try:
            # Try newer Web3.py version method
            signed_txn = w3.eth.account.sign_transaction(transfer_txn, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        except AttributeError:
            # Fallback for older Web3.py versions
            signed_txn = Account.sign_transaction(transfer_txn, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            return (
                f"✅ Transfer Successful!\n\n"
                f"Token: {token_info['name']} ({token_info['symbol']})\n"
                f"Amount: {amount:,.2f} {token_info['symbol']}\n"
                f"From: {WALLET_ADDRESS}\n"
                f"To: {to_address}\n\n"
                f"🔍 View transaction:\n"
                f"{METIS_SEPOLIA_CONFIG['explorer_url']}/tx/{receipt['transactionHash'].hex()}"
            )
        else:
            return "❌ Transfer failed. Transaction reverted."

    except Exception as e:
        return f"❌ Error during transfer: {str(e)}"


async def handle_transfer(update: Update, context: CallbackContext) -> None:
    """Handle the transfer command"""
    try:
        params = update.message.text.split()
        if len(params) != 4:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "Please use the format:\n"
                    "/transfer <contract_address> <to_address> <amount>"
                )
            )
            return

        _, contract_address, to_address, amount = params
        
        # Check current balance first
        try:
            balance, decimals, symbol = await check_token_balance(contract_address, WALLET_ADDRESS)
            formatted_balance = balance / (10 ** decimals)
            
            # Send initial status with balance info
            status_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔄 Processing transfer...\nCurrent balance: {formatted_balance:.2f} {symbol}"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error checking balance: {str(e)}"
            )
            return

        # Execute transfer
        result = await transfer_token(contract_address, to_address, float(amount))
        
        # Update with result
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text=result
        )

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Invalid amount format. Please provide a valid number."
        )

async def check_balance_command(update: Update, context: CallbackContext) -> None:
    """Handle the /balance command"""
    try:
        params = update.message.text.split()
        if len(params) != 3:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "Please provide contract and wallet address:\n"
                    "/balance <contract_address> <wallet_address>"
                )
            )
            return

        _, contract_address, wallet_address = params
        
        if not is_valid_address(contract_address) or not is_valid_address(wallet_address):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Invalid address format. Addresses should be 42 characters long and start with '0x'"
            )
            return

        # Send initial status
        status_message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔍 Checking token balance..."
        )

        # Get balance and token info
        balance, decimals, symbol = await check_token_balance(contract_address, wallet_address)
        token_info = await get_token_info(contract_address)
        
        formatted_balance = balance / (10 ** decimals)
        
        # Calculate percentage of total supply
        percentage = (formatted_balance / token_info["formatted_supply"]) * 100 if token_info["formatted_supply"] > 0 else 0

        # Format response
        response = (
            f"💰 Token Balance Report\n\n"
            f"Token Information:\n"
            f"• Name: {token_info['name']}\n"
            f"• Symbol: {token_info['symbol']}\n"
            f"• Decimals: {token_info['decimals']}\n"
            f"• Total Supply: {token_info['total_supply']} {token_info['symbol']}\n\n"
            f"Wallet Information:\n"
            f"• Address: {wallet_address}\n"
            f"• Balance: {balance} {token_info['symbol']}\n"
            f"• % of Supply: {percentage:.4f}%\n\n"
            f"🔍 View on Explorer:\n"
            f"• Token: {METIS_SEPOLIA_CONFIG['explorer_url']}/token/{contract_address}\n"
            f"• Wallet: {METIS_SEPOLIA_CONFIG['explorer_url']}/address/{wallet_address}"
        )

        # Update with result
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text=response
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Error checking balance: {str(e)}"
        )

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages"""
    message_text = update.message.text.lower()
    
    if message_text.startswith('/balance'):
        await check_balance_command(update, context)
    elif message_text.startswith('/transfer'):
        await handle_transfer(update, context)
    elif "check balance" in message_text:
        # Handle natural language balance checks
        try:
            words = message_text.split()
            addresses = [word for word in words if is_valid_address(word)]
            
            if len(addresses) < 2:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "Please provide both contract and wallet addresses.\n"
                        "Example: Check balance for contract 0x123... wallet 0x456..."
                    )
                )
                return
                
            contract_address = addresses[0]
            wallet_address = addresses[1]
            
            # Reuse the check_balance_command logic
            update.message.text = f"/balance {contract_address} {wallet_address}"
            await check_balance_command(update, context)
            
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error: {str(e)}"
            )
    elif "transfer" in message_text:
        # Handle natural language transfers
        try:
            words = message_text.split()
            addresses = [word for word in words if is_valid_address(word)]
            amounts = [word for word in words if word.replace('.', '').isdigit()]
            
            if len(addresses) < 2 or not amounts:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "Please provide contract address, recipient address, and amount.\n"
                        "Example: Transfer 100 tokens from contract 0x123... to 0x456..."
                    )
                )
                return
                
            contract_address = addresses[0]
            to_address = addresses[1]
            amount = float(amounts[0])
            
            # Reuse the handle_transfer logic
            update.message.text = f"/transfer {contract_address} {to_address} {amount}"
            await handle_transfer(update, context)
            
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error: {str(e)}"
            )
    else:
        # Handle other messages with AI agent
        response = agent.prompt(update.message.text)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def main():
    # Initialize bot
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Add handlers
    app.add_handler(CommandHandler("balance", check_balance_command))
    app.add_handler(CommandHandler("transfer", handle_transfer))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Start bot
    print(f"🤖 Bot starting on {METIS_SEPOLIA_CONFIG['name']}...")
    print(f"🔑 Using wallet address: {WALLET_ADDRESS}")
    print("Available commands:")
    print("1. /balance <contract_address> <wallet_address>")
    print("2. /transfer <contract_address> <to_address> <amount>")
    print("3. Natural language: 'Check balance for contract 0x... wallet 0x...'")
    print("4. Natural language: 'Transfer 100 tokens from contract 0x... to 0x...'")
    app.run_polling()

if __name__ == "__main__":
    main()