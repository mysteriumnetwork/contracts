"""Test fixtures."""
import datetime

import pytest
from web3.contract import Contract


from ico.tests.utils import time_travel
from ico.state import CrowdsaleState
from ico.tests.fixtures.general import *  # noqa
from ico.tests.fixtures.flatprice import *  # noqa
from ico.tests.fixtures.releasable import *  # noqa
from ico.tests.fixtures.finalize import *  # noqa
from ico.tests.fixtures.presale import *  # noqa


@pytest.fixture
def starts_at() -> int:
    """When pre-ico opens"""
    return int(datetime.datetime(2017, 1, 1).timestamp())


@pytest.fixture
def ends_at() -> int:
    """When pre-ico closes"""
    return int(datetime.datetime(2017, 2, 3).timestamp())


@pytest.fixture
def mysterium_token(chain, team_multisig, token_name, token_symbol, initial_supply) -> Contract:
    """Create the token contract."""

    args = ["Mysterium", "MYST", 0, 8]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumToken', deploy_args=args, deploy_transaction=tx)
    return contract


@pytest.fixture
def mysterium_finalize_agent(team_multisig, chain, mysterium_token, crowdsale, mysterium_pricing, accounts) -> Contract:
    # Create finalizer contract
    args = [
        mysterium_token.address,
        crowdsale.address,
        mysterium_pricing.address
    ]
    tx = {
        "from": team_multisig
    }
    contract, hash = chain.provider.deploy_contract('MysteriumTokenDistribution', deploy_args=args, deploy_transaction=tx)

    contract.transact({"from": team_multisig}).setVaults(
        _earlybirdVault=accounts[0],
        _regularVault=accounts[0],
        _seedVault=accounts[0],
        _futureRoundVault=accounts[0],
        _foundationVault=accounts[0],
        _teamVault=accounts[0],
        _seedVault1=accounts[0],
        _seedVault2=accounts[0])  # TODO: Use actual contracts here
    return contract


@pytest.fixture
def mysterium_pricing(chain, preico_token_price, team_multisig) -> Contract:
    """Flat pricing contact."""
    args = [
        120000  # 120 CHF = 1 ETH at the scale of 10000
    ]
    tx = {
        "from": team_multisig,
    }
    pricing_strategy, hash = chain.provider.deploy_contract('MysteriumPricing', deploy_args=args,  deploy_transaction=tx)
    return pricing_strategy


@pytest.fixture
def crowdsale(chain, mysterium_token, mysterium_pricing, starts_at, ends_at, preico_funding_goal, team_multisig) -> Contract:
    token = mysterium_token

    args = [
        token.address,
        mysterium_pricing.address,
        team_multisig,
        starts_at,
        ends_at,
    ]
    tx = {
        "from": team_multisig,
    }
    contract, hash = chain.provider.deploy_contract('MysteriumCrowdsale', deploy_args=args, deploy_transaction=tx)

    mysterium_pricing.transact({"from": team_multisig}).setCrowdsale(contract.address)
    mysterium_pricing.transact({"from": team_multisig}).setConversionRate(120*10000)

    assert contract.call().owner() == team_multisig
    assert not token.call().released()

    # Allow pre-ico contract to do mint()
    token.transact({"from": team_multisig}).setMintAgent(contract.address, True)
    token.transact({"from": team_multisig}).setTransferAgent(contract.address, True)
    assert token.call().mintAgents(contract.address) == True

    return contract


@pytest.fixture()
def ready_crowdsale(crowdsale, mysterium_token, mysterium_finalize_agent, team_multisig):
    """Crowdsale waiting the time to start."""
    crowdsale.transact({"from": team_multisig}).setFinalizeAgent(mysterium_finalize_agent.address)  # Must be done before sending
    mysterium_token.transact({"from": team_multisig}).setReleaseAgent(team_multisig)
    mysterium_token.transact({"from": team_multisig}).setTransferAgent(mysterium_finalize_agent.address, True)
    mysterium_token.transact({"from": team_multisig}).setMintAgent(mysterium_finalize_agent.address, True)
    return crowdsale


@pytest.fixture()
def started_crowdsale(chain, ready_crowdsale):
    """Crowdsale that has been time traveled to funding state."""
    # Setup crowdsale to Funding state
    crowdsale = ready_crowdsale

    time_travel(chain, crowdsale.call().startsAt() + 1)
    assert crowdsale.call().getState() == CrowdsaleState.Funding
    return crowdsale
