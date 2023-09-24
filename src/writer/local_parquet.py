from typing import List
import time
import os
import logging

from src.writer.writer_interface import WriterInterface

logger = logging.getLogger(__name__)

class LocalParquetWriter(WriterInterface):
    """
    A class to represent a local parquet writer that writes data to a local filesystem.

    Attributes:
        buffer_size (int): The size of the data buffer.
        data_directory (str): The directory where the parquet files will be saved.
        partition_cols (List[str]): The list of columns for partitioning.
    """

    def __init__(self, buffer_size: int, data_directory: str, partition_cols: List[str] = None, buffer: List = None):
        """
        Constructs the LocalParquetWriter object.

        Args:
            buffer_size (int): The size of the data buffer.
            data_directory (str): The directory where the parquet files will be saved.
            partition_cols (List[str], optional): The list of columns for partitioning. Defaults to None.
        """
        self.buffer_size = buffer_size
        if buffer is None:
            buffer = []
        self.buffer = buffer
        self.data_directory = data_directory
        self.partition_cols = partition_cols if partition_cols else []

    def append(self, data: List[dict], event_type: str):
        """
        Appends the given data to the buffer.

        Args:
            data (List[dict]): Data to append.
            event_type (str): The event type. Such as "orderbook", "ticker", "trades".
        """
        if event_type not in self.buffer:
            self.buffer[event_type] = []
        self.buffer[event_type].extend(data)

    def is_buffer_full(self, event_type) -> bool:
        """
        Checks if the buffer is full.
        Args:
            event_type (str): The event type. Such as "orderbook", "ticker", "trades".

        Returns:
            bool: True if buffer is full, False otherwise.
        """
        return len(self.buffer[event_type]) >= self.buffer_size

    def save_and_refresh(self, event_type):
        """
        Saves the data in the buffer to S3 and then refreshes the buffer.
        Args:
            event_type (str): The event type. Such as "orderbook", "ticker", "trades".
        """
        if not self.buffer[event_type]:
            logger.warning("Buffer is empty")
            return

        data = self._list_of_dict_to_df(self.buffer)
        data["write_time"] = time.strftime("%Y%m%d-%H")

        os.makedirs(self.data_directory, exist_ok=True)
        partition_cols = self.partition_cols + ["write_time"]
        data.to_parquet(self.data_directory, engine='pyarrow', partition_cols=partition_cols)
        logger.info(f"Saved {len(self.buffer)} rows to {self.data_directory}")

        # don't init into a new buffer = [] since websocket streaming is through list referencing
        self.buffer.clear()

    
    
