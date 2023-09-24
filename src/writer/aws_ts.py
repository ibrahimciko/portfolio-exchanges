from typing import List

from src.writer.writer_interface import WriterInterface

class DBAWSWriter(WriterInterface):
    def __init__(self, buffer_size: int, connection_string: str):
        self.buffer_size = buffer_size
        self.buffer = []
        self.connection_string = connection_string
        # Initialize DB connection here

    def append(self, data: List[dict]):
        self.buffer.extend(data)

    def is_buffer_full(self) -> bool:
        return len(self.buffer) >= self.buffer_size

    def save_and_refresh(self):
        # Write data to DB
        # Refresh the buffer
        self.buffer = []
