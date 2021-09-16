from solcx import install_solc

from web3 import Web3
from web3.middleware import geth_poa_middleware
from solcx import compile_files, compile_source
import configparser

sc_new_event = './smart_contracts/New_event.sol'
sc_storage = './smart_contracts/Storage.sol'


def deploy_smart_contract_new_event(name_event, date_event, available_seats_event, username):
    install_solc('0.7.0')  # Install the compiler of Solidity
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    # Compile the smart contract
    source_code = open(sc_new_event, 'r').read()
    compiled_sol = compile_source(source_code)
    print(compiled_sol)

    # Retrieve the contract interface and get bytecode / abi
    contract_id, contract_interface = compiled_sol.popitem()
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']

    # web3 instance
    w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))

    # Inject the poa compatibility middleware to the innermost layer
    #  Done for the error about dimension block
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        new_event_contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # Submit the transaction that deploys the contract
        first_account = w3.eth.accounts[0]
        nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(first_account))
        transaction = {
            'from': first_account,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': 0
        }
        print('Send the transaction...')
        tx_hash = new_event_contract.constructor(name_event, date_event, available_seats_event).transact(transaction)
        # tx_hash = new_event_contract.constructor().transact(transaction)

        # Wait for the transaction to be mined, and get the transaction receipt
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print('Transaction sent.')

        # TODO: salva l'indirizzo in una lista
        event = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
        print(event)

        event_name_test = event.functions.get_name().call()
        print(event_name_test)
