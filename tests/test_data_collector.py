from src.exchanges.btcturk import BtcTurk
from src.exchanges.bitvavo import Bitvavo
import pytest
from src.data_collector import DataCollector


@pytest.mark.parametrize("mock_config_data_collector", ["async"], indirect=True)
def test_data_collector_init(mocker, mock_config_data_collector, unauthenticated_bitvavo, unauthenticated_btcturk):
    mocker.patch("src.data_collector.load_config_by_name", return_value=mock_config_data_collector)
    dc = DataCollector(exchanges=[unauthenticated_bitvavo, unauthenticated_btcturk])

    assert dc.collection_mode == "async"
    assert dc.limit == 5
    assert "bitvavo" in dc.pairs
    assert "btcturk" in dc.pairs
    assert "BTC-EUR" in dc.pairs["bitvavo"]
    assert "BTC-TRY" in dc.pairs["btcturk"]
    
@pytest.mark.parametrize("mock_config_data_collector", ["async", "sync"], indirect=True)
def test_data_collector_fetch_orderbooks(mocker, mock_config_data_collector):
    # use actual development config for BtcTurk and Bitvavo
    exchanges = [BtcTurk(False), Bitvavo(False)]
    mocker.patch("src.data_collector.load_config_by_name", return_value=mock_config_data_collector)
    dc = DataCollector(exchanges)
    orderbooks = dc.fetch_orderbooks()
    
    # Check if you have order books
    assert orderbooks
    for ob in orderbooks:
        assert "fetch_time" in ob
        assert "bids" in ob and "asks" in ob
        assert "exchange" in ob