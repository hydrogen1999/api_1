from fastapi import FastAPI, Request
from web3 import Web3
import json
import requests

app = FastAPI()
bsc_test = "https://data-seed-prebsc-1-s1.binance.org:8545/"
bsc = "https://bsc-dataseed.binance.org/"

@app.get("/") 
async def Welcome():
    return {"Hello World"}

@app.get("/balance")
async def Balance(address):
    web3 = Web3(Web3.HTTPProvider(bsc_test))
    balance = web3.eth.get_balance(address)
    return {"Balance": balance}

# 0x1a0a20590C787cAf455B73Df6c2F8b52B5Ae6285

@app.get("/tokens/{token_address}/{my_address}")
async def Tokens(token_address, my_address):
    web3 = Web3(Web3.HTTPProvider(bsc_test))

    url_eth = "https://api-testnet.bscscan.com/api"
    API_ENDPOINT = url_eth+"?module=contract&action=getabi&address="+str(token_address)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
    r = requests.get(url = API_ENDPOINT, headers=headers)
    response = r.json()
    abi=json.loads(response["result"])
    contract = web3.eth.contract(address=token_address, abi=abi)
    totalSupply = contract.functions.totalSupply().call()
    TS = web3.fromWei(totalSupply, "ether")
    balance = contract.functions.balanceOf(my_address).call()
    BL = web3.fromWei(balance, "ether")
    return {"Total Supply": TS, "Your Balance": BL}

@app.get("/getPrice/{A}/{B}")
async def getPrice(A,B):
    web3 = Web3(Web3.HTTPProvider(bsc))
    pancake_factory_address = web3.toChecksumAddress("0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73")
    TK_A = web3.toChecksumAddress(A)
    TK_B = web3.toChecksumAddress(B)
    InputTokenAddr = TK_A
    OutputTokenAddr = TK_B

    with open('pancake_factory.json', 'r') as abi_definition:
        abi = json.load(abi_definition)

    with open('pancakepair.json', 'r') as abi_definition:
        parsed_pair = json.load(abi_definition)
    
    contract = web3.eth.contract(address=pancake_factory_address, abi=abi)
    pair_address = contract.functions.getPair(InputTokenAddr,OutputTokenAddr).call()
    pair1 = web3.eth.contract(address=pair_address, abi=parsed_pair)
    reserves = pair1.functions.getReserves().call()
    reserve0 = reserves[0]
    reserve1 = reserves[1]
    return {"Pair A/B":reserve0/reserve1, "Pair B/A":reserve1/reserve0}