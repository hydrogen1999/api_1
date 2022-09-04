from fastapi import FastAPI, Request
from web3 import Web3
import json
import requests

app = FastAPI()
bsc = "https://data-seed-prebsc-1-s1.binance.org:8545/"
web3 = Web3(Web3.HTTPProvider(bsc))

@app.get("/") 
async def Welcome():
    return {"Hello World"}

@app.get("/balance")
async def Balance(address):
    balance = web3.eth.get_balance(address)
    return {"Balance": balance}

# 0x1a0a20590C787cAf455B73Df6c2F8b52B5Ae6285

@app.get("/tokens/{token_address}")
async def Tokens(token_address):
    url_eth = "https://api-testnet.bscscan.com/api"
    contract_address = web3.toChecksumAddress(token_address)
    API_ENDPOINT = url_eth+"?module=contract&action=getabi&address="+str(token_address)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
    r = requests.get(url = API_ENDPOINT, headers=headers)
    response = r.json()
    abi=json.loads(response["result"])
    contract = web3.eth.contract(address=token_address, abi=abi)
    totalSupply = contract.functions.totalSupply().call()

    return {"Total Supply": totalSupply}