from abc import ABC, abstractmethod
import os
from math import isclose, inf
from typing import List



class ExchangeInterface(ABC):
    name = None
    ws_handlers: None
    
    def __init__(self):
        pass
        # self.set_api_keys(public_key, private_key)
        
    @abstractmethod
    def fetch_orderbook(self, pair:str, limit: int = None)-> dict:
        pass
    
    @abstractmethod
    async def async_fetch_orderbook(self, pair:str, limit: int = None) -> dict:
        pass
    
    @abstractmethod
    def subscribe(self, event_types: List[str], pairs: List[str]):
        pass
    
    def extract_data(self) -> List[dict]:
        return {k:v.extract_data() for k, v in self.ws_handlers.items()}
    
    def clear_ws_data(self) -> None:
        for v in self.ws_handlers.values():
            v.clear_data()
    
    def close_socket(self):
        if self.socket is not None:
            self.socket.closeSocket()
        
    def is_socket_closed(self) -> bool:
        pass