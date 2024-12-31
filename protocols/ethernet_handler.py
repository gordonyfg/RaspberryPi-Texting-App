# protocols/ethernet_handler.py
from protocols.protocol_handler import ProtocolHandler

class EthernetHandler(ProtocolHandler):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def send(self, message: str):
        print(f"Ethernet: Sending message: {message}")

    def receive(self) -> str:
        return "Ethernet: Received a message"
