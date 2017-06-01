from ico.utils import check_succesful_tx
import populus
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
            amount = int(float(amount) * 10000)  # Use this precision
            if contract.call().balances(address) == 0:
                contract.transact({"from": deploy_address}).addInvestor(address, amount)


with p.get_chain("kovan") as chain:
    web3 = chain.web3
    Contract = getattr(chain.contract_factories, "MultiVault")
    seed_participant_vault1 = Contract(address="0x6d73EA22232aF29465A6a5070F32e199bF1D11e9")
    seed_participant_vault2 = Contract(address="0xbcd575b7D3187251752300892aD680A63a0e0050")

    import_investor_data(seed_participant_vault1, "0x001FC7d7E506866aEAB82C11dA515E9DD6D02c25", "fake_seed_investor_data.csv")
    import_investor_data(seed_participant_vault2, "0x001FC7d7E506866aEAB82C11dA515E9DD6D02c25", "fake_seed_investor_data.csv")
