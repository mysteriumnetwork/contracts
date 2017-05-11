import datetime

import pytest
from eth_utils import to_wei


@pytest.fixture()
def team_multisig(accounts):
    """Team multisig address"""
    return accounts[0]  # accounts array comes from testrpc


@pytest.fixture()
def customer(accounts):
    """Test customer"""
    return accounts[0]  # accounts array comes from testrpc


@pytest.fixture()
def customer_2(accounts):
    """Test customer 2"""
    return accounts[0]  # accounts array comes from testrpc


@pytest.fixture
def start_time() -> int:
    return int((datetime.datetime(2017, 4, 15, 16, 00) - datetime.datetime(1970, 1, 1)).total_seconds())


@pytest.fixture
def end_time(start_time) -> int:
    return int(start_time + 4*7*24*3600)

@pytest.fixture()
def token(chain, team_multisig):
    """Py.test fixture for creating a Mysterium token contract."""

    kwargs = {
        "_name": "Mysterium",
        "_symbol": "MYST",
        "_initialSupply": 0,
        "_decimals": 8,
    }

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumToken', deploy_kwargs=kwargs, deploy_transaction=tx)
    return contract


@pytest.fixture()
def pricing_strategy(chain, start_time, end_time):
    """TODO : Switch to Mysterium soft cap strategy"""

    week = 24*3600*7

    # TODO: Arguments not relevant here, placeholder pricing strategy
    args = [
        "0x0000000000000000000000000000000000000000",
        to_wei("0.05", "ether"),
        [
            start_time + 0, to_wei("0.10", "ether"),
            start_time + week*1, to_wei("0.12", "ether"),
            start_time + week*2, to_wei("0.13", "ether"),
            start_time + week*3, to_wei("0.14", "ether"),
            end_time, to_wei("0", "ether"),
        ],
    ]

    tx = {
        "gas": 4000000
    }
    contract, hash = chain.provider.deploy_contract('MilestonePricing', deploy_args=args, deploy_transaction=tx)
    return contract


@pytest.fixture()
def crowdsale(chain, token, team_multisig, start_time, end_time, pricing_strategy):
    """Py.test fixture for creating a Mysterium crowdsale contract."""

    kwargs = {
        "_token": token.address,
        "_pricingStrategy": pricing_strategy.address,
        "_multisigWallet": team_multisig,
        "_start": start_time,
        "_end": end_time,
        "_minimumFundingGoal": 0,
        "_maximumSellableTokens": 999,  # TODO: Take number from whitepaper
    }

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumCrowdsale', deploy_kwargs=kwargs, deploy_transaction=tx)
    return contract

