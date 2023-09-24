import logging
import time

from python_bitvavo_api.bitvavo import Bitvavo


from src.ws_handlers.base_handler import WSHandler


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BitvavoWSHandler(WSHandler):
    keys = {
        "orderbook": ["bids", "asks", "market"],
        "ticker": ["market"],
        "trades": ["id", "amount", "price", "timestamp", "market", "side"]
    }
    
    def __init__(self, event_type, socket: Bitvavo.websocket, limit: int = 20, pairs: list = None):
        super().__init__()
        self.socket = socket
        if event_type not in ["orderbook", "ticker", "trades"]:
            logger.error("Invalid event type in WS.")
            raise ValueError("Invalid event type.")
        self.event_type = event_type
        self.active_buffer = []
        self.swap_buffer = []
        self.limit = limit
        self.pairs = pairs
    
    def callback(self, response):
        response = self.validate_data_keys(response)
        if response is None:
            return None
        response = self.add_event_type_callback(response)
        response = self.add_fetch_time(response)
        
        if self.event_type ==  "orderbook":
            response = self.limit_orderbook_callback(response)
        
        if self.event_type == "ticker":
            response = self.add_null_columns(response)   
        
        response = self.append_exchange_name_callback(response, "bitvavo")
        self.append_data_callback(response)
        
    def add_null_columns(self, response):
        if self.event_type == "ticker":
            for key in ["bestBid", "bestBidSize", "bestAsk", "bestAskSize"]:
                if key not in response:
                    response[key] = None
        return response
    
    def error_callback(self, error):
        #TODO depending on the error type, implement specific error handling
        # if error is caused by A do this
        # if error is caused by B do that 
        # ....
        # now just sleep and try to reconnect to websocket
        logger.error(f"Something happened in websocket {error}")
        logger.info("Sleeping for 60 seconds and then try to reconnect again...")
        time.sleep(60)
        if self.socket.is_socket_closed():
            # reconnect to websocket
            logger.info("socket is already closed. Will open a new one.")
        else:
            self.socket.checkReconnect()
    