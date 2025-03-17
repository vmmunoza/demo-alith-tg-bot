import os
from web3 import Web3
import json
from dotenv import load_dotenv
from alith import Agent

# Load environment variables
load_dotenv()

# Metis Sepolia Configuration
METIS_SEPOLIA_CONFIG = {
    'chain_id': 59902,
    'rpc_url': 'https://sepolia.metisdevops.link',
    'explorer_url': 'https://sepolia-explorer.metisdevops.link',
    'name': 'Metis Sepolia'
}

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(METIS_SEPOLIA_CONFIG['rpc_url']))

# ERC20 ABI (minimal for balance checks)
ERC20_ABI = '''[
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
    name="Metis Token Balance Agent",
    model="gpt-4",
    preamble="""You are an AI assistant for Metis L2 that can check ERC20 token balances.
    You can help users retrieve token information from the Metis Sepolia network.""",
)

def is_valid_address(address: str) -> bool:
    """Validate Ethereum address format"""
    return address and len(address) == 42 and address.startswith('0x') and all(c in '0123456789abcdefABCDEF' for c in address[2:])

def check_balance(contract_address: str, wallet_address: str) -> str:
    try:
        # Validate addresses
        if not is_valid_address(contract_address) or not is_valid_address(wallet_address):
            return "❌ Invalid address format. Addresses should be 42 characters long and start with '0x'"

        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=json.loads(ERC20_ABI)
        )
        
        # Get token info
        try:
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            name = contract.functions.name().call()
            total_supply = contract.functions.totalSupply().call()
        except Exception as e:
            return f"❌ Error reading token information: {str(e)}"
        
        # Get balance
        balance = contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        
        # Format balance with proper decimals
        formatted_balance = balance
        
        return (
            f"💰 Token Balance Report\n\n"
            f"Token Name: {name}\n"
            f"Symbol: {symbol}\n"
            f"Total Supply: {total_supply} {symbol}\n\n"
            f"Wallet: {wallet_address}\n"
            f"Balance: {formatted_balance} {symbol}\n\n"
            f"🔍 View on Explorer:\n"
            f"Token: {METIS_SEPOLIA_CONFIG['explorer_url']}/token/{contract_address}\n"
            f"Wallet: {METIS_SEPOLIA_CONFIG['explorer_url']}/address/{wallet_address}"
        )
    
    except Exception as e:
        return f"❌ Error checking balance: {str(e)}"

def main():
    print(f"🤖 Metis Token Balance Agent running on {METIS_SEPOLIA_CONFIG['name']}...")
    print("This agent can check ERC20 token balances. Type 'exit' to quit.")
    print("Format: check <contract_address> <wallet_address>")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: Goodbye! Have a great day!")
            break
        
        # Check if this is a balance check request
        if user_input.lower().startswith("check "):
            parts = user_input.split()
            if len(parts) >= 3:
                contract_address = parts[1]
                wallet_address = parts[2]
                
                print("🔍 Checking token balance...")
                result = check_balance(contract_address, wallet_address)
                print(f"Agent: {result}")
            else:
                print("Agent: Please provide both contract and wallet addresses.")
                print("Example: check 0x123... 0x456...")
        else:
            # Handle with the AI agent for other queries
            response = agent.prompt(user_input)
            print(f"Agent: {response}")

if __name__ == "__main__":
    main()
