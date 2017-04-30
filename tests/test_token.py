"""Basic token properties"""


def test_token_interface(token):
    """Check token properties"""

    assert token.call().totalSupply() == 0
    assert token.call().symbol() == "MYST"
    assert token.call().name() == "Mysterium"
    assert token.call().decimals() == 8

