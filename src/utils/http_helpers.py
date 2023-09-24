import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from json import JSONDecodeError
import logging
import time
import functools

import asyncio

from src.exchanges.exceptions import MissingApiKeyError


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def fetch_json(url, retries=3, context=None, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
            return response.json()

        except (ConnectionError, Timeout) as e:
            # Maybe log the error here and retry
            msg = f"Connection error occurred on attempt {attempt} of {retries}: {e}"
            if context:
                msg = f"Context: {context}. {msg}"
            logger.error(msg)
            if attempt == retries:
                raise e
            # Optional: sleep for 2 seconds (or any desired delay)
            time.sleep(2)

        except HTTPError as http_err:
            msg = f"Error {http_err} occurred while fetching {url}."
            if context:
                msg = f"Context: {context}. {msg}"
            logger.error(msg)
            if attempt == retries:
                raise http_err

        except JSONDecodeError as json_err:
            msg = f"JSON decode error occurred: {json_err}, response: {response.text}"
            if context:
                msg = f"Context: {context}. {msg}"
            logger.error(msg)
            if attempt == retries:
                raise json_err
            
def retry_on_failure(exception_type=Exception):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_type as e:
                logger.exception(f"Error in function {func.__name__}: {e}. Retrying...")
                
                # Retry
                try:
                    return func(*args, **kwargs)
                except exception_type as retry_error:
                    logger.exception(f"Error in function {func.__name__} on retry: {retry_error}. Raising error.")
                    raise
        return wrapper
    return decorator

def async_retry_on_failure(attempts=3, delay=5):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logging.exception("An error occurred in attempt %s:", attempt + 1)
                    if attempt < attempts - 1:
                        await asyncio.sleep(delay)  # Wait for 'delay' seconds before retrying
                    else:
                        raise  # Raise the last exception
        return wrapper
    return decorator


def requires_authentication(method):
    """
    Decorator to check if the object has been authenticated.
    """
    def wrapper(self, *args, **kwargs):
        if not self.public_key or not self.private_key:
            raise MissingApiKeyError(name=self.name)
        return method(self, *args, **kwargs)
    return wrapper
