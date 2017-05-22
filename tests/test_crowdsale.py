import datetime

import pytest
from decimal import Decimal

from eth_utils import from_wei
from eth_utils import to_wei
from ethereum.tester import TransactionFailed
from web3.contract import Contract


from ico.tests.utils import time_travel
from ico.state import CrowdsaleState
from ico.utils import decimalize_token_amount


def in_chf(wei):
    """Convert amount to CHF using our test 120 rate."""
    return int(from_wei(wei, "ether") * 120)


@pytest.fixture
def bitcoin_suisse(accounts) -> str:
    """Fixture for BitcoinSuisse address."""
    return accounts[9]



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
def mysterium_finalize_agent(team_multisig, chain, mysterium_token, crowdsale, mysterium_pricing) -> Contract:

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
def crowdsale(chain, mysterium_token, mysterium_pricing, preico_starts_at, preico_ends_at, preico_funding_goal, team_multisig) -> Contract:
    token = mysterium_token

    args = [
        token.address,
        mysterium_pricing.address,
        team_multisig,
        preico_starts_at,
        preico_ends_at,
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


def test_caps(crowdsale, mysterium_pricing):
    """"Soft cap and hard cap match specification."""

    # We lose ~1 ETH precision in the conversions
    assert abs(in_chf(crowdsale.call().getMinimumFundingGoal()) - 700000) < 10

    soft_cap = mysterium_pricing.call().getSoftCapInWeis()
    assert abs(in_chf(soft_cap) -  6000000) < 10


def test_soft_cap_price(crowdsale, mysterium_pricing):
    """"Soft cap prices match the specification."""

    one_chf_in_eth = to_wei(1/120, "ether")

    # See we get correct price for one token
    tokens_bought = mysterium_pricing.call().calculatePrice(one_chf_in_eth, 0, 0, '0x0000000000000000000000000000000000000000', 8)

    assert tokens_bought == 1 * 10**8


def test_hard_cap_price(crowdsale, mysterium_pricing):
    """"Soft cap prices match the specification."""

    one_point_two_chf_in_eth = to_wei(1.2/120, "ether")

    soft_cap_goal = mysterium_pricing.call().getSoftCapInWeis()

    # See we get correct price for one token
    tokens_bought = mysterium_pricing.call().calculatePrice(one_point_two_chf_in_eth, soft_cap_goal + 1, 0, '0x0000000000000000000000000000000000000000', 8)

    assert tokens_bought == 1 * 10**8


def test_set_rate(crowdsale, mysterium_pricing, team_multisig):
    """"Set CHF rate before crowdsale begins."""

    assert mysterium_pricing.call().chfRate() == 120 * 10000
    mysterium_pricing.transact({"from": team_multisig}).setConversionRate(130 * 10000)
    assert mysterium_pricing.call().chfRate() == 130 * 10000


def test_set_rate_late(chain, crowdsale, mysterium_pricing, team_multisig):
    """"CHF rate cannot be set after the crowdsale starts.."""

    time_travel(chain, crowdsale.call().startsAt()+1)
    with pytest.raises(TransactionFailed):
        mysterium_pricing.transact({"from": team_multisig}).setConversionRate(130 * 10000)


def test_bitcoin_suisse(chain, ready_crowdsale, bitcoin_suisse, mysterium_pricing, team_multisig):
    """"Test BitcoinSuisse address whitelisting.

    Spec 3.2.
    """

    crowdsale = ready_crowdsale

    # Cannot transact initially
    assert crowdsale.call().getState() == CrowdsaleState.PreFunding

    with pytest.raises(TransactionFailed):
        crowdsale.transact({"from": bitcoin_suisse, "value": to_wei(10000, "ether")}).buy()

    # Now let's set rate and whitelist
    mysterium_pricing.transact({"from": team_multisig}).setConversionRate(130 * 10000)
    crowdsale.transact({"from": team_multisig}).setEarlyParicipantWhitelist(bitcoin_suisse, True)

    # Now BitcoinSuisse can execute
    crowdsale.transact({"from": bitcoin_suisse, "value": to_wei(10000, "ether")}).buy()


def test_set_minimum_funding_goal(crowdsale, team_multisig):
    """Reset minimum funding goal

    Spec 3.4.
    """

    # Original goal
    # We lose ~1 ETH precision in the conversions
    assert abs(in_chf(crowdsale.call().getMinimumFundingGoal()) - 700000) < 10

    # reset it
    crowdsale.transact({"from": team_multisig}).setMinimumFundingLimit(8123123 * 10000)

    # New goal
    # We lose ~1 ETH precision in the conversions
    new_goal_chf = in_chf(crowdsale.call().getMinimumFundingGoal())
    assert abs(new_goal_chf - 8123123) < 10


def test_trigger_soft_cap(started_crowdsale, team_multisig, customer, mysterium_pricing):
    """See that the soft cap trigger causes the end time rewind.

    Spec 3.5.
    """

    crowdsale = started_crowdsale

    # Let's first change the soft cap as the owner
    mysterium_pricing.transact({"from": team_multisig}).setSoftCapCHF(6000000 * 10000)

    old_ends_at = crowdsale.call().endsAt()

    # Some generous person comes and buy all tokens in the soft cap
    cap = mysterium_pricing.call().getSoftCapInWeis()
    crowdsale.transact({"from": customer, "value": cap+1}).buy()

    # We reached the cap
    assert crowdsale.call().isSoftCapReached()
    assert crowdsale.call().softCapTriggered()

    new_ends_at = crowdsale.call().endsAt()

    # Now buyers need to hurry
    assert new_ends_at < old_ends_at
    assert crowdsale.call().getState() == CrowdsaleState.Funding

    # We can still buy after the soft cap is triggered
    assert not crowdsale.call().isCrowdsaleFull()
    crowdsale.transact({"from": customer, "value": to_wei(1, "ether")}).buy()


def test_hard_cao_reached(started_crowdsale, team_multisig, customer, mysterium_pricing):
    """Crowdsale is full when the hard cap is reached.

    Spec 3.6.
    """

    crowdsale = started_crowdsale

    # Reset hard cap
    crowdsale.transact({"from": team_multisig}).setHardCapCHF(10000000 * 10000)

    hard_cap = crowdsale.call().getHardCap()

    # Some generous person comes and buy all tokens in the world
    crowdsale.transact({"from": customer, "value": hard_cap}).buy()

    # We reached the cap
    assert crowdsale.call().isCrowdsaleFull()
    assert crowdsale.call().getState() == CrowdsaleState.Success

    with pytest.raises(TransactionFailed):
        crowdsale.transact({"from": customer, "value": to_wei(1, "ether")}).buy()


def test_manual_release(started_crowdsale, mysterium_token, team_multisig):
    """Mysterium token transfers can be manually released by team multisig."""

    assert not mysterium_token.call().released()
    mysterium_token.transact({"from": team_multisig}).releaseTokenTransfer()
    assert mysterium_token.call().released()



def test_distribution_700k(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    # 700k

    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact().distribute(700000, 88)

    assert mysterium_finalize_agent.call().earlybird_percentage() > 0
    earlybird_coins = mysterium_finalize_agent.call().earlybird_coins()
    regular_coins = mysterium_finalize_agent.call().regular_coins()
    seed_coins = mysterium_finalize_agent.call().seed_coins()
    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    total_coins = mysterium_finalize_agent.call().total_coins()

    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference

    # You can use this for debugging:
    #print (" ", earlybird_coins, " ", regular_coins, " ", seed_coins, " ", future_round_coins, " ", foundation_coins, " ", team_coins, " ", total_coins, " ")

    assert earlybird_coins == 840000 * decimal_scale
    assert regular_coins == 0
    assert seed_coins == 528000 * decimal_scale
    assert future_round_coins == 220645161398103
    assert foundation_coins == 39716129051658
    assert team_coins == 44129032279620
    assert total_coins == 441290322796206
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 66825
    assert mysterium_finalize_agent.call().seed_coins_vault1() == 528000 * decimal_scale
    assert mysterium_finalize_agent.call().seed_coins_vault2() == 0


def test_distribution_1m(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    # 1M
    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact().distribute(1000000, 88)

    assert mysterium_finalize_agent.call().earlybird_percentage() > 0
    earlybird_coins = mysterium_finalize_agent.call().earlybird_coins()
    regular_coins = mysterium_finalize_agent.call().regular_coins()
    seed_coins = mysterium_finalize_agent.call().seed_coins()
    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    total_coins = mysterium_finalize_agent.call().total_coins()

    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference

    assert earlybird_coins == 120000000000000
    assert regular_coins == 0
    assert seed_coins == 52800000000000
    assert future_round_coins == 278709677520049
    assert foundation_coins == 50167741953608
    assert team_coins == 55741935504009
    assert total_coins == 557419355040099
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 62433
    assert mysterium_finalize_agent.call().seed_coins_vault1() == 52800000000000
    assert mysterium_finalize_agent.call().seed_coins_vault2() == 0


def test_distribution_2m(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    # 2M
    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact().distribute(2000001, 88)

    assert mysterium_finalize_agent.call().earlybird_percentage() > 0
    earlybird_coins = mysterium_finalize_agent.call().earlybird_coins()
    regular_coins = mysterium_finalize_agent.call().regular_coins()
    seed_coins = mysterium_finalize_agent.call().seed_coins()
    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    total_coins = mysterium_finalize_agent.call().total_coins()

    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference

    assert earlybird_coins == 240000120000000
    assert regular_coins == 0
    assert seed_coins == 52800000000000
    assert future_round_coins == 472258258187620
    assert foundation_coins == 85006486473771
    assert team_coins == 94451651637524
    assert total_coins == 944516516375240
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 76325
    assert mysterium_finalize_agent.call().seed_coins_vault1() == 52800000000000
    assert mysterium_finalize_agent.call().seed_coins_vault2() == 0


def test_distribution_5m(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    # 5M
    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact().distribute(5 * 1000000, 88)

    assert mysterium_finalize_agent.call().earlybird_percentage() > 0
    earlybird_coins = mysterium_finalize_agent.call().earlybird_coins()
    regular_coins = mysterium_finalize_agent.call().regular_coins()
    seed_coins = mysterium_finalize_agent.call().seed_coins()
    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    total_coins = mysterium_finalize_agent.call().total_coins()

    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference

    assert earlybird_coins == 600000000000000
    assert regular_coins == 0
    assert seed_coins == 211200000000000
    assert future_round_coins == 336524017516625
    assert foundation_coins == 127524890848405
    assert team_coins == 141694323164894
    assert total_coins == 1416943231648948
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 119024
    assert mysterium_finalize_agent.call().seed_coins_vault1() == 52800000000000
    assert mysterium_finalize_agent.call().seed_coins_vault2() == 158400000000000


def test_distribution_8m(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    # 8M
    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact().distribute(8 * 1000000, 88)

    assert mysterium_finalize_agent.call().earlybird_percentage() > 0
    earlybird_coins = mysterium_finalize_agent.call().earlybird_coins()
    regular_coins = mysterium_finalize_agent.call().regular_coins()
    seed_coins = mysterium_finalize_agent.call().seed_coins()
    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    total_coins = mysterium_finalize_agent.call().total_coins()

    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference

    assert earlybird_coins == 720000000000000
    assert regular_coins == 200000000000000
    assert seed_coins == 264000000000000
    assert future_round_coins == 269090909125338
    assert foundation_coins == 161454545475202
    assert team_coins == 179393939416892
    assert total_coins == 1793939394168921
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 151489
    assert mysterium_finalize_agent.call().seed_coins_vault1() == 52800000000000
    assert mysterium_finalize_agent.call().seed_coins_vault2() == 211200000000000
