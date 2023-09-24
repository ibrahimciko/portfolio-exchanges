
import os
from typing import List, Tuple, Dict
import logging
import time
import threading
import json

import httpx
from python_bitvavo_api.bitvavo import Bitvavo as BitvavoWrapper
from python_bitvavo_api.bitvavo import errorToConsole
from python_bitvavo_api.bitvavo import debugToConsole
from python_bitvavo_api.bitvavo import createSignature

from src.exchanges.exceptions import (
    MissingApiKeyError, PairNotFoundError, AssetNotFoundError
)
from src.exchanges.exchange_interface import ExchangeInterface
from src.utils.config_loader import load_config_by_name
from src.utils.http_helpers import retry_on_failure, requires_authentication
from src.ws_handlers.bitvavo import BitvavoWSHandler


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomBitvavoWrapper(BitvavoWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    
    def newWebsocket(self):
        return CustomBitvavoWrapper.customWebSocket(self.APIKEY, self.APISECRET, self.ACCESSWINDOW, self.wsUrl, self)
        
        
    class customWebSocket(BitvavoWrapper.websocket):
        def __init__(self, *args, **kwargs):
            logger.info("initializing custom websocket")
            super().__init__(*args, **kwargs)
            
        def on_error(self, error):
            if "error" in self.callbacks:
                self.callbacks["error"](error)
            else:
                errorToConsole(error)
                
        def on_close(self):
            if hasattr(self.ws, "receiveThread"):
                if hasattr(self.ws.receiveThread, "exit"):
                    self.ws.receiveThread.exit()
            else:
                logger.warning("'receiveThread' object has no attribute 'exit'")
                # Using closeSocket to ensure proper closure
                logger.warning("Closing the socket with manual closeSocket method")
                self.close_socket_safely()
                
                
        def on_open(self):
            now = int(time.time()*1000)
            self.open = True
            self.reconnectTimer = 0.5
            if(self.APIKEY != ''):
                self.doSend(self.ws, json.dumps({ 'window':str(self.ACCESSWINDOW), 'action': 'authenticate', 'key': self.APIKEY, 'signature': createSignature(now, 'GET', '/websocket', {}, self.APISECRET), 'timestamp': now }))
            if self.reconnect:
                debugToConsole("we started reconnecting", self.checkReconnect)
                thread = threading.Thread(target = self.checkReconnect)
                thread.start()
            
        def close_socket_safely(self):
            if self.ws and hasattr(self.ws, 'close'):
                try:
                    self.ws.close()
                    if hasattr(self.ws, 'keepAlive'):
                        self.ws.keepAlive = False
                    
                    # Check if 'receiveThread' exists and join it to ensure its termination
                    if hasattr(self.ws, 'receiveThread') and self.ws.receiveThread.is_alive():
                        self.ws.receiveThread.join()
                    logger.info("Socket closed safely.")
                except Exception as e:
                    logger.error(f"Error while closing socket: {e}")
        
        def is_socket_closed(self):
            if not hasattr(self, 'ws'):
                return True
            if hasattr(self.ws, 'connected'):
                return not self.ws.connected
            if hasattr(self.ws, 'keepAlive'):
                return not self.ws.keepAlive
            if hasattr(self.ws, 'closed'):
                return self.ws.closed
            if hasattr(self.ws, 'keep_running'):
                return not self.ws.keep_running
            return False
        
        
class Bitvavo(ExchangeInterface):
    def __init__(self, authenticate: bool = False):
        super(Bitvavo, self).__init__()
        self.config = self._load_config()
        self._set_attributes_from_config(self.config)
        
        self.public_key, self.private_key = self._authenticate() if authenticate else (None, None)
        options = {"APIKEY": self.public_key, "APISECRET": self.private_key} if self.public_key and self.private_key else {}
        self.wrapper = CustomBitvavoWrapper(options=options)
        
        # placeholders for attributes that will be set later
        self._exchange_info = None
        self._pairs = None
        self._assets = None
        self._fetch_exchange_info()
        self.socket = None
        # websocket handlers will be populated if subscriptions are made
        self.ws_handlers: Dict[BitvavoWSHandler] = {}
        
    
    def _authenticate(self)-> Tuple[str, str]:
        public_key = os.getenv(f"{self.name.upper()}_PUBLIC_KEY")
        private_key = os.getenv(f"{self.name.upper()}_PRIVATE_KEY")
        if not public_key or not private_key:
            raise MissingApiKeyError(name=self.name)
        return public_key, private_key
    
    def _load_config(self) -> dict:
        config = load_config_by_name("bitvavo")
        return self._handle_endpoints(config)
    
    def _set_attributes_from_config(self, config: dict):
        self.name = config["name"]
        self.exchange_type  = config["exchange_type"]
        self.commision = config["commission"]
        self.pair_sep = config["pair_sep"]
        self.exchange_fiat =  config["exchange_fiat"]
        self.base_endpoint = config["base_endpoint"]
        self.exchange_info_url = config["exchange_info_url"]
        self.assets_info_url = config["assets_info_url"]
    
    def _handle_endpoints(self, config):
        for key in ["exchange_info_url", "assets_info_url"]:
            config[key] = config["base_endpoint"] + config[key]
        return config
    
    @retry_on_failure()
    def _fetch_exchange_info(self):
        """Fetches the exchange info from the exchange and sets the attributes
        """
        self._exchange_info  = self.wrapper.markets({})
        self._pairs = {pair["market"]: pair for pair in self._exchange_info}
        # also add pairidentifier without dash
        self._pairs_normalized = {k.replace(self.pair_sep, ""): v for k,v in self._pairs.items()}
        
        self._assets  = {asset["symbol"]: asset for asset in self.wrapper.assets({})}
        
    def _get_pair(self, pair:str) -> dict:
        # convert to upercase
        # convert underscore to dash if exists
        pair = pair.replace("_", self.pair_sep).upper()
        value = self._pairs.get(pair) or self._pairs_normalized.get(pair)
        if value is None:
            msg = f"pair: {pair} not in pairs"
            raise PairNotFoundError(message=msg)
        return value
    
    def _get_pair_name(self, pair:str) -> str:
        return self._get_pair(pair)["market"]
    
    def _get_asset(self, asset: str) -> dict:
        asset = asset.upper()
        if asset not in self._assets:
            msg = f"asset: {asset} not in assets"
            logger.error(msg)
            raise AssetNotFoundError(message=msg)
        return self._assets[asset]
    
    def _get_asset_name(self, asset:str) -> str:
        return self._get_asset(asset)["symbol"]
    
    def fetch_orderbook(self, pair:str, limit: int = None) -> dict:
        # TODO add headers 
        # Decide whether to include authentication  here
        pair_name = self._get_pair_name(pair)
        options = {"depth": limit} if limit else {}
        data = self.wrapper.book(pair_name, options)
        return {
            "bids": list(map(lambda x: [float(x[0]), float(x[1])], data["bids"])),
            "asks": list(map(lambda x: [float(x[0]), float(x[1])], data["asks"])),
            "timestamp": None,
            "pair": pair,
            "exchange": self.name
        }
    
        
    async def async_fetch_orderbook(self, pair:str, limit: int = None) -> dict:
        pair_name = self._get_pair_name(pair)
        url = self.base_endpoint + f"/{pair_name}/book"
        if limit:
            url += f"?depth={limit}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()
            
        return {
            "bids": list(map(lambda x: [float(x[0]), float(x[1])], data["bids"])),
            "asks": list(map(lambda x: [float(x[0]), float(x[1])], data["asks"])),
            "timestamp": None,
            "pair": pair,
            "exchange": self.name
        }

    @retry_on_failure()
    @requires_authentication
    def fetch_balance(self)->dict:
        raw_balance = self.wrapper.balance({}) 
        balance = {}
        for item in raw_balance:
            available = float(item["available"])
            in_order = float(item["inOrder"])
            balance[self._get_asset_name(item["symbol"])] = {"available": available, "total": available + in_order}        
        return balance
    
    def subscribe(self, event_types:List[str], pairs:List[str]):
        """Subscribe to events for pairs

        Args:
            event_types (List[str]): such as ["orderbook", "ticker", "trades"]
            pairs (List[str]): such as ["BTC-EUR", "ETH-EUR"]

        Raises:
            ValueError: if event type is not supported
        """
        if isinstance(event_types, str):
            event_types = [event_types]
        if not set(event_types).issubset(["orderbook", "ticker", "trades"]): 
            logger.error(f"invalid event type {event_types}")
            raise ValueError

        fnc_mapping = {
            "orderbook": self._subscribe_orderbook,
            "ticker": self._subscribe_ticker,
            "trades": self._subscribe_trades
        }
        for event in event_types:
            logger.info(f"subscribing to {event} for pairs:{pairs} in exchange {self.name}")
            fnc_mapping[event](pairs)
            
        # set global error callback
        # since errorCallback is not specific to an event type, we can only set one
        self.socket.setErrorCallback(self.ws_handlers[event_types[0]].error_callback)
        
    def _subscribe_orderbook(self, pairs:List[str]) -> dict:
        pair_names, callback = self._subscribe_ws("orderbook", pairs)
        for p in pair_names:
            self.socket.subscriptionBook(p, callback)
            time.sleep(0.3)
    
    def _subscribe_ticker(self, pairs:List[str]) -> dict:
        pair_names, callback = self._subscribe_ws("ticker", pairs)
        for p in pair_names:
            self.socket.subscriptionTicker(p, callback)
            time.sleep(0.3)
    
    def _subscribe_trades(self, pairs:List[str]) -> dict:
        pair_names, callback = self._subscribe_ws("trades", pairs)
        for p in pair_names:
            self.socket.subscriptionTrades(p, callback)
            time.sleep(0.3)

    def _subscribe_ws(self, event_type:str, pairs:List[str]) -> dict:
        if self.socket is None:
            self.socket = self.wrapper.newWebsocket()
        ws_handler = BitvavoWSHandler(event_type, self.socket)
        # register the handler
        self.ws_handlers[event_type] = ws_handler
        
        if isinstance(pairs, str):
            pairs = [pairs]
        pair_names = [self._get_pair_name(pair) for pair in pairs]
        return pair_names, ws_handler.callback

    
    