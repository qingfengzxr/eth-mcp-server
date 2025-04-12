# basic import 
from mcp.server.fastmcp import FastMCP
from web3 import Web3
import json
import requests
from typing import Dict, List, Optional, Union, Any

# instantiate an MCP server client
mcp = FastMCP("Ethereum Blockchain Info")

RPC_URL = "https://eth.llamarpc.com"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# 以太坊Market API
ETH_PRICE_API = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
# Etherscan API，need to replace with your own API key
ETHERSCAN_API_KEY = "REPLACE_WITH_YOUR_API_KEY"
ETHERSCAN_API = "https://api.etherscan.io/api"

# DEFINE TOOLS

@mcp.tool()
def get_eth_balance(address: str) -> str:
    """
    Get ETH balance of an Ethereum address
    """
    if not w3.is_address(address):
        return f"Invalid Ethereum address: {address}"
    
    try:
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        return f"{balance_eth} ETH"
    except Exception as e:
        return f"Error getting balance: {str(e)}"

@mcp.tool()
def get_eth_price() -> str:
    """
    Get current Ethereum price in USD
    """
    try:
        response = requests.get(ETH_PRICE_API)
        data = response.json()
        price = data['ethereum']['usd']
        return f"${price}"
    except Exception as e:
        return f"Error getting price: {str(e)}"

@mcp.tool()
def get_gas_price() -> str:
    """
    Get current Ethereum network gas price
    """
    try:
        gas_price_wei = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price_wei, 'gwei')
        return f"{gas_price_gwei} Gwei"
    except Exception as e:
        return f"Error getting gas price: {str(e)}"

@mcp.tool()
def get_latest_block() -> Dict[str, Any]:
    """
    Get latest block information
    """
    try:
        latest_block = w3.eth.get_block('latest')
        # Return only useful information
        return {
            "number": latest_block.number,
            "timestamp": latest_block.timestamp,
            "miner": latest_block.miner,
            "transaction_count": len(latest_block.transactions),
            "gas_used": latest_block.gasUsed,
            "gas_limit": latest_block.gasLimit
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_transaction(tx_hash: str) -> Dict[str, Any]:
    """
    Get transaction details
    """
    try:
        tx = w3.eth.get_transaction(tx_hash)
        if tx is None:
            return {"error": "Transaction not found"}
        
        # Return only useful information
        return {
            "hash": tx.hash.hex(),
            "from": tx["from"],
            "to": tx.to,
            "value": w3.from_wei(tx.value, 'ether'),
            "gas": tx.gas,
            "gas_price": w3.from_wei(tx.gasPrice, 'gwei'),
            "nonce": tx.nonce,
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def estimate_tx_fee(gas_amount: int) -> str:
    """
    Estimate transaction fee
    """
    try:
        gas_price_wei = w3.eth.gas_price
        fee_wei = gas_price_wei * gas_amount
        fee_eth = w3.from_wei(fee_wei, 'ether')
        return f"{fee_eth} ETH"
    except Exception as e:
        return f"Error estimating fee: {str(e)}"

@mcp.tool()
def get_account_transactions(address: str, page: int = 1, offset: int = 20) -> Dict[str, Any]:
    """
    Get all transaction history for an account
    
    Parameters:
    address: Ethereum address
    page: Page number (starts from 1)
    offset: Number of records per page (max 10000)
    """
    if not w3.is_address(address):
        return {"error": f"Invalid Ethereum address: {address}"}
    
    try:
        # Use Etherscan API to get transaction history
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": offset,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY
        }
        
        response = requests.get(ETHERSCAN_API, params=params)
        data = response.json()
        
        if data["status"] != "1":
            return {"error": data["message"]}
        
        # Process transaction data
        transactions = []
        for tx in data["result"]:
            transactions.append({
                "hash": tx["hash"],
                "blockNumber": int(tx["blockNumber"]),
                "timestamp": int(tx["timeStamp"]),
                "from": tx["from"],
                "to": tx["to"],
                "value": w3.from_wei(int(tx["value"]), 'ether'),
                "gas": int(tx["gas"]),
                "gasPrice": w3.from_wei(int(tx["gasPrice"]), 'gwei'),
                "isError": tx["isError"] == "1",
                "txreceipt_status": tx["txreceipt_status"]
            })
        
        return {
            "address": address,
            "page": page,
            "offset": offset,
            "transactions": transactions
        }
    except Exception as e:
        return {"error": str(e)}

# DEFINE RESOURCES

@mcp.resource("ethereum://price")
def eth_price_resource() -> Dict[str, Any]:
    """Get Ethereum price information resource"""
    try:
        response = requests.get(ETH_PRICE_API)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("ethereum://stats")
def eth_stats_resource() -> Dict[str, Any]:
    """Get Ethereum network statistics resource"""
    try:
        latest_block = w3.eth.get_block('latest')
        gas_price = w3.eth.gas_price
        
        return {
            "latest_block": latest_block.number,
            "gas_price_gwei": w3.from_wei(gas_price, 'gwei'),
            "is_connected": w3.is_connected(),
            "peer_count": w3.net.peer_count
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("ethereum://address/{address}")
def address_info(address: str) -> Dict[str, Any]:
    """Get information resource for the specified address"""
    if not w3.is_address(address):
        return {"error": f"Invalid Ethereum address: {address}"}
    
    try:
        balance_wei = w3.eth.get_balance(address)
        return {
            "address": address,
            "balance_eth": w3.from_wei(balance_wei, 'ether'),
            "balance_wei": balance_wei,
            "transaction_count": w3.eth.get_transaction_count(address)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.resource("ethereum://address/{address}/transactions")
def address_transactions(address: str) -> Dict[str, Any]:
    """Get transaction history resource for the specified address"""
    return get_account_transactions(address)

# execute and return the stdio output
if __name__ == "__main__":
    mcp.run(transport="stdio")
