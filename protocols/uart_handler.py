# protocols/uart_handler.py
from protocols.protocol_handler import ProtocolHandler

class UARTHandler(ProtocolHandler):
    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate

    def send(self, message: str):
        print(f"UART: Sending message: {message}")

    def receive(self) -> str:
        return "UART: Received a message"
