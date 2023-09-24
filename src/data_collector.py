from datetime import datetime
import time
from typing import List
import sys
import logging
import traceback

import asyncio

from src.exchanges.exchange_interface import ExchangeInterface
from src.utils.config_loader import load_config_by_name
from src.writer.writer_interface import WriterInterface
from src.utils.http_helpers import async_retry_on_failure

logger = logging.getLogger(__name__)


class DataCollector:

    def __init__(self, exchanges: List[ExchangeInterface] = None, writer: WriterInterface = None):
        self.exchanges = exchanges
        self.writer = writer
        self.collection_mode = None
        self.limit = None
        self.pairs = None
        self._sleep_duration = None
        self.config = self._load_config()
        self._set_attributes_from_config(self.config)
        if self.collection_mode not in ["sync", "async", "websocket"]:
            raise ValueError(f"Collection mode {self.collection_mode} is not supported.")
        
        self.collection_fnc = self._async_fetch_orderbooks if self.collection_mode == "async" else self._sync_fetch_orderbooks
        if self.collection_mode == "websocket":
            self._initialize_websocket()
            
        self._counter = 0

                    
    def _load_config(self) -> dict:
        """Load configuration for data collector."""
        return load_config_by_name("data_collector")

    def _set_attributes_from_config(self, config: dict) -> None:
        """Set class attributes based on configuration."""
        self.collection_mode = config["collection_mode"]
        self.limit = config.get("limit")
        self._sleep_duration = config["sleep_duration"]
        self.pairs = config["pairs"]
        self.event_types = config["event_types"]
        exchange_names = list(self.pairs.keys())
        if set(exchange_names) != (set(self.event_types.keys())): 
            msg = "Exchange names in trading pairs and event types in config does not match"
            logger.error(msg)
            raise ValueError(msg)
        if not set(exchange_names).issubset(set([x.name for x in self.exchanges])):
            raise ValueError("Exchange names in config file and exchanges passed to DataCollector do not match.")

    @async_retry_on_failure(attempts=3, delay=5)
    async def _async_fetch_orderbooks(self) -> List[dict]:
        """Asynchronously fetch order books from exchanges."""
        tasks = [
            exchange.async_fetch_orderbook(pair, self.limit)
            for exchange in self.exchanges
            for pair in self.pairs[exchange.name]
        ]
        orderbooks = await asyncio.gather(*tasks)
        return orderbooks

    def _sync_fetch_orderbooks(self) -> List[dict]:
        """Synchronously fetch order books from exchanges."""
        return [
            exchange.fetch_orderbook(pair, self.limit)
            for exchange in self.exchanges
            for pair in self.pairs[exchange.name]
        ]

    def fetch_orderbooks(self) -> List[dict]:
        """Fetch order books using either async or sync methods based on the configuration."""
        if asyncio.iscoroutinefunction(self.collection_fnc):
            data = asyncio.run(self.collection_fnc())
        elif self.collection_mode == "sync":
            data = self._sync_fetch_orderbooks()
        else:
            raise NotImplementedError(f"Collection mode {self.collection_mode} is not implemented.")
        
        now = datetime.now()
        for book in data:
            book["fetch_time"] = now
        
        return {"orderbook": data}
    
    def graceful_shutdown(self, signum, frame):
        """Handle graceful shutdown of the data collector."""
        logger.info("Received shutdown signal. Saving buffer...")
        if self.collection_mode == "websocket":
            data = self._combine_data_across_exchanges()
            for event_type, event_data in data.items():
                self.writer.append(event_data, event_type)
            for x in self.exchanges:
                x.close_socket()
        
        for event_type in self.writer.buffer.keys():
            self.writer.save_and_refresh(event_type)
        sys.exit(0)

    def fetch_forever(self):
        """Continuously fetch order books and save them when the buffer is full."""
        logger.info("Fetching order books...")
        if self.writer is None:
            msg = "Writer is not initialized."
            logger.error(msg)
            raise ValueError(msg)
        
        while True:
            try:
                self._counter += 1
                #TODO Currently only supports orderbook fetching data in async and sync mode
                # Add new capabilities for fetching other event types
                if self.collection_mode in ["sync", "async"]:
                    data = self.fetch_orderbooks()
                else:
                    # check if socket is closed and reconnect if necessary
                    self.reconnect()
                    if self._counter % 100 == 0:
                        data = self._combine_data_across_exchanges()
                        self._counter = 0
                    else:
                        data = None
                if data is not None:
                    for event_type in data.keys():
                        self.writer.append(data[event_type], event_type)
                        if self.writer.is_buffer_full(event_type):
                            self.writer.save_and_refresh(event_type)
                time.sleep(self._sleep_duration)
            except Exception as e:
                logger.error("An error occurred: %s\n%s", e, traceback.format_exc())
                time.sleep(30)
                if self.collection_mode == "websocket":
                    self.reconnect()
                continue

    def _initialize_websocket(self):
        """Initialize websocket for data collection."""
        for exchange in self.exchanges:
            exchange.subscribe(self.event_types[exchange.name], self.pairs[exchange.name])
            
    
    def reconnect(self):
        """Reconnect to websocket."""
        for x in self.exchanges:
            if x.is_socket_closed():
                x.subscribe(self.event_types[x.name], self.pairs[x.name])
        
    
    def _combine_data_across_exchanges(self) -> dict:
        """ Data resides in the buffer of each exchange. This method combines the data from all exchanges.
        By calling the extract_data method of each exchange, the data is removed from the buffer of each exchange.

        Returns:
            dict: A dictionary of event type and data where data is a list of dictionaries and event types are keys.
        """
        data = {}
        for exchange in self.exchanges:
            exchange_data = exchange.extract_data()
            for event_type, event_data in exchange_data.items():
                if event_type not in data:
                    data[event_type] = []
                data[event_type].extend(event_data)
        return data
                