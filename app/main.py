from fastapi import FastAPI, File, UploadFile
from web3 import Web3
import json,requests, config
import solcx
from solcx import compile_standard

app = FastAPI()
bsc_test = "https://data-seed-prebsc-1-s1.binance.org:8545/"
bsc = "https://bsc-dataseed.binance.org/"

solcx.install_solc('v0.8.0')

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
    pancake = web3.toChecksumAddress(config.PANCAKE_FACTORY_ADDRESS)
    pancake_factory_address = web3.toChecksumAddress(pancake)
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

@app.get("/mintNFT/{receiver}/{type}/{rarity}")
async def mint(receiver, type:int, rarity:int):
    web3 = Web3(Web3.HTTPProvider(bsc_test))
    wallet = web3.toChecksumAddress(config.WALLET_ADDRESS)
    nft_address = web3.toChecksumAddress(config.NFT_ADDRESS)
    key = config.PRIVATE_KEY
    url_eth = "https://api-testnet.bscscan.com/api"
    API_ENDPOINT = url_eth+"?module=contract&action=getabi&address="+str(nft_address)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"}
    r = requests.get(url = API_ENDPOINT, headers=headers)
    response = r.json()
    abi=json.loads(response["result"])
    contractNFT = web3.eth.contract(address=nft_address, abi=abi)

    mint = contractNFT.functions.mintNFT(receiver, type, rarity).buildTransaction({
        'from': wallet,
        'gasPrice': web3.toWei('10', 'gwei'),
        'nonce': web3.eth.get_transaction_count(wallet)
    })
    signed_txn = web3.eth.account.sign_transaction(mint, private_key=key)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return {"Minted": web3.toHex(tx_token)}

@app.post("/deploy")
async def deployContract (rawfile: UploadFile, contractName):
    web3 = Web3(Web3.HTTPProvider(bsc_test))
    wallet = web3.toChecksumAddress(config.WALLET_ADDRESS)
    key = config.PRIVATE_KEY

    try:
        contents = rawfile.file.read()
        with open(rawfile.filename, 'wb') as f:
            f.write(contents)
    except Exception:
        return {"message": "There was an error uploading the file"}
    finally:
        rawfile.file.close()
    
    with open(f"{rawfile.filename}") as file: 
        contract = file.read()
    compiled_contract = compile_standard(
        {
            "language": "Solidity",
            "sources": {"test.sol":{"content":contract}},
            "settings": {"outputSelection": {"*": {"*": ["*"]}}},
        },
        solc_version="0.8.0",
    )
    with open("contract.json", "w") as file:
        json.dump(compiled_contract, file)
    bytecode = compiled_contract['contracts'][f'{rawfile.filename}'][f'{contractName}']['evm']['bytecode']['object']
    abi = compiled_contract['contracts'][f'{rawfile.filename}'][f'{contractName}']['abi']
    chainId = 97
    SimpleStorage = web3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = web3.eth.getTransactionCount(wallet)
    transaction = SimpleStorage.constructor().buildTransaction({'chainId': chainId, 'from': wallet, 'nonce': nonce, 'gasPrice': web3.eth.gas_price})
    signed_transaction = web3.eth.account.signTransaction(transaction, key)
    tx_hash = web3.eth.sendRawTransaction(signed_transaction.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    return {"contract": contract_address}