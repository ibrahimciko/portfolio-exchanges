from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class WriterInterface(ABC):
    """
    Abstract class defining the interface for a writer object.

    This interface ensures that the writer has methods to append data,
    check if a buffer is full, and save & refresh its contents.
    """

    @abstractmethod
    def append(self, data: List[dict], event_type):
        """
        Appends the given data.

        Args:
            data (List[dict]): Data to append.
        """
        pass

    @abstractmethod
    def is_buffer_full(self, event_type) -> bool:
        """
        Checks if the buffer is full.

        Returns:
            bool: True if buffer is full, False otherwise.
        """
        pass

    @abstractmethod
    def save_and_refresh(self, event_type):
        """
        Saves the current buffer's data and then refreshes the buffer.
        """
        pass

    def _list_of_dict_to_df(self, data: List[dict]) -> pd.DataFrame:
        """
        Converts a list of dictionaries to a pandas DataFrame.

        Args:
            data (List[dict]): List of dictionaries to be converted.

        Returns:
            pd.DataFrame: The converted pandas DataFrame.
        """
        return pd.DataFrame(data)
