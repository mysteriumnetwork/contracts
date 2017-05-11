"""Basic token properties"""


def test_token_interface(token, team_multisig):
    """Deployed token properties are correct."""

    assert token.call().totalSupply() == 0
    assert token.call().symbol() == "MYST"
    assert token.call().name() == "Mysterium"
    assert token.call().decimals() == 8
    assert token.call().owner() == team_multisig
    assert token.call().upgradeMaster() == team_multisig

