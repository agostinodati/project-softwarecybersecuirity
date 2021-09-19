from solcx import install_solc
from solcx import compile_source

from web3 import Web3
from web3.middleware import geth_poa_middleware

import configparser
import csv
from os.path import isfile

sc_new_event = './smart_contracts/New_event.sol'
sc_storage = './smart_contracts/Storage.sol'
smart_contract_local_path = './smart_contracts/address_list.txt'
smart_contracts_dict = {}


def get_smart_contracts_dict():
    """
    Get the dictionary (name: address) of the smart contracts deployed on the blockchain.
    :return: Dictionary (name: address) of the smart contracts deployed on the blockchain
    """
    return smart_contracts_dict.copy()


def store_smart_contract_address(name_contract, address_contract):
    """
    This function will store the contract name and the address in a dictionary and in a file in the local system.
    :param name_contract: Contract's name
    :param address_contract: Contract's address
    :param path: Path where to save the dict
    :return: Nothing
    """
    smart_contracts_dict.update({name_contract: address_contract})
    if not isfile(smart_contracts_dict):
        with open(smart_contracts_dict, 'w') as f:
            f.write('contract name;contract address')
    with open(smart_contract_local_path, 'a') as f:
        f.write(name_contract + ';' + address_contract)
        f.write('\n')


def get_smart_contract_file_dict():
    with open(smart_contract_local_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        # TODO: Need to complete


def deploy_smart_contract_new_event(name_event, date_event, available_seats_event, username):
    """
    This function create the smart contract of a new event added by the event manager.
    :param name_event: Name of the event
    :param date_event: Date when the event take place
    :param available_seats_event: Available seats of the event
    :param username: Name of the user that add the event
    :return: Name of the smart contract and an error string
    """
    error = 'No error'

    install_solc('0.7.0')  # Install the compiler of Solidity
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    # Compile the smart contract
    try:
        source_code = open(sc_new_event, 'r').read()
        compiled_sol = compile_source(source_code)
        print(compiled_sol)
    except Exception as e:
        error = e
        return None, error

    # Retrieve the contract interface and get bytecode / abi
    try:
        contract_id, contract_interface = compiled_sol.popitem()
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
    except Exception as e:
        error = e
        return None, error

    # web3 instance
    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        error = e
        return None, error

    # Inject the poa compatibility middleware to the innermost layer
    # Done to solve the error about dimension block
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

        try:
            print('Sending the transaction...')
            tx_hash = new_event_contract.constructor(name_event, date_event, available_seats_event).transact(
                transaction)

            # Wait for the transaction to be mined, and get the transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print('Transaction sent.')
        except Exception as e:
            error = e
            return None, error

        address_event_smart_contract = tx_receipt.contractAddress
        event = w3.eth.contract(address=address_event_smart_contract, abi=abi)

        try:
            name_event_smart_contract = event.functions.get_name().call()  # Get the name of the smart contract event
        except Exception as e:
            error = e
            return None, error

        store_smart_contract_address(name_event_smart_contract, address_event_smart_contract)

        print(smart_contracts_dict)

        return name_event_smart_contract, error
