# app.py
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from protocols.uart_handler import UARTHandler
from protocols.ethernet_handler import EthernetHandler

class ChatApp(App):
    def build(self):
        self.protocol_handlers = {
            "UART": UARTHandler(port="/dev/ttyUSB0", baudrate=9600),
            "Ethernet": EthernetHandler(host="127.0.0.1", port=5000),
        }
        return self.root

    def send_message(self):
        protocol_spinner = self.root.ids.protocol_spinner.text
        message_input = self.root.ids.message_input.text
        chat_history = self.root.ids.chat_history

        handler = self.protocol_handlers.get(protocol_spinner)
        if handler:
            handler.send(message_input)
            response = handler.receive()
            chat_history.text += f"\nYou: {message_input}\n{protocol_spinner}: {response}"

if __name__ == "__main__":
    ChatApp().run()
