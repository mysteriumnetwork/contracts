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


def test_distribution_14m(chain, mysterium_token, preico_funding_goal, preico_starts_at, customer, mysterium_finalize_agent, started_crowdsale, team_multisig):
    crowdsale = started_crowdsale

    assert crowdsale.call().getState() == CrowdsaleState.Funding
    minimum = crowdsale.call().getMinimumFundingGoal()

    assert  mysterium_token.call().transferAgents(mysterium_finalize_agent.address) == True
    mysterium_finalize_agent.transact({"from": team_multisig}).distribute(14 * 1000000, 204)

    future_round_coins = mysterium_finalize_agent.call().future_round_coins()
    foundation_coins = mysterium_finalize_agent.call().foundation_coins()
    team_coins = mysterium_finalize_agent.call().team_coins()
    seed_coins_vault1 = mysterium_finalize_agent.call().seed_coins_vault1()
    seed_coins_vault2 = mysterium_finalize_agent.call().seed_coins_vault2()

    earlybird_coins = 771459337903602
    regular_coins = 757142793161612

    foundation_percentage = 9
    future_round_percentage = 15
    team_percentage = 10

    seed_multiplier = 5
    seed_raised_eth = 6000
    eth_chf_price = 204
    decimal_scale = 10**8  # 8 decimal points, this is here for every function for reference
    seed_coins = seed_raised_eth * eth_chf_price * seed_multiplier * decimal_scale
    assert seed_coins == 612000000000000

    percentage_of_three = 100 - foundation_percentage - team_percentage - future_round_percentage
    earlybird_percentage = earlybird_coins * percentage_of_three / (earlybird_coins+regular_coins+seed_coins)
    total_coins = earlybird_coins * 100 / earlybird_percentage
    assert total_coins == 3243336562220021

    assert future_round_coins + 3.1 == total_coins * future_round_percentage / 100
    assert team_coins + 2.06 == total_coins * team_percentage / 100
    assert foundation_coins - 198.1 == total_coins * foundation_percentage / 100
    assert seed_coins_vault1 == seed_coins / seed_multiplier
    assert seed_coins_vault2 == seed_coins - seed_coins / seed_multiplier

    assert future_round_coins == 486500484333000
    assert foundation_coins == 291900290600000
    assert team_coins == 324333656222000
    assert seed_coins_vault1 == 122400000000000
    assert seed_coins_vault2 == 489600000000000

    assert total_coins + 193 == earlybird_coins + regular_coins + future_round_coins + foundation_coins + team_coins + seed_coins_vault1 + seed_coins_vault2

