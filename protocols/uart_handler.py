# protocols/uart_handler.py
from protocols.protocol_handler import ProtocolHandler

class UARTHandler(ProtocolHandler):
    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate

    def send(self, message: str):
        print(f"UART: Sending message '{message}' on port {self.port} at {self.baudrate} baud")

    def receive(self) -> str:
        return "UART: Message received!"
