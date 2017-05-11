import pytest


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
def crowdsale(chain, team_multisig):
    """Py.test fixture for creating a Mysterium crowdsale contract."""

    kwargs = {
        "_token": 0, 
        "_pricingStrategy": 0, 
        "_multisigWallet": 0, 
        "_start": 0, 
        "_end": 0, 
        "_minimumFundingGoal": 0,
    }

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumCrowdsale', deploy_kwargs=kwargs, deploy_transaction=tx)
    return contract

