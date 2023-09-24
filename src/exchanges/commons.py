import functools
import logging
import os
from typing import Union
import traceback

def configure_root_logger():
    root_logger = logging.getLogger()
    # logging.basicConfig(level = logging.INFO)
    # fh = logging.FileHandler("logs/root_path.log")
    # ch = logging.StreamHandler()
    # formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    # fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    # # # add the handlers to the logger
    # root_logger.addHandler(fh)
    # root_logger.addHandler(ch)

def configure_module_logger(logger_name:str,
                            file_name,
                            file_dir: str = "logs",
                            file_format:str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                            log_level: int = logging.DEBUG,
                            stream_format:str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'):
    logger = logging.getLogger(logger_name)
    # add file handler
    fh = configure_file_handler_for_module(file_name, file_dir, format=file_format)
    logger.addHandler(fh)
    # add stream handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(stream_format))
    logger.addHandler(ch)
    logger.propagate = False
    logger.setLevel(log_level)
    return logger


def configure_file_handler_for_module(file_name:str,
                                        dir: str = None,
                                        format: str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s' 
    ) -> logging.FileHandler:
    if dir:
        os.makedirs(f"./{dir}", exist_ok=True)
    path = os.path.join(dir, file_name)
    fh = logging.FileHandler(path)
    formatter = logging.Formatter(format)
    fh.setFormatter(formatter)
    return fh



def log_exceptions(_func=None, *, my_logger:logging.Logger = None, raise_error: bool = False):
    def decorator_log(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = my_logger
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.info(f"function {func.__name__} called with args {signature}")
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"Exception found {func.__name__} in class {func.__qualname__}. Exception: {str(e)}")
                logger.error(traceback.format_exc())
                if raise_error:
                    raise e
                else:
                    logger.error("Error has not been raised by the general log_exceptions decorator. Please handle the error customly.")
        return wrapper
    if _func is None:
        return decorator_log
    else:
        return decorator_log(_func)
    
    
    
class RequestLimitExceededError(Exception):
    """Raised when the http requests pass beyond the limit of the exchange
    """
    def __init__(self, message="Limit exceeded."):
        self.message = message
        super().__init__(self.message)
        
        
class InternalServerError(Exception):
    pass
