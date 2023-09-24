from src.exchanges.bitvavo import Bitvavo
from src.exchanges.btcturk import BtcTurk
from src.exchanges.exchange_interface import ExchangeInterface

EXCHANGE_MAPPING = {
    "bitvavo": Bitvavo,
    "btcturk": BtcTurk
}

def create_exchange(exchange_name: str, authenticate: bool = False) -> ExchangeInterface:
    exchange_class = EXCHANGE_MAPPING.get(exchange_name.lower())
    
    if not exchange_class:
        raise NotImplementedError(f"Exchange {exchange_name} is not implemented.")
    
    return exchange_class(authenticate)