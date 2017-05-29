"""Deploy all contracts using the deploy script."""
import os

import datetime
import pytest
from eth_utils import to_wei

from ico.deploy import _deploy_contracts
from ico.definition import load_crowdsale_definitions
from ico.state import CrowdsaleState
from ico.tests.utils import time_travel


from web3.contract import Contract


@pytest.fixture()
def deploy_address(accounts):
    """Operational control account"""
    return accounts[9]


@pytest.fixture()
def bitcoin_suisse(accounts):
    """BitcoinSuisse accounts."""
    return accounts[8]


@pytest.fixture()
def fake_seed_investor(accounts):
    """Test account planted in fake_seed_investor_data.csv"""
    return accounts[7]


@pytest.fixture
def everything_deployed(project, chain, web3, accounts, deploy_address):
    """Deploy our token plan."""
    yaml_filename = os.path.join(os.path.dirname(__file__), "..", "crowdsales", "mysterium-testrpc.yml")
    deployment_name = "kovan"
    chain_data = load_crowdsale_definitions(yaml_filename, deployment_name)
    runtime_data, statistics, contracts = _deploy_contracts(project, chain, web3, yaml_filename, chain_data, deploy_address)
    return contracts


@pytest.fixture()
def proxy_buyer_freeze_ends_at(chain, crowdsale) -> Contract:
    """When investors can reclaim."""
    return int(datetime.datetime(2017, 6, 10).timestamp())


@pytest.fixture
def proxy_buyer(project, chain, web3, customer, everything_deployed, deploy_address, proxy_buyer_freeze_ends_at):
    """Make a preico buy contract and see it gets tokens distributed"""

    # Create finalizer contract
    args = [
        deploy_address,
        proxy_buyer_freeze_ends_at,
        1,  # 1 wei
    ]
    proxy_buyer, hash = chain.provider.deploy_contract('PreICOProxyBuyer', deploy_args=args)

    # Do a purchase
    assert proxy_buyer.call().getState() == 1
    proxy_buyer.transact({"value": to_wei(10000, "ether"), "from": customer}).invest()

    # Set ICO
    proxy_buyer.transact({"from": deploy_address}).setCrowdsale(everything_deployed["crowdsale"].address)

    return proxy_buyer


def test_deploy_all(chain, web3, everything_deployed, proxy_buyer, deploy_address, bitcoin_suisse, customer, customer_2, fake_seed_investor):
    """Acceptance test to verify that token sale functions properly."""

    crowdsale = everything_deployed["crowdsale"]
    pricing_strategy = everything_deployed["pricing_strategy"]
    token_distribution = everything_deployed["token_distribution"]
    intermediate_vault = everything_deployed["intermediate_vault"]
    seed_participant_vault = everything_deployed["seed_participant_vault"]
    seed_participant_vault_2 = everything_deployed["seed_participant_vault_2"]
    founders_vault = everything_deployed["founders_vault"]
    future_funding_vault = everything_deployed["future_funding_vault"]
    token = everything_deployed["token"]
    team_multisig_funds = everything_deployed["team_multisig_funds"]

    assert crowdsale.call().getState() == CrowdsaleState.PreFunding

    # Let's set the daily rate
    assert pricing_strategy.call().owner() == deploy_address
    assert pricing_strategy.call().crowdsale() == crowdsale.address
    pricing_strategy.transact({"from": deploy_address}).setConversionRate(170 * 10000)

    # Bitcoinsuisse shows up
    crowdsale.transact({"from": deploy_address}).setEarlyParicipantWhitelist(bitcoin_suisse, True)
    crowdsale.transact({"from": bitcoin_suisse, "value": to_wei(500000 / 170, "ether")}).buy()
    assert token.call().balanceOf(bitcoin_suisse) > 0

    # Set up proxy buyer crowdsale addresses
    proxy_buyer.transact({"from": deploy_address}).setCrowdsale(crowdsale.address)

    # ICO starts
    time_travel(chain, crowdsale.call().startsAt() + 1)

    # Load proxy buyer money
    proxy_buyer.transact({"from": deploy_address}).buyForEverybody()
    assert token.call().balanceOf(proxy_buyer.address) > 0

    # All current money is in the intermediate vault
    assert web3.eth.getBalance(intermediate_vault.address) > 0

    # We are not yet in the soft cap
    assert not crowdsale.call().isSoftCapReached()

    one_chf_in_eth = to_wei(1 / 170, "ether")

    before_price = pricing_strategy.call().calculatePrice(one_chf_in_eth, crowdsale.call().weiRaised(), crowdsale.call().tokensSold(), '0x0000000000000000000000000000000000000000', 8)
    before_ends_at = crowdsale.call().endsAt()

    # Do a retail transaction that fills soft cap
    crowdsale.transact({"from": customer_2, "value": one_chf_in_eth * 6000000}).buy()
    assert crowdsale.call().isSoftCapReached()

    after_price = pricing_strategy.call().calculatePrice(one_chf_in_eth, crowdsale.call().weiRaised(), crowdsale.call().tokensSold(), '0x0000000000000000000000000000000000000000', 8)
    after_ends_at = crowdsale.call().endsAt()

    assert after_ends_at < before_ends_at  # End date got moved
    assert after_price < before_price  # We get less tokens per ETH

    # Let's close it by reaching end of time
    time_travel(chain, crowdsale.call().endsAt() + 1)

    # Check that we have distribution facts correct
    chf_raised, chf_rate = token_distribution.call().getDistributionFacts()
    assert chf_raised == 8199999
    assert chf_rate == 170

    # Finalize the sale
    assert crowdsale.call().getState() == CrowdsaleState.Success
    assert token_distribution.call().crowdsale() == crowdsale.address
    assert token_distribution.call().mysteriumPricing() == pricing_strategy.address

    crowdsale.transact({"from": deploy_address}).finalize()

    #
    # Finalize vaults
    #

    # Seed vault 1
    assert seed_participant_vault.address != seed_participant_vault_2.address  # Let's not mix vaults
    assert seed_participant_vault.call().getToken() == token.address  # Vault 1 is set up
    seed_participant_vault.transact({"from": deploy_address}).fetchTokenBalance()

    # Seed vault 2
    assert token_distribution.call().seed_coins_vault2() > 0  # We did distribute vault 2
    assert seed_participant_vault_2.call().getToken() == token.address  # Vault 2 is set up
    assert token.call().balanceOf(seed_participant_vault_2.address) > 0
    seed_participant_vault_2.transact({"from": deploy_address}).fetchTokenBalance()

    # Future vault
    assert token.call().balanceOf(future_funding_vault.address) > 0
    future_funding_vault.transact({"from": deploy_address}).fetchTokenBalance()

    # Founders vault
    assert token.call().balanceOf(founders_vault.address) > 0
    founders_vault.transact({"from": deploy_address}).fetchTokenBalance()

    #
    # Long timeline
    #

    # Money moves to multisig after two weeks
    time_travel(chain, crowdsale.call().endsAt() + 14*24*3600)
    money_before = web3.eth.getBalance(team_multisig_funds.address)
    intermediate_vault.transact({"from": deploy_address}).unlock()  # Move from intermediate to team funds
    money_after = web3.eth.getBalance(team_multisig_funds.address)
    assert money_after > money_before

    # Token is released after we have money in the multisig
    token.transact({"from": deploy_address}).releaseTokenTransfer()
    assert token.call().released()  # Participants can transfer the token
    assert token.call().mintingFinished()  # No more tokens can be created

    # Do a test transaction with a single token
    token.transact({"from": customer_2}).transfer(customer, 1*10**8)

    # Claim tokens from a preico contract
    old_balance = token.call().balanceOf(customer)
    proxy_buyer.transact({"from": customer}).claimAll()
    new_balance = token.call().balanceOf(customer)
    assert new_balance > old_balance

    # After 12 months, claim vaults
    time_travel(chain, crowdsale.call().endsAt() + 365 * 24*3600)

    # Claim seed vault 1, get seed investor tokens
    seed_participant_vault.transact({"from": fake_seed_investor}).claimAll()
    assert token.call().balanceOf(fake_seed_investor) > 0

    # Claim seed vault 2, get even more tokens
    old_balance = token.call().balanceOf(fake_seed_investor)
    seed_participant_vault_2.transact({"from": fake_seed_investor}).claimAll()
    new_balance = token.call().balanceOf(fake_seed_investor)
    assert new_balance > old_balance
