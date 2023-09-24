import pytest
import json
import os
from pathlib import Path

from src.exchanges.bitvavo import Bitvavo
from src.exchanges.btcturk import BtcTurk
from src.utils.config_loader import load_config_by_name


def load_mock_resource(exchange, content):
    current_dir = Path(__file__).parent
    resource_path = os.path.join(current_dir, "resources", exchange, content)
    with open(resource_path, "r") as f:
        return json.load(f)
     
@pytest.fixture
def mock_os_api_key_bitvavo(monkeypatch):
    """
    Fixture to mock Bitvavo's public and private keys in the OS environment.
    """
    private_key = "a" * 64
    monkeypatch.setenv(
        "BITVAVO_PUBLIC_KEY",
        "mock_public_key")
    monkeypatch.setenv("BITVAVO_PRIVATE_KEY", private_key)

@pytest.fixture
def mock_config_bitvavo():
    """
    Fixture to provide a mock config for Bitvavo.
    """
    return {
        "name": "bitvavo",
        "exchange_type": "mock_type",
        "commission": 0.01,
        "pair_sep": "-",
        "exchange_fiat": "USD",
        "base_endpoint": "http://mock_endpoint",
        "exchange_info_url": "/mock_exchange_info",
        "assets_info_url": "/mock_assets_info"
    }
    
@pytest.fixture
def mock_exchange_info_bitvavo():
    return load_mock_resource("bitvavo", "exchange_info.json")
    
@pytest.fixture
def mock_assets_bitvavo():
    return load_mock_resource("bitvavo", "assets.json")
    
@pytest.fixture
def unauthenticated_bitvavo(mocker, mock_config_bitvavo, mock_exchange_info_bitvavo, mock_assets_bitvavo):
    """
    Fixture to create and return an unauthenticated Bitvavo instance.
    """
    mocker.patch("src.exchanges.bitvavo.load_config_by_name", return_value=mock_config_bitvavo)
    mocker.patch("src.exchanges.bitvavo.BitvavoWrapper.markets", return_value=mock_exchange_info_bitvavo)
    mocker.patch("src.exchanges.bitvavo.BitvavoWrapper.assets", return_value=mock_assets_bitvavo)
    b = Bitvavo(authenticate=False)
    mocker.patch.object(b.wrapper, "APIKEY", "")
    return b
    
@pytest.fixture
def authenticated_bitvavo(mocker, 
                          mock_config_bitvavo,
                          mock_os_api_key_bitvavo,
                          mock_exchange_info_bitvavo,
                          mock_assets_bitvavo):
    mocker.patch("src.exchanges.bitvavo.load_config_by_name", return_value=mock_config_bitvavo)
    mocker.patch("src.exchanges.bitvavo.BitvavoWrapper.markets", return_value=mock_exchange_info_bitvavo)
    mocker.patch("src.exchanges.bitvavo.BitvavoWrapper.assets", return_value=mock_assets_bitvavo)
    b = Bitvavo(authenticate=True)
    mocker.patch.object(b.wrapper, "APIKEY", "")
    return b

@pytest.fixture
def mock_orderbook_bitvavo():
    return load_mock_resource("bitvavo", "orderbook_btc_eur.json")

@pytest.fixture
def mock_os_api_key_btcturk(monkeypatch):
    """
    Fixture to mock BTCTurk's public and private keys in the OS environment.
    """
    monkeypatch.setenv("BTCTURK_PUBLIC_KEY", "mock_public_key")
    monkeypatch.setenv("BTCTURK_PRIVATE_KEY", "mock_private_key")

@pytest.fixture
def mock_config_btcturk():
    """
    Fixture to provide a mock config for Btcturk.
    """
    return {
        "name": "btcturk",
        "exchange_type": "crypto",
        "commission": 0.01,
        "pair_sep": "_",
        "exchange_fiat": "TRY",
        "base_endpoint": "http://mock_endpoint",
        "exchange_info_url": "/mock_exchange_info",
        "balance_url": "/mock_balance",
        "order_url": "/mock_orderbook",
        "orderbook_url": "/mock_orderbook",
        "orderbook_limit": 20,
    }

@pytest.fixture
def mock_exchange_info_btcturk():
    return load_mock_resource("btcturk", "exchange_info.json")
    
@pytest.fixture
def unauthenticated_btcturk(mocker, mock_config_btcturk, mock_exchange_info_btcturk):
    """
    Fixture to create and return an unauthenticated BTCTurk instance.
    """
    mocker.patch("src.exchanges.btcturk.load_config_by_name", return_value=mock_config_btcturk)
    mocker.patch("src.exchanges.btcturk.fetch_json", return_value=mock_exchange_info_btcturk)

    b = BtcTurk(authenticate=False)
    return b

@pytest.fixture
def authenticated_btcturk(mocker, mock_config_btcturk, mock_exchange_info_btcturk, mock_os_api_key_btcturk):
    """
    Fixture to create and return an unauthenticated BTCTurk instance.
    """
    mocker.patch("src.exchanges.btcturk.load_config_by_name", return_value=mock_config_btcturk)
    mocker.patch("src.exchanges.btcturk.fetch_json", return_value=mock_exchange_info_btcturk)
    b = BtcTurk(authenticate=True)
    
    return b

    
@pytest.fixture
def mock_orderbook_btcturk():
    return load_mock_resource("btcturk", "orderbook_btc_try.json")

@pytest.fixture
def mock_config_data_collector(request):
    return {
        "collection_mode": request.param,
        "limit": 5,
        "pairs": {
            "bitvavo": ["BTC-EUR"],
            "btcturk": ["BTC-TRY"]
        }
    }