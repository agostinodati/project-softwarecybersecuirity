from solcx import install_solc
from solcx import compile_source

from web3 import Web3
from web3.middleware import geth_poa_middleware

import configparser
import numpy as np
from os.path import isfile
import json
from datetime import datetime
from hashlib import sha256

from cryptography.fernet import Fernet
import ast

sc_new_event = './smart_contracts/Event.sol'
sc_ticket = './smart_contracts/Tickets.sol'
smart_contract_local = './smart_contracts/address_dict.npy'
ticket_smart_contract_local = './smart_contracts/ticket_address_dict.npy'

key_path = './smart_contracts/key.key'

ticket_smart_contracts_dict_global = {}
smart_contracts_dict_global = {}


def write_key():
    # generate the key and save it
    if isfile(key_path) is False:
        key = Fernet.generate_key()
        with open(key_path, "wb") as key_file:
            key_file.write(key)


def load_key():
    # load the key
    return open(key_path, "rb").read()


def get_smart_contracts_dict(mode):
    """
    Get the dictionary (name: address) of the smart contracts deployed on the blockchain.
    :return: Dictionary (name: address) of the smart contracts deployed on the blockchain
    """

    # TODO: Criptare il file locale, salvare in memoria una copia del dizionario per poter avere una copia di backup nel caso il file
    #      venga perso e salvare il tutto sul db. Risolvere problema omonimi.
    dictio = {}

    f = Fernet(load_key())

    if mode == "event":
        dictio = np.load(smart_contract_local, allow_pickle='TRUE').item()
        dict = ast.literal_eval(f.decrypt(dictio).decode())
    elif mode == "ticket_office":
        dictio = np.load(ticket_smart_contract_local, allow_pickle='TRUE').item()
        dict = ast.literal_eval(f.decrypt(dictio).decode())
    return dict


def store_smart_contract_address(name_contract, address_contract, abi, smart_contract_local_path):
    """
    This function will store the contract name and the address in a dictionary and in a file in the local system.
    :param smart_contract_local_path: path of where store the smart contract.
    :param name_contract: Contract's name
    :param address_contract: Contract's address
    :param abi: Contract's abi
    :param path: Path where to save the dict
    :return: Nothing
    """

    write_key()

    f = Fernet(load_key())

    if isfile(smart_contract_local_path):
        dict = np.load(smart_contract_local_path, allow_pickle='TRUE').item()
        read_dictionary = ast.literal_eval(f.decrypt(dict).decode())
        read_dictionary.update({name_contract: (address_contract, abi)})
    else:
        read_dictionary = {name_contract: (address_contract, abi)}
    np.save(smart_contract_local_path, f.encrypt(str(read_dictionary).encode()))

    return read_dictionary


def deploy_smart_contract_new_event(name_event, date_event, available_seats_event, ticket_price, artist_event,
                                    location_event, description_event, username):
    """
    This function create the smart contract of a new event added by the event manager.
    :param name_event: Name of the event
    :param date_event: Date when the event take place
    :param available_seats_event: Available seats of the event
    :param ticket_price: Price of the ticket
    :param artist_event: Name of the artist for the event
    :param location_event: Location of the event
    :param description_event: description of the event
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
        # print(compiled_sol)
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
            tx_hash = new_event_contract.constructor(name_event, date_event, available_seats_event, ticket_price,
                                                     artist_event, location_event, description_event).transact(
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
            name_event_smart_contract = event.functions.getName().call()  # Get the name of the smart contract event
        except Exception as e:
            error = e
            return None, error

        abi_str = json.dumps(abi)
        smart_contracts_dict = store_smart_contract_address(name_event_smart_contract,
                                                            address_event_smart_contract, abi_str, smart_contract_local)

        global smart_contracts_dict_global
        smart_contracts_dict_global = smart_contracts_dict.copy()

        return name_event_smart_contract, error


def get_address_abi(name, mode):
    """
    Obtains the address and the abi of the smart contract using the name of the event.
    :param mode: if event, load from the file of events, if ticket_office load the file oj tickets
    :param name: Name of the smart contract (event)
    :return: Address, abi
    """
    dict_event = get_smart_contracts_dict(mode)
    address, abi = dict_event[name]

    return address, abi


def get_event_information(username, name_event):
    """
    Get the information about the event using its name.
    :param username: Name of the user
    :param name_event: Event's name
    :return:
    """
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_event, abi_event = get_address_abi(name_event, "event")
        event = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            date_event = event.functions.getDate().call()
            available_seats_event = event.functions.getAvailableSeats().call()
            seats_price = event.functions.getSeatsPrice().call()

            artist_event = event.functions.getArtist().call()
            location_event = event.functions.getLocation().call()
            description_event = event.functions.getDescription().call()
        except Exception as e:
            return None, None, None, None, None, None, e

        return date_event, available_seats_event, seats_price, artist_event, location_event, description_event, None


def purchase_seats(username, name_event, seats_purchase):
    """
    Make a transaction to purchase event's seats from the reseller's side.
    :param username: Name of the reseller user
    :param name_event: Event's name
    :param seats_purchase: Number of seats to purchase
    :return: None if there aren't error or a string error.
    """
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        error = e
        return None, error

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_event, abi_event = get_address_abi(name_event, "event")
        event = w3.eth.contract(address=address_event, abi=abi_event)

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
            # Send the transaction.
            tx_hash = event.functions.purchaseSeats(seats_purchase).transact(transaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            return e

        return None


def deploy_ticket(event_name, address_event, ticket_price, seats_purchase, username):
    error = None

    install_solc('0.7.0')  # Install the compiler of Solidity
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    address_reseller = config[username]["address_node"]

    # Compile the smart contract
    try:
        source_code = open(sc_ticket, 'r').read()
        compiled_sol = compile_source(source_code)
    except Exception as e:
        error = e
        return None, error

    # Retrieve the contract interface and get bytecode / abi
    try:
        # waste first item in stack
        compiled_sol.popitem()

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

        address_reseller = w3.eth.accounts[0]

        ticket_office = w3.eth.contract(abi=abi, bytecode=bytecode)

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
            tx_hash = ticket_office.constructor(address_reseller, address_event, ticket_price, seats_purchase).transact(
                transaction)

            # Wait for the transaction to be mined, and get the transaction receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print('Transaction sent.')

        except Exception as e:
            print(e)
            error = e
            return None, error

        address_ticket_office = tx_receipt.contractAddress
        ticket = w3.eth.contract(address=address_ticket_office, abi=abi)

        abi_str = json.dumps(abi)
        ticket_smart_contracts_dict = store_smart_contract_address(event_name,
                                                                   address_ticket_office, abi_str,
                                                                   ticket_smart_contract_local)

        global ticket_smart_contracts_dict_global
        ticket_smart_contracts_dict_global = ticket_smart_contracts_dict.copy()

        return ticket_smart_contracts_dict, error


def create_ticket(username, price, seal):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    address_buyer = config[username]["address_node"]

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address, abi = get_address_abi("Ticket Office", "ticket_office")
        ticket_office = w3.eth.contract(address=address, abi=abi)

        timestamp = datetime.datetime.today()

        try:
            ticket_id = ticket_office.functions.createTicket(address_buyer, price, seal, timestamp)
        except Exception as e:
            return None, None, None, e

        return ticket_id, None


def get_reseller_events(username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    events = get_smart_contracts_dict("event")
    event_dict = events.keys()
    list_event_names = []
    for key in event_dict:
        list_event_names.append(key)

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        address_reseller = w3.eth.accounts[0]

        reseller_events = []

        for event_name in list_event_names:
            address_event, abi_event = get_address_abi(event_name, "event")
            event = w3.eth.contract(address=address_event, abi=abi_event)

            try:
                seats_reseller = event.functions.getReseller_seats(address_reseller).call()
                if seats_reseller > 0:
                    # reseller_events.append(event_name, (address_event, abi_event))
                    reseller_events.append(event_name)
            except Exception as e:
                return None, e

        return reseller_events, None


def get_reseller_tickets_for_event(event_name, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    # address_reseller = address_reseller.encode('utf-8')

    events = get_smart_contracts_dict("event")
    event_dict = events.keys()
    list_event_names = []
    for key in event_dict:
        list_event_names.append(key)

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        address_reseller = w3.eth.accounts[0]

        address_event, abi_event = get_address_abi(event_name, "event")
        event = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            seats_reseller = event.functions.getReseller_seats(address_reseller).call()
            return seats_reseller, None
        except Exception as e:
            return None, e

        return seats_reseller, None


def get_ticket_office_info(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_event, abi_event = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            ticket_price = ticket_office.functions.getTicketsPrice().call()
            ticket_remaining = ticket_office.functions.getRemainingTickets().call()
        except Exception as e:
            return None, None, e

        return ticket_price, ticket_remaining, None


def purchase_ticket(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    timestamp = datetime.now()
    timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        error = e
        return None, error

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        address_buyer = w3.eth.accounts[0]
        address_ticket, abi_ticket = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_ticket, abi=abi_ticket)

        # Submit the transaction that deploys the contract
        first_account = w3.eth.accounts[0]
        nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(first_account))
        transaction = {
            'from': first_account,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': 0
        }

        seal = sealer(address_buyer, address_ticket, timestamp)

        try:
            # Send the transaction.
            tx_hash = ticket_office.functions.purchaseTicket(address_buyer, username, seal, timestamp).transact(
                transaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            ticket_id = ticket_office.functions.getTicketIdByAddressBuyer(address_buyer).call()
            print("Transaction Completed.")
        except Exception as e:
            return None, e

        return ticket_id, None


def get_ticket_info(name_event, ticket_id, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_event, abi_event = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            ticket_state = ticket_office.functions.getState(ticket_id).call()
            ticket_seal = ticket_office.functions.getSeal(ticket_id).call()
            ticket_date = ticket_office.functions.getPurchaseTimestamp(ticket_id).call()
        except Exception as e:
            return None, None, None, e

        return ticket_state, ticket_seal, ticket_date, None


def get_event_state(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_event, abi_event = get_address_abi(name_event, "event")
        event = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            state = event.functions.getState().call()
        except Exception as e:
            None, e

        return state, None


def has_ticket(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        buyer_address = w3.eth.accounts[0]

        address_event, abi_event = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            ticket_id = ticket_office.functions.getTicketIdByAddressBuyer(buyer_address).call()
        except Exception as e:
            return None, e

        ticket_already_purchased = True

        if ticket_id == 0:
            ticket_already_purchased = False

        return ticket_already_purchased, ticket_id, None


def has_event(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        reseller_address = w3.eth.accounts[0]

        address_event, abi_event = get_address_abi(name_event, "event")
        event = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            event_purchased = event.functions.hasPurchased(reseller_address).call()
        except Exception as e:
            return None, e

        event_already_purchased = True

        if event_purchased == 0:
            event_already_purchased = False

        return event_already_purchased, None


def set_event_state(name_event, state, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        error = e
        return None, error

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_ticket, abi_ticket = get_address_abi(name_event, "event")
        event = w3.eth.contract(address=address_ticket, abi=abi_ticket)

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
            # Send the transaction.
            if state == "expired":
                tx_hash = event.functions.setExpiredState().transact(transaction)
            elif state == "cancelled":
                tx_hash = event.functions.setCancelledState().transact(transaction)
            elif state == "available":
                tx_hash = event.functions.setAvailableState().transact(transaction)
            else:
                return "State not valid. Valid states: expired, cancelled, available."

            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print("Transaction Completed.")
        except Exception as e:
            return e

        return None


def set_ticket_state(name_event, id, state, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        error = e
        return None, error

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender

        address_ticket, abi_ticket = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_ticket, abi=abi_ticket)

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
            # Send the transaction.
            if state == "valid":
                tx_hash = ticket_office.functions.setValidState(id).transact(transaction)
            elif state == "cancelled":
                tx_hash = ticket_office.functions.setCancelledState(id).transact(transaction)
            elif state == "obliterated":
                tx_hash = ticket_office.functions.setObliteratedState(id).transact(transaction)
            else:
                return "State not valid. Valid states: expired, cancelled, available."

            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print("Transaction Completed.")
        except Exception as e:
            return e

        return None


def get_ticket_office_counter(name_event, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")
        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        buyer_address = w3.eth.accounts[0]

        address_event, abi_event = get_address_abi(name_event, "ticket_office")
        ticket_office = w3.eth.contract(address=address_event, abi=abi_event)

        try:
            counter = ticket_office.functions.getTicketCounter().call()
        except Exception as e:
            return None, e

        return counter, None


def set_tickets_state(event_name, state, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")

        try:
            address_ticket_office, abi_ticket_office = get_address_abi(event_name, "ticket_office")
        except:
            return None

        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        address_reseller = w3.eth.accounts[0]

        first_account = w3.eth.accounts[0]
        nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(first_account))
        transaction = {
            'from': first_account,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': 0
        }

        ticket_office = w3.eth.contract(address=address_ticket_office, abi=abi_ticket_office)

        counter, error = get_ticket_office_counter(event_name, username)

        try:
            for id_ticket in range(counter):
                if state == "valid":
                    ticket_office.functions.setValidState((id_ticket+1)).transact(transaction)
                elif state == "cancelled":
                    ticket_office.functions.setCancelledState((id_ticket+1)).transact(transaction)
                elif state == "obliterated":
                    ticket_office.fucntions.setObliteratedState((id_ticket+1)).transact(transaction)
        except Exception as e:
            print(str(e))
        return None


def sealer(address_buyer, address_ticket, timestamp):
    seal = str(address_buyer) + str(address_ticket) + str(timestamp)
    hash_seal = sha256(seal.encode('utf-8')).hexdigest()
    print(hash_seal)
    return hash_seal


def getTicketList(event_name, username):
    config = configparser.ConfigParser()  # Use to access to the config file
    config.read('config.ini')

    try:
        w3 = Web3(Web3.HTTPProvider(config[username]["address_node"]))
    except Exception as e:
        return None, None, e

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if w3.isConnected():
        print("Connected to the blockchain.")

        try:
            address_ticket_office, abi_ticket_office = get_address_abi(event_name, "ticket_office")
        except:
            return None

        w3.eth.defaultAccount = w3.eth.accounts[0]  # Set the sender
        address_reseller = w3.eth.accounts[0]

        first_account = w3.eth.accounts[0]
        nonce = w3.eth.getTransactionCount(Web3.toChecksumAddress(first_account))
        transaction = {
            'from': first_account,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': 0
        }

        ticket_office = w3.eth.contract(address=address_ticket_office, abi=abi_ticket_office)

        try:
            list = ticket_office.functions.getTicketList().call()
        except Exception as e:
            return None, e

        return list, None