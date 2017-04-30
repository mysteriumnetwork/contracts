import pytest


@pytest.fixture()
def team_multisig(accounts):
    """Team multisig address"""
    return accounts[0]  # accounts array comes from testrpc


@pytest.fixture()
def customer(accounts):
    """Test customer"""
    return account[0]  # accounts array comes from testrpc


@pytest.fixture()
def customer_2(accounts):
    """Test customer 2"""
    return customer_2[0]  # accounts array comes from testrpc


@pytest.fixture()
def token(chain):
    """Py.test fixture for creating a Mysterium token contract."""

    kwargs = {
        "_name": "Mysterium",
        "_symbol": "Myst",
        "_initialSupply": 0,
        "_decimals": 8,
    }

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('CrowdsaleToken', deploy_kwargs=kwargs, deploy_transaction=tx)
    return contract



