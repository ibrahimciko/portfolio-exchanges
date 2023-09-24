from typing import List
from src.writer.writer_interface import WriterInterface
from src.writer.s3_parquet import S3ParquetWriter
from src.writer.aws_ts import DBAWSWriter
from src.writer.local_parquet import LocalParquetWriter
from src.utils.config_loader import load_config_by_name

def create_parquet_s3_writer(buffer_size: int, 
                             partition_cols: List[str] = None) -> S3ParquetWriter:
    """
    Create an S3ParquetWriter instance using a specified configuration.

    Args:
        buffer_size (int): The size of the buffer to use.
        partition_cols (List[str], optional): The list of columns to use for partitioning.

    Returns:
        S3ParquetWriter: A configured S3ParquetWriter instance.
    """
    # Load the S3 configuration details from a centralized location
    config = load_config_by_name("data")["s3"]
    return S3ParquetWriter(config["bucket"], config["prefix"], buffer_size, partition_cols)


def create_db_aws_writer(buffer_size: int, connection_string: str) -> DBAWSWriter:
    """
    Create a DBAWSWriter instance.

    Args:
        buffer_size (int): The size of the buffer to use.
        connection_string (str): Connection string to the timeseries database.

    Returns:
        DBAWSWriter: A configured DBAWSWriter instance.
    """
    return DBAWSWriter(buffer_size, connection_string)


def create_parquet_local_writer(buffer_size: int, 
                                data_directory: str, 
                                partition_cols: List[str] = None) -> LocalParquetWriter:
    """
    Create a LocalParquetWriter instance.

    Args:
        buffer_size (int): The size of the buffer to use.
        data_directory (str): Directory to save the parquet files.
        partition_cols (List[str], optional): The list of columns to use for partitioning.

    Returns:
        LocalParquetWriter: A configured LocalParquetWriter instance.
    """
    return LocalParquetWriter(buffer_size, data_directory, partition_cols)


# Dictionary mapping writer types to their corresponding factory functions
WRITER_FACTORIES = {
    'parquet_s3': create_parquet_s3_writer,
    'db_aws': create_db_aws_writer,
    'parquet_local': create_parquet_local_writer,
}

def create_writer(writer_config: dict) -> WriterInterface:
    """
    Factory function to create a writer instance based on the given configuration.

    Args:
        writer_config (dict): Configuration details for the writer.

    Returns:
        WriterInterface: A writer instance based on the specified configuration.

    Raises:
        ValueError: If an unknown writer type is provided.
    """
    writer_type = writer_config["type"].lower()
    buffer_size = writer_config["buffer_size"]
    specific_config = writer_config.get(writer_type, {})

    config = {"buffer_size": buffer_size}
    config.update(specific_config)

    # Get the factory function for the specified writer type
    factory_function = WRITER_FACTORIES.get(writer_type)
    if factory_function is None:
        raise ValueError(f"Unknown writer type: {writer_type}")

    return factory_function(**config)

