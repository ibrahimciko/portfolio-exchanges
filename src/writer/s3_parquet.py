from typing import List
import time
import os
import tempfile
import logging

import boto3
from src.writer.writer_interface import WriterInterface

logger = logging.getLogger(__name__)

class S3ParquetWriter(WriterInterface):
    """
    A class to represent an S3 Parquet writer.

    Attributes:
        s3_bucket (str): The S3 bucket name.
        s3_prefix (str): The S3 prefix path.
        buffer_size (int): The size of the data buffer.
        partition_cols (List[str]): The list of columns for partitioning.
    """

    def __init__(self, s3_bucket: str, s3_prefix: str, buffer_size: int = 10000, partition_cols: List[str] = None, buffer:dict = None):
        """
        Constructs the S3ParquetWriter object.

        Args:
            s3_bucket (str): The S3 bucket name.
            s3_prefix (str): The S3 prefix path.
            buffer_size (int): The size of the data buffer. Defaults to 10000.
            partition_cols (List[str], optional): The list of columns for partitioning. Defaults to None.
            buffer (dict, optional): The buffer to use. Defaults to None.
        """
        self.buffer_size = buffer_size
        if buffer is None:
            buffer = {}
        self.buffer = buffer
        self.partition_cols = partition_cols if partition_cols else []
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix

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
        
        data = self._list_of_dict_to_df(self.buffer[event_type])
        data["write_time"] = time.strftime("%Y%m%d-%H")
        partition_cols = self.partition_cols + ["write_time"]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "data")
            data.to_parquet(path, engine='pyarrow', partition_cols=partition_cols)
            s3_dest_path = f"{self.s3_prefix}/{event_type}"
            self.upload_to_s3(path, self.s3_bucket, s3_dest_path)
            logger.info(f"Uploaded data to s3://{self.s3_bucket}/{s3_dest_path}")

        # don't init into a new buffer = [] since websocket streaming is through list referencing
        self.buffer[event_type].clear()
    

    @staticmethod
    def upload_to_s3(local_dir: str, s3_bucket: str, s3_prefix: str, boto_client=None):
        """
        Uploads files from the local directory to the specified S3 location.

        Args:
            local_dir (str): Path to the local directory or file.
            s3_bucket (str): The S3 bucket name.
            s3_prefix (str): The S3 prefix path.
            boto_client (boto3.client, optional): The boto3 S3 client. If None, creates a new client.
        """
        if boto_client is None:
            boto_client = boto3.client(
                "s3",
                aws_access_key_id=os.environ.get('aws_access_key_id'),
                aws_secret_access_key=os.environ.get('aws_secret_access_key')
            )

        if os.path.isdir(local_dir):
            for dirpath, _, filenames in os.walk(local_dir):
                for filename in filenames:
                    local_file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(local_file_path, local_dir)
                    s3_key = os.path.join(s3_prefix, relative_path)
                    boto_client.upload_file(local_file_path, s3_bucket, s3_key)
        else:
            s3_key = os.path.join(s3_prefix, os.path.basename(local_dir))
            boto_client.upload_file(local_dir, s3_bucket, s3_key)
