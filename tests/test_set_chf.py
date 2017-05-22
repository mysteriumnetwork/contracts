"""Basic token properties"""

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
def mysterium_pricing(chain, preico_token_price, team_multisig) -> Contract:
    """Flat pricing contact."""
    args = [
        120 * 10000,
    ]
    tx = {
        "from": team_multisig,
    }
    pricing_strategy, hash = chain.provider.deploy_contract('MysteriumPricing', deploy_args=args,  deploy_transaction=tx)
    return pricing_strategy


def test_convert(mysterium_pricing):
    assert mysterium_pricing.call().convertToWei(120*10000) == 1 * 10**18


