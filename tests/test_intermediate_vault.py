"""Intermediate vault."""
import pytest
import time

from eth_utils import to_wei
from ethereum.tester import TransactionFailed
from ico.tests.utils import time_travel


@pytest.fixture
def vault_opens_at(chain, team_multisig):
    return int(time.time() + 30*24*3600)


@pytest.fixture
def vault(chain, team_multisig, vault_opens_at):
    """Create a vault that locks ETH for 30 days."""
    args = [team_multisig, vault_opens_at]

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('IntermediateVault', deploy_args=args, deploy_transaction=tx)
    return contract


@pytest.fixture
def depositor(accounts):
    return accounts[8]


def test_unlock_vault(chain, web3, vault, depositor, vault_opens_at, team_multisig):
    """Vault unlocks successfully."""
    # Money goes in
    test_value = to_wei(1000, "ether")

    vault_balance = web3.eth.getBalance(vault.address)
    team_multisig_balance = web3.eth.getBalance(team_multisig)
    web3.eth.sendTransaction({"from": depositor, "value": test_value, "to": vault.address})

    # Vault received ETH
    assert web3.eth.getBalance(vault.address) > vault_balance

    # Go to unlock date
    time_travel(chain, vault_opens_at+1)
    vault.transact({"from": depositor}).unlock()

    # Money was transferred to team multisig
    assert web3.eth.getBalance(team_multisig) - team_multisig_balance > test_value - 100000

    # Vault is empty now
    assert web3.eth.getBalance(vault.address) == 0


def test_unlock_vault_early(chain, web3, vault, depositor, vault_opens_at, team_multisig):
    """Vault unlock fails."""
    # Money goes in
    test_value = to_wei(1000, "ether")

    vault_balance = web3.eth.getBalance(vault.address)
    team_multisig_balance = web3.eth.getBalance(team_multisig)
    web3.eth.sendTransaction({"from": depositor, "value": test_value, "to": vault.address})

    # Vault received ETH
    assert web3.eth.getBalance(vault.address) > vault_balance

    # Go to unlock date
    time_travel(chain, vault_opens_at-1)
    with pytest.raises(TransactionFailed):
        vault.transact({"from": depositor}).unlock()

    # Money was transferred to team multisig
    assert web3.eth.getBalance(team_multisig) == team_multisig_balance

    # Vault is empty now
    assert web3.eth.getBalance(vault.address) == test_value


def test_two_deposts(chain, web3, vault, depositor, vault_opens_at, team_multisig):
    """Vault accepts several deposits."""
    # Money goes in
    test_value = to_wei(1000, "ether")
    test_value_2 = to_wei(3333, "ether")

    vault_balance = web3.eth.getBalance(vault.address)
    team_multisig_balance = web3.eth.getBalance(team_multisig)
    web3.eth.sendTransaction({"from": depositor, "value": test_value, "to": vault.address})
    web3.eth.sendTransaction({"from": depositor, "value": test_value_2, "to": vault.address})

    # Vault received ETH
    assert web3.eth.getBalance(vault.address) > vault_balance

    # Go to unlock date
    time_travel(chain, vault_opens_at+1)
    vault.transact({"from": depositor}).unlock()

    # Money was transferred to team multisig
    assert web3.eth.getBalance(team_multisig) - team_multisig_balance > (test_value + test_value_2) - 100000

    # Vault is empty now
    assert web3.eth.getBalance(vault.address) == 0


