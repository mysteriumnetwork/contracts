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
def crowdsale(chain, uncapped_token, flat_pricing, preico_starts_at, preico_ends_at, preico_funding_goal, team_multisig) -> Contract:
    token = uncapped_token

    args = [
        token.address,
        flat_pricing.address,
        team_multisig,
        preico_starts_at,
        preico_ends_at,
        preico_funding_goal,
        preico_funding_goal
    ]
    tx = {
        "from": team_multisig,
    }
    contract, hash = chain.provider.deploy_contract('MysteriumCrowdsale', deploy_args=args, deploy_transaction=tx)

    assert contract.call().owner() == team_multisig
    assert not token.call().released()

    # Allow pre-ico contract to do mint()
    token.transact({"from": team_multisig}).setMintAgent(contract.address, True)
    assert token.call().mintAgents(contract.address) == True

    return contract

def test_distribution_700k(crowdsale, team_multisig):
    # 700K
    crowdsale.transact().distribute(700000, 88)

    earlybird_coins = crowdsale.call().earlybird_coins()
    regular_coins = crowdsale.call().regular_coins()
    seed_coins = crowdsale.call().seed_coins()
    future_round_coins = crowdsale.call().future_round_coins()
    foundation_coins = crowdsale.call().foundation_coins()
    team_coins = crowdsale.call().team_coins()
    total_coins = crowdsale.call().total_coins()

    assert earlybird_coins == 840000
    assert regular_coins == 0
    assert seed_coins == 528000
    assert future_round_coins == 2206451
    assert foundation_coins == 397161
    assert team_coins == 441290
    assert total_coins == 4412903
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 1
    assert crowdsale.call().seed_coins_vault1() == 528000
    assert crowdsale.call().seed_coins_vault2() == 0

def test_distribution_1m(crowdsale, team_multisig):
    # 1M
    crowdsale.transact().distribute(1 * 1000000, 88)

    earlybird_coins = crowdsale.call().earlybird_coins()
    regular_coins = crowdsale.call().regular_coins()
    seed_coins = crowdsale.call().seed_coins()
    future_round_coins = crowdsale.call().future_round_coins()
    foundation_coins = crowdsale.call().foundation_coins()
    team_coins = crowdsale.call().team_coins()
    total_coins = crowdsale.call().total_coins()

    assert earlybird_coins == 1200000
    assert regular_coins == 0
    assert seed_coins == 528000
    assert future_round_coins == 2787096
    assert foundation_coins == 501677
    assert team_coins == 557419
    assert total_coins == 5574193
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 1
    assert crowdsale.call().seed_coins_vault1() == 528000
    assert crowdsale.call().seed_coins_vault2() == 0

def test_distribution_2m(crowdsale, team_multisig):
    # 2M
    crowdsale.transact().distribute(2000001, 88)

    earlybird_coins = crowdsale.call().earlybird_coins()
    regular_coins = crowdsale.call().regular_coins()
    seed_coins = crowdsale.call().seed_coins()
    future_round_coins = crowdsale.call().future_round_coins()
    foundation_coins = crowdsale.call().foundation_coins()
    team_coins = crowdsale.call().team_coins()
    total_coins = crowdsale.call().total_coins()

    assert earlybird_coins == 2400001
    assert regular_coins == 0
    assert seed_coins == 528000
    assert future_round_coins == 4722582
    assert foundation_coins == 850064
    assert team_coins == 944516
    assert total_coins == 9445165
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 2

    assert crowdsale.call().seed_coins_vault1() == 528000
    assert crowdsale.call().seed_coins_vault2() == 0

def test_distribution_5m(crowdsale, team_multisig):
    # 5M
    crowdsale.transact().distribute(5 * 1000000, 88)

    earlybird_coins = crowdsale.call().earlybird_coins()
    regular_coins = crowdsale.call().regular_coins()
    seed_coins = crowdsale.call().seed_coins()
    future_round_coins = crowdsale.call().future_round_coins()
    foundation_coins = crowdsale.call().foundation_coins()
    team_coins = crowdsale.call().team_coins()
    total_coins = crowdsale.call().total_coins()

    assert earlybird_coins == 6000000
    assert regular_coins == 0
    assert seed_coins == 2112000
    assert future_round_coins == 3365240
    assert foundation_coins == 1275248
    assert team_coins == 1416943
    assert total_coins == 14169432
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins + 1

    assert crowdsale.call().seed_coins_vault1() == 528000
    assert crowdsale.call().seed_coins_vault2() == 1584000

def test_distribution_8m(crowdsale, team_multisig):
    # 8M
    crowdsale.transact().distribute(8 * 1000000, 88)

    earlybird_coins = crowdsale.call().earlybird_coins()
    regular_coins = crowdsale.call().regular_coins()
    seed_coins = crowdsale.call().seed_coins()
    future_round_coins = crowdsale.call().future_round_coins()
    foundation_coins = crowdsale.call().foundation_coins()
    team_coins = crowdsale.call().team_coins()
    total_coins = crowdsale.call().total_coins()

    assert earlybird_coins == 7200000
    assert regular_coins == 2000000
    assert seed_coins == 2640000
    assert future_round_coins == 2690909
    assert foundation_coins == 1614545
    assert team_coins == 1793939
    assert total_coins == 17939393
    assert total_coins == earlybird_coins + regular_coins + seed_coins + future_round_coins + foundation_coins + team_coins

    assert crowdsale.call().seed_coins_vault1() == 528000
    assert crowdsale.call().seed_coins_vault2() == 2112000
