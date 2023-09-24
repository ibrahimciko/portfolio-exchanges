class OrderbookRequestException(Exception):
    pass
    
    def __init__(self, message=None):
        self.message = message

class AccountBalanceRequestException(Exception):
    def __init__(self, message=None):
        self.message = message

class PairNotFoundError(Exception):
    def __init__(self, message=None):
        self.message = message

class AssetNotFoundError(Exception):
    def __init__(self, message=None):
        self.message = message


class MarketOrderNotSupportedError(Exception):
    def __init__(self, message=None):
        self.message = message


class InsufficientBalanceForArbitrage(Exception):
    def __init__(self, message=None):
        self.message = message


class ExecutionFailedAtStart(Exception):
    def __init__(self, message=None):
        self.message = message


class ExecutionFailedCritical(Exception):
    def __init__(self, message=None):
        self.message = message


class MissingApiKeyError(Exception):
    def __init__(self, message=None, name=None):
        if message is None:
            message = self._generic_message(name)
        super().__init__(message)
        
    def _generic_message(self, name: str = None):
        name = "" if name is None else name
        return f"missing API keys for the exchange {name}"
    
class PairNotFoundError(Exception):
    def __init__(self, message=None):
        self.message = message
        
class AssetNotFoundError(Exception):
    def __init__(self, message=None):
        self.message = message