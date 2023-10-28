from abc import ABC, abstractmethod


class NNInterface(ABC):

    @abstractmethod
    def post(self, data: dict) -> dict:
        raise NotImplementedError


class NNException(Exception):
    pass


class NNFailTimeoutException(NNException):
    pass


class NNReturnedBadJSONException(NNException):
    pass
