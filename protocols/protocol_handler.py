# protocols/protocol_handler.py

from abc import ABC, abstractmethod

class ProtocolHandler(ABC):
    @abstractmethod
    def send(self, message: str):
        pass

    @abstractmethod
    def receive(self) -> str:
        pass

    def initialize(self):
        """Optional initialization method"""
        pass

    def cleanup(self):
        """Optional cleanup method"""
        pass
