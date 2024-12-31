# protocols/protocol_handler.py

class ProtocolHandler:
    def send(self, message: str):
        """Send a message through the protocol."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def receive(self) -> str:
        """Receive a message through the protocol."""
        raise NotImplementedError("This method should be overridden by subclasses.")
