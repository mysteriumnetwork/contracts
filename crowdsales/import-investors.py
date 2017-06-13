from ico.utils import check_succesful_tx
import populus
import time
from populus.utils.cli import request_account_unlock
from populus.utils.accounts import is_account_locked
from eth_utils import to_wei
from web3 import Web3
from web3.contract import Contract

import uuid

p = populus.Project()
account = "0x"  # Our controller account on Kovan

def import_investor_data(contract: Contract, deploy_address: str, fname: str):
    """Load investor data to a MultiVault contract.

    Mysterium specific data loader.

    :return: List of unconfirmed transaction ids
    """

    assert fname.endswith(".csv")

    txs = []
    with open(fname, "rt") as inp:
        for line in inp:
            address, amount = line.split(",")
            address = address.strip()
            amount = amount.strip()
            assert address.startswith("0x")
            amount = int(float(amount) * 1000000000)  # Use this precision. CHANGED
            if contract.call().balances(address) == 0:
                contract.transact({"from": deploy_address}).addInvestor(address, amount)
            #time.sleep(1)


with p.get_chain("mainnet") as chain:
    web3 = chain.web3
    Contract = getattr(chain.contract_factories, "MultiVault")
    seed_participant_vault1 = Contract(address="0x35AfB92d3F2bE0D206E808355ca7bfAc9d820735")
    seed_participant_vault2 = Contract(address="0x1962A6183412360Ca64eD34c111efDabF08b909B")
    founders_vault = Contract(address="0x33222541eaE599124dF510D02f6e70DAdA1a9331")

    import_investor_data(seed_participant_vault1, "0x6efD5665ab4B345A7eBE63c679b651f375DDdB7E", "seed_investor_data.csv")
    import_investor_data(seed_participant_vault2, "0x6efD5665ab4B345A7eBE63c679b651f375DDdB7E", "seed_investor_data.csv")
    import_investor_data(founders_vault, "0x6efD5665ab4B345A7eBE63c679b651f375DDdB7E", "founders_data.csv")
