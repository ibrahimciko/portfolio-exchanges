import logging
from datetime import datetime
from abc import ABC, abstractmethod
import threading
import copy


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class WSHandler(ABC):
    
    keys: dict = None
    event_type: str = None
    limit: int = None
    active_buffer: list = None
    swap_buffer: list = None
    pairs: list = None
    
    def __init__(self):
        self.lock = threading.Lock()

    def validate_data_keys(self, response):
        for key in self.keys[self.event_type]:
            if key not in response:
                logger.error(f"Invalid data in response: {response} with missing key: {key} for event type: {self.event_type}")
                logger.error(f"Incorrrect response: {response}")
                return None
        return response
            
    def add_event_type_callback(self, response):
        # some exchanges don't have an event name in the response
        if "event" not in response:
            response["event"] = self.event_type
        return response
        
    def add_fetch_time(self, response):
        response["fetch_time"] = datetime.now()
        return response
    
    def append_data_callback(self, response):
        with self.lock:
            self.active_buffer.append(response)

        
    def append_exchange_name_callback(self, response, name):
        response["exchange"] = name
        return response
        
    def clear_data(self):
        with self.lock:
            self.active_buffer.clear()
            self.swap_buffer.clear()

    @abstractmethod
    def callback(self, response):
        pass
    
    @abstractmethod
    def error_callback(self, error):
        pass
    
    def limit_orderbook_callback(self, response):
        response["bids"] = response["bids"][:self.limit]
        response["asks"] = response["asks"][:self.limit]
        return response

    def extract_data(self):
        """ Extracts the data from the active buffer and returns a deep copy of it. Thread safe.

        Returns:
            list: A deep copy of the active buffer.
        """
        with self.lock:
            # Swap the buffers
            self.active_buffer, self.swap_buffer = self.swap_buffer, self.active_buffer
            # Clear active buffer for new data
            self.active_buffer.clear()
            # Return deep copy of swap buffer for safety
            return copy.deepcopy(self.swap_buffer)
    