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
def mysterium_release_agent(chain, team_multisig, mysterium_mv_token) -> Contract:
    """Create a simple release agent (useful for testing)."""

    args = [mysterium_mv_token.address]

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('SimpleReleaseAgent', deploy_args=args, deploy_transaction=tx)
    return contract

@pytest.fixture
def mysterium_mv_token(chain, team_multisig, token_name, token_symbol, initial_supply) -> Contract:
    """Create the token contract."""

    args = ["Mysterium", "MYST", 100, 8]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumToken', deploy_args=args, deploy_transaction=tx)
    return contract

@pytest.fixture
def mysterium_multivault(chain, mysterium_mv_token, preico_starts_at, customer, customer_2, team_multisig) -> Contract:
    args = [
        mysterium_mv_token.address,
        preico_starts_at,
        [
            customer,
            customer_2
        ],
        [
            50,
            50
        ],
        100
        ]

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MultiVault', deploy_args=args, deploy_transaction=tx)
    return contract;

def test_token_interface(chain, preico_starts_at, mysterium_mv_token, mysterium_multivault, team_multisig, customer, customer_2, mysterium_release_agent):
    """Deployed token properties are correct."""
    mysterium_mv_token.transact({"from": team_multisig}).setReleaseAgent(mysterium_release_agent.address)
    mysterium_release_agent.transact({"from": team_multisig}).release()
    assert mysterium_mv_token.call().balanceOf(customer) == 0
    assert mysterium_mv_token.call().totalSupply() == 100
    mysterium_mv_token.transact({"from": team_multisig}).transfer(mysterium_multivault.address, mysterium_mv_token.call().totalSupply());
    assert mysterium_mv_token.call().balanceOf(mysterium_multivault.address) == mysterium_mv_token.call().totalSupply()
    time_travel(chain, preico_starts_at + 100)
    mysterium_multivault.transact({"from": team_multisig}).unlock();
    assert mysterium_mv_token.call().balanceOf(customer) == 50
    assert mysterium_mv_token.call().balanceOf(customer_2) == 50
