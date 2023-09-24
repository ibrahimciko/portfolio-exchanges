import pytest

from src.exchanges.exceptions import MissingApiKeyError


def test_btcturk_init(authenticated_btcturk, unauthenticated_btcturk):
    """
    Test the initialization of Bitvavo instances.
    """
    # Checking the names of the Bitvavo instances
    assert all(b.name == "btcturk" for b in [authenticated_btcturk, unauthenticated_btcturk])
    
    # Validating the authentication status and keys of the authenticated instance
    assert authenticated_btcturk.public_key == "mock_public_key"
    assert authenticated_btcturk.private_key == "mock_private_key"
    
    # Validating the lack of authentication and keys for the unauthenticated instance
    assert unauthenticated_btcturk.public_key is None
    assert unauthenticated_btcturk.private_key is None 
    
def test_btcturk_raise_exception(unauthenticated_btcturk):
    """
    Test if an exception is raised when trying to authenticate without API keys.
    """
    with pytest.raises(MissingApiKeyError):
        unauthenticated_btcturk._authenticate()

def test_fetch_orderbook(mocker, unauthenticated_btcturk, mock_orderbook_btcturk):
    """
    Test fetching orderbook functionality of Bitvavo.
    """
    # Mocking the orderbook return value
    mocker.patch("src.exchanges.btcturk.fetch_json", return_value=mock_orderbook_btcturk)
    orderbook = unauthenticated_btcturk.fetch_orderbook("BTC-TRY")

    # Validate the structure of the fetched orderbook
    for key in ["bids", "asks", "timestamp", "pair"]:
        assert key in orderbook

    # Confirming correct sorting of bids and asks in the orderbook
    assert orderbook["asks"] == sorted(orderbook["asks"])
    assert orderbook["bids"] == sorted(orderbook["bids"], reverse=True)

    # Validating data types for bids and asks in the orderbook
    for order in orderbook["asks"]:
        assert isinstance(order[0], float)
        assert isinstance(order[1], float)

    for order in orderbook["bids"]:
        assert isinstance(order[0], float)
        assert isinstance(order[1], float)

    # Checking if correct pair name is returned
    assert orderbook["pair"] == "BTC-TRY"

    # Confirming the timestamp value (based on the current function implementation)
    assert orderbook["timestamp"] is not None