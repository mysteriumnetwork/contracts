"""Basic token properties"""

import datetime

import pytest
from decimal import Decimal
from eth_utils import to_wei
from ethereum.tester import TransactionFailed
from web3.contract import Contract


from ico.tests.utils import time_travel
from ico.state import CrowdsaleState
from ico.utils import decimalize_token_amount

@pytest.fixture
def token_new_name() -> str:
    return "New name"

@pytest.fixture
def token_new_symbol() -> str:
    return "NEW"

@pytest.fixture
def mysterium_token(chain, team_multisig, token_name, token_symbol, initial_supply) -> Contract:
    """Create the token contract."""

    args = ["Mysterium", "MYST", 0, 8]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('CrowdsaleToken', deploy_args=args, deploy_transaction=tx)
    return contract


def test_token_interface(mysterium_token, team_multisig, token_new_name, token_new_symbol):
    """Deployed token properties are correct."""

    assert mysterium_token.call().totalSupply() == 0
    assert mysterium_token.call().symbol() == "MYST"
    assert mysterium_token.call().name() == "Mysterium"
    assert mysterium_token.call().decimals() == 8
    assert mysterium_token.call().owner() == team_multisig
    assert mysterium_token.call().upgradeMaster() == team_multisig

    mysterium_token.transact({"from": team_multisig}).setTokenInformation(token_new_name, token_new_symbol)
    assert mysterium_token.call().name() == token_new_name
    assert mysterium_token.call().symbol() == token_new_symbol
