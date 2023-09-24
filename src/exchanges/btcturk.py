from typing import Tuple
import base64
import time
import hmac
import hashlib
import logging
import os
import httpx

from src.exchanges.exchange_interface import ExchangeInterface
from src.utils.config_loader import load_config_by_name
from src.utils.http_helpers import retry_on_failure, requires_authentication
from src.exchanges.exceptions import (
    MissingApiKeyError, PairNotFoundError, AssetNotFoundError
)
from src.utils.http_helpers import fetch_json

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class BtcTurk(ExchangeInterface):    
    def __init__(self, authenticate: bool = False):
        super(BtcTurk, self).__init__()
        # loading the config from the central config file
        self.config = self._load_config()
        self._set_attributes_from_config(self.config)
        # authentication is required for private endpoints
        self.public_key, self.private_key = self._authenticate() if authenticate else (None, None)
        
        # placeholders for attributes that will be set later
        self._exchange_info = None
        self._pairs = None
        self._assets = None
        self._fetch_exchange_info()
        
    def _authenticate(self)-> Tuple[str,str]:
        public_key = os.getenv(f"{self.name.upper()}_PUBLIC_KEY")
        private_key = os.getenv(f"{self.name.upper()}_PRIVATE_KEY")
        if not public_key or not private_key:
            raise MissingApiKeyError(name=self.name)
        return public_key, private_key
        
    def _load_config(self) -> dict:
        """Loads the config for the exchange from the central config
            file and modifies the endpoints to include the base endpoint

        Returns:
            dict: config for the exchange
        """
        config = load_config_by_name("btcturk")
        # modify the endpoints to include the base endpoint
        return self._handle_endpoints(config)
        
    def _set_attributes_from_config(self, config: dict):
        self.name = config["name"]
        self.exchange_type  = config["exchange_type"]
        self.commision = config["commission"]
        self.pair_sep = config["pair_sep"]
        self.exchange_fiat =  config["exchange_fiat"]
        self.base_endpoint = config["base_endpoint"]
        self.exchange_info_url = config["exchange_info_url"]
        self.balance = config["balance_url"]
        self.order_url = config["order_url"]
        self.orderbook_url = config["orderbook_url"]
        self.orderbook_limit = config["orderbook_limit"]
        
    def _handle_endpoints(self, config):
        for key in ["balance_url", "order_url", "orderbook_url", "exchange_info_url"]:
            config[key] = config["base_endpoint"] + config[key]
        return config

    @retry_on_failure()
    def _fetch_exchange_info(self) -> None:
        """Fetches the exchange info from the exchange and sets the attributes
        """
        # set exchange info
        self._exchange_info = fetch_json(self.exchange_info_url)
        # set pairs-
        symbols = self._exchange_info["data"]["symbols"]
        self._pairs = {}
        self._pairs_normalized = {}
        for symbol in symbols:
            self._pairs[symbol["name"]] = symbol
            self._pairs_normalized[symbol["nameNormalized"]] = symbol
        # set assets
        assets = self._exchange_info["data"]["currencies"]
        self.assets = {asset["name"] for asset in assets}
        
    def _get_pair(self, pair: str) -> dict:
        pair = pair.replace("-", "_").upper()
        value = self._pairs.get(pair) or self._pairs_normalized.get(pair)
        if value is None:
            msg = f"pair: {pair} not in pairs"
            raise PairNotFoundError(message=msg)
        return value
    
    def _get_pair_name(self, pair:str) -> str:
        return self._get_pair(pair)["name"]
        
    def _get_asset(self, asset: str) -> dict:
        asset = asset.upper()
        if asset not in self.assets:
            msg = f"asset: {asset} not in assets: {self.assets}"
            logger.error(msg)
            raise AssetNotFoundError(message=msg)
        return self.assets[asset]
    
    def _get_asset_name(self, asset: str) -> str:
        return self._get_asset(asset)["name"]
    
    def fetch_orderbook(self, pair:str, limit: int = None) -> dict:
        """Interface method to fetch the orderbook for a given pair

        Args:
            pair (str): _description_
            limit (int, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """
        pair_name = self._get_pair_name(pair)
        limit_param = "" if limit is None else f"&limit={limit}"
        url = f"{self.orderbook_url}?pairSymbol={pair_name}&{limit_param}"
        data = fetch_json(url)["data"]
        return {
            "bids": list(map(lambda x: [float(x[0]), float(x[1])], data["bids"])),
            "asks": list(map(lambda x: [float(x[0]), float(x[1])], data["asks"])),
            "timestamp": data["timestamp"],
            "pair": pair,
            "exchange": self.name
        }
    
    async def async_fetch_orderbook(self, pair:str, limit: int = None) -> dict:
        pair_name = self._get_pair_name(pair)
        limit_param = "" if limit is None else f"&limit={limit}"
        url = f"{self.orderbook_url}?pairSymbol={pair_name}&{limit_param}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()["data"]
        
        return {
            "bids": list(map(lambda x: [float(x[0]), float(x[1])], data["bids"])),
            "asks": list(map(lambda x: [float(x[0]), float(x[1])], data["asks"])),
            "timestamp": data["timestamp"],
            "pair": pair,
            "exchange": self.name
        }
    
    @retry_on_failure()
    @requires_authentication
    def fetch_balance(self)-> dict:
        """Interface method to get the balance per asset.

        Returns:
            dict: balance per asset
        """
        data = fetch_json(self.balance_url, headers=self._get_private_headers())
        data = data["data"]
        balance = {
            self._get_asset_name(asset["asset"]): {"total": float(asset["balance"]), "available":float(asset["free"])} for asset in data
        }
        return balance
    
    def _get_private_headers(self)-> dict:
        """Private headers required for private endpoints
        """
        private_key_decoded = base64.b64decode(self.private_key)
        stamp = str(int(time.time())*1000)
        data = "{}{}".format(self.public_key, stamp).encode("utf-8")
        signature = hmac.new(private_key_decoded, data, hashlib.sha256).digest()
        signature = base64.b64encode(signature)
        headers = {"X-PCK": self.public_key, "X-Stamp": stamp, "X-Signature": signature, "Content-Type" : "application/json"}
        return headers
    
    
    # def check_required_amounts(self, pair:str, amount: float = None, amountQuote: float = None):
    #     # assert logical or
    #     assert bool(amount) ^ bool(amountQuote), "provide either amount or amountQuote"
    #     pair_info = self.get_pair_by_name(pair)["filters"][0]

    #     if amount is not None:
    #         required_amount = pair_info["minAmount"]
    #         if required_amount:
    #             assert amount >= float(required_amount) , f"amount: {amount} is smaller than required: {required_amount}"  
            
    #     if amountQuote is not None:
    #         required_amount = pair_info["minExchangeValue"]
    #         if required_amount:
    #             assert amountQuote >= float(required_amount) , f"amountQuote: {amountQuote} is smaller than required: {required_amount}"  
    
    # def is_amount_tradable_above_minimum(self, pair:str, amount: float = None, amountQuote: float = None)-> bool:
    #     assert bool(amount) ^ bool(amountQuote), "provide either amount or amountQuote"
    #     pair_info = self.get_pair_by_name(pair)["filters"][0]

    #     if amount is not None:
    #         required_amount = pair_info["minAmount"]
    #         if required_amount:
    #             if amount < float(required_amount):
    #                 return False

    #     if amountQuote is not None:
    #         required_amount = pair_info["minExchangeValue"]
    #         if required_amount:
    #             if amountQuote < float(required_amount):
    #                 return False
        
    #     return True

    # @requires_authentication
    # def market_order(self, pair:str, ordertype:str, amount: float = None, amountQuote: float = None) -> dict:
    #     """[summary]

    #     Args:
    #         pair (str): Please use a normalised string for the pair. E.g BTC_USDT
    #         ordertype (str): "buy" or "sell"
    #         amount (float, optional):  Specifies the amount of the base asset that will be sold.
    #             amount can be only used if the base asset is sold. Example: If one wants to sell 0.1 BTC to USDT,
    #             amount is 0.1 and ordertype is 'sell'. 
    #             If ordertype is buy one needs to use amountQuote. Defaults to None.
    #         amountQuote (float, optional): Specifies the amount of the quote asset that will be traded to buy the base asset.
    #             amountQuote can be only used if the quote asset is sold. Example, If one would like to buy 1000USDT amount
    #             of BTC, one needs to specify amountQuote as 1000 and ordertype as buy.

    #     Returns:
    #         dict: [description]
    #     """
        
        
    #     assert ordertype == "buy" or ordertype == "sell"
        
    #     assert bool(amount) ^ bool(amountQuote), "please specify either amount or amountQuote"
        
    #     # correct amount and amountQuote based on pair info
    #     pair_info = self.get_pair_by_name(pair)
    #     if amount:
    #         amount = float(amount)
    #         amount = round_decimals_down(amount, decimals = int(pair_info["numeratorScale"]))
            
    #     if amountQuote:
    #         if pair_info["hasFraction"] is False:
    #             amountQuote = trunc(amountQuote)
    #         else:  
    #             amountQuote = round_decimals_down(float(amountQuote),
    #                                               decimals=int(pair_info["denominatorScale"]))
                
    #     if ordertype == "buy":
    #         if amount is not None:
    #             raise MarketOrderNotSupportedError
    #         quantity = amountQuote
        
    #     else:
    #         # ordertype is sell
    #         if amountQuote is not None:
    #             raise MarketOrderNotSupportedError
    #         quantity = amount
        
    #     order_result = {"success": False, "id": None, "amount": None, "amountQuote": None, "error_message": None}
        
    #     headers = self._get_private_headers()
    #     newOrderClientId = "test"
        
    #     params={"quantity": quantity,
    #             "orderMethod": "market",
    #             "orderType": ordertype,
    #             "newOrderClientId": newOrderClientId,
    #             "pairSymbol": pair}

    #     response = requests.post(url=self.order_url, headers=headers, json=params)
    #     if response.ok:
    #         response = response.json()
    #         data = response["data"]
    #         order_result["success"] = True
    #         order_result["id"] = data["id"]
    #         order_result["ordertype"] = data["type"]
    #         if amount:
    #             key = "amount"
    #         else:
    #             key = "amountQuote"
    #         order_result[key] = float(data["quantity"])
    #         order_result["time"] = data["datetime"] 
    #     else:
    #         order_result["error_message"] = f"Text:{response.text}, code: {response.status_code}, reason: {response.reason}"
    #     return order_result
        
    
    
    # def correct_precision(self, asset:str, amount:float) -> float:
    #     # get asset info
    #     asset_info = self.get_asset_by_name(asset)
    #     decimals = asset_info.get("precision")
    #     if decimals is not None:
    #         amount = round_decimals_down(amount, decimals)
    #     return amount        
if __name__ == "__main__":
    pass
    