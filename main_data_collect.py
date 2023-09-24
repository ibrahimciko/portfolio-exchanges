import argparse
import signal
import logging

# setup logging for entire application
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("application.log"),
        logging.StreamHandler()
    ]
)

# Suppress logs from 'requests' library
logging.getLogger("requests").setLevel(logging.WARNING)
# Suppress logs from httpx library
logging.getLogger("httpx").setLevel(logging.WARNING)

from src.utils.config_loader import load_config_by_name
from src.writer.factory import create_writer
from src.data_collector import DataCollector
from src.exchanges.exchange_factory import create_exchange


def parse_args():
    parser = argparse.ArgumentParser(description="Data Collector CLI options.")
    
    # Argument to overwrite writer choice
    parser.add_argument('--writer-type', type=str, help='Type of writer to use.', choices=['parquet_s3', 'db_aws', 'parquet_local'])
    
    # Argument to overwrite buffer size
    parser.add_argument('--buffer-size', type=int, help='Buffer size for the writer.')
    
    # Argument to overwrite sleep duration
    parser.add_argument('--sleep-duration', type=int, help='Sleep duration for the data collector.')
    
    return parser.parse_args()

def main():
    args = parse_args()
    logging.info(f"Starting data collection with args: {args}")
    
    # load data collector config and initialize exchanges
    data_collector_config = load_config_by_name("data_collector")
    logging.info(f"Loaded data collector config: {data_collector_config}")
    
    # Overwrite with command line arguments if provided
    if args.sleep_duration:
        data_collector_config['sleep_duration'] = args.sleep_duration
        
    exchanges = [create_exchange(name) for name in data_collector_config["pairs"].keys()]
    logging.info(f"Initialized exchanges: {[exchange.name for exchange in exchanges]}")
    
    # load writer config and initialize writer
    writer_config = load_config_by_name("writer")
    
    # Overwrite with command line arguments if provided
    if args.writer_type:
        logging.info(f"Overwriting writer type with {args.writer_type}")
        writer_config['type'] = args.writer_type
    if args.buffer_size:
        logging.info(f"Overwriting buffer size with {args.buffer_size}")
        writer_config['buffer_size'] = args.buffer_size
    
    writer = create_writer(writer_config)
    
    # initialize data collector
    data_collector = DataCollector(exchanges, writer)
    
    # register signal handler to stop data collection
    # Attach signal handlers
    signal.signal(signal.SIGINT, data_collector.graceful_shutdown)
    signal.signal(signal.SIGTERM, data_collector.graceful_shutdown)
    
    data_collector.fetch_forever()

if __name__ == "__main__":
    main()
