import pytest

from src.exchanges.exceptions import MissingApiKeyError


def test_bitvavo_init(authenticated_bitvavo, unauthenticated_bitvavo):
    """
    Test the initialization of Bitvavo instances.
    """
    # Checking the names of the Bitvavo instances
    assert all(b.name == "bitvavo" for b in [authenticated_bitvavo, unauthenticated_bitvavo])
    
    # Validating the authentication status and keys of the authenticated instance
    assert authenticated_bitvavo.public_key == "mock_public_key"
    assert authenticated_bitvavo.private_key == "a" * 64
    
    # Validating the lack of authentication and keys for the unauthenticated instance
    assert unauthenticated_bitvavo.public_key is None
    assert unauthenticated_bitvavo.private_key is None  
    
def test_bitvavo_raise_exception(unauthenticated_bitvavo):
    """
    Test if an exception is raised when trying to authenticate without API keys.
    """
    with pytest.raises(MissingApiKeyError):
        unauthenticated_bitvavo._authenticate()

def test_fetch_orderbook(mocker, unauthenticated_bitvavo, mock_orderbook_bitvavo):
    """
    Test fetching orderbook functionality of Bitvavo.
    """
    # Mocking the orderbook return value
    mocker.patch.object(unauthenticated_bitvavo.wrapper, "book", return_value=mock_orderbook_bitvavo)
    orderbook = unauthenticated_bitvavo.fetch_orderbook("BTC-EUR")

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
    assert orderbook["pair"] == "BTC-EUR"

    # Confirming the timestamp value (based on the current function implementation)
    assert orderbook["timestamp"] is None