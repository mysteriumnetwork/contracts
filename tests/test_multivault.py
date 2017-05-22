"""Basic token properties"""

import time
from enum import IntEnum

import pytest
from ethereum.tester import TransactionFailed
from web3.contract import Contract


from ico.tests.utils import time_travel



class MultiVaultState(IntEnum):
    Unknown = 0
    Holding = 1
    Distributing = 2



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

    args = ["Mysterium", "MYST", 200, 8]  # Owner set

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MysteriumToken', deploy_args=args, deploy_transaction=tx)

    contract.transact({"from": team_multisig}).setReleaseAgent(team_multisig)
    contract.transact({"from": team_multisig}).releaseTokenTransfer()

    return contract


@pytest.fixture
def freeze_ends_at() -> int:
    """Timestamp when the vault unlocks."""
    return int(time.time() + 1000)


@pytest.fixture
def mysterium_multivault(chain, mysterium_mv_token, freeze_ends_at, customer, customer_2, team_multisig) -> Contract:
    args = [
        team_multisig,
        freeze_ends_at
    ]

    tx = {
        "from": team_multisig
    }

    contract, hash = chain.provider.deploy_contract('MultiVault', deploy_args=args, deploy_transaction=tx)
    contract.transact({"from": team_multisig}).setToken(mysterium_mv_token.address)
    contract.transact({"from": team_multisig}).addInvestor(customer, 30)
    contract.transact({"from": team_multisig}).addInvestor(customer_2, 35)
    contract.transact({"from": team_multisig}).addInvestor(customer_2, 35)
    return contract


def test_multi_vault_initial(mysterium_multivault, customer, customer_2, freeze_ends_at, team_multisig):
    """Multi vault holds the initial balances and state."""

    assert mysterium_multivault.call().balances(customer) == 30
    assert mysterium_multivault.call().balances(customer_2) == 70
    assert mysterium_multivault.call().getState() == MultiVaultState.Holding
    assert mysterium_multivault.call().freezeEndsAt() == freeze_ends_at
    assert mysterium_multivault.call().owner() == team_multisig


def test_fetch_balance(mysterium_multivault, customer, customer_2, freeze_ends_at, team_multisig, mysterium_mv_token):
    """Multi vault gets its token balance.."""

    # Load 200 tokens on the vaule
    mysterium_mv_token.transact({"from": team_multisig}).transfer(mysterium_multivault.address, mysterium_mv_token.call().totalSupply())

    mysterium_multivault.transact({"from": team_multisig}).fetchTokenBalance()
    assert mysterium_multivault.call().initialTokenBalance() == 200

    with pytest.raises(TransactionFailed):
        # Can be called only once
        mysterium_multivault.transact({"from": team_multisig}).fetchTokenBalance()


def test_multi_vault_distribute(chain, mysterium_multivault, preico_starts_at, mysterium_mv_token, team_multisig, customer, customer_2, mysterium_release_agent):
    """Check that multivaut acts correctly."""

    assert mysterium_mv_token.call().released()
    assert mysterium_mv_token.call().balanceOf(customer) == 0
    assert mysterium_mv_token.call().totalSupply() == 200

    # Load all 100% tokens to the vault for the test
    mysterium_mv_token.transact({"from": team_multisig}).transfer(mysterium_multivault.address, mysterium_mv_token.call().totalSupply())
    assert mysterium_mv_token.call().balanceOf(mysterium_multivault.address) == mysterium_mv_token.call().totalSupply()

    # Set the distribution balance
    mysterium_multivault.transact({"from": team_multisig}).fetchTokenBalance()

    # We pass the vault expiration date
    time_travel(chain, mysterium_multivault.call().freezeEndsAt() + 1)
    assert mysterium_multivault.call().getState() == MultiVaultState.Distributing

    # Check we calculate claims correctly
    assert mysterium_multivault.call().getClaimAmount(customer) + mysterium_multivault.call().getClaimAmount(customer_2) == 200
    assert mysterium_multivault.call().getClaimLeft(customer) + mysterium_multivault.call().getClaimLeft(customer_2) == 200

    # First customer gets his tokens
    assert mysterium_multivault.call().getClaimAmount(customer) == 60
    mysterium_multivault.transact({"from": customer}).claimAll()
    assert mysterium_mv_token.call().balanceOf(customer) == 60  # 200*3/10
    assert mysterium_multivault.call().getClaimLeft(customer) == 0

    # Then customer 2 claims his tokens in two batches
    mysterium_multivault.transact({"from": customer_2}).claim(20)
    assert mysterium_mv_token.call().balanceOf(customer_2) == 20

    assert mysterium_multivault.call().getClaimLeft(customer_2) == 120
    mysterium_multivault.transact({"from": customer_2}).claim(120)
    assert mysterium_mv_token.call().balanceOf(customer_2) == 140
    assert mysterium_multivault.call().getClaimLeft(customer_2) == 0


def test_multi_vault_claim_too_much(chain, mysterium_multivault, preico_starts_at, mysterium_mv_token, team_multisig, customer, customer_2, mysterium_release_agent):
    """Somebody tries to claim too many tokens."""

    assert mysterium_mv_token.call().released()
    assert mysterium_mv_token.call().balanceOf(customer) == 0
    assert mysterium_mv_token.call().totalSupply() == 200

    # Load all 100% tokens to the vault for the test
    mysterium_mv_token.transact({"from": team_multisig}).transfer(mysterium_multivault.address, mysterium_mv_token.call().totalSupply())
    assert mysterium_mv_token.call().balanceOf(mysterium_multivault.address) == mysterium_mv_token.call().totalSupply()

    # Set the distribution balance
    mysterium_multivault.transact({"from": team_multisig}).fetchTokenBalance()

    # We pass the vault expiration date
    time_travel(chain, mysterium_multivault.call().freezeEndsAt() + 1)
    assert mysterium_multivault.call().getState() == MultiVaultState.Distributing

    # First customer gets his tokens
    assert mysterium_multivault.call().getClaimAmount(customer) == 60
    with pytest.raises(TransactionFailed):
        mysterium_multivault.transact({"from": customer}).claim(61)



def test_multi_vault_claim_early(chain, mysterium_multivault, preico_starts_at, mysterium_mv_token, team_multisig, customer, customer_2, mysterium_release_agent):
    """Somebody tries to claim his tokens early."""

    assert mysterium_mv_token.call().released()
    assert mysterium_mv_token.call().balanceOf(customer) == 0
    assert mysterium_mv_token.call().totalSupply() == 200

    # Load all 100% tokens to the vault for the test
    mysterium_mv_token.transact({"from": team_multisig}).transfer(mysterium_multivault.address, mysterium_mv_token.call().totalSupply())
    assert mysterium_mv_token.call().balanceOf(mysterium_multivault.address) == mysterium_mv_token.call().totalSupply()

    # Set the distribution balance
    mysterium_multivault.transact({"from": team_multisig}).fetchTokenBalance()

    # We do not pass the vault expiration date
    time_travel(chain, mysterium_multivault.call().freezeEndsAt() - 1)
    assert mysterium_multivault.call().getState() == MultiVaultState.Holding

    # We can see the balance even before the transfer kicks in
    assert mysterium_multivault.call().getClaimAmount(customer) == 60

    # Early claim request fails
    with pytest.raises(TransactionFailed):
        mysterium_multivault.transact({"from": customer}).claim(1)
