import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import ListProperty
from kivy.clock import Clock
from protocols.uart_handler import UARTHandler
from protocols.ethernet_handler import EthernetMasterHandler, EthernetClientHandler
from functools import partial
from kivy.uix.widget import Widget

class MessageBubble(Label):
    bubble_color = ListProperty([0, 0, 0, 0])

class ChatApp(App):
    def build(self):
        # Initialize protocol handlers
        self.protocol_handlers = {
            "Ethernet(Master)": EthernetMasterHandler(host="127.0.0.1", port=5001),
            "Ethernet(Client)": EthernetClientHandler(host="127.0.0.1", port=5001),
            "UART": UARTHandler(port="/dev/ttyUSB0", baudrate=9600),
        }
        self.base_url = "http://127.0.0.1:5000/messages"
        self.current_protocol = None
        self.setup_protocol_list()
        self.scroll_to_bottom = Clock.create_trigger(self._scroll_to_bottom, timeout=0.1)
        self.start_receiving()
        self.connection_lost_shown = False  # Add flag for connection message
        return self.root

    def _scroll_to_bottom(self, dt):
        scroll_view = self.root.ids.chat_scroll
        if (scroll_view):
            scroll_view.scroll_y = 0

    def setup_protocol_list(self):
        protocol_list = self.root.ids.protocol_list
        protocol_list.clear_widgets()
        
        for protocol in self.protocol_handlers.keys():
            btn = Button(
                text=protocol,
                size_hint_y=None,
                height=40,
                background_normal="",
                background_color=(0.35, 0.35, 0.35, 1) if protocol != self.current_protocol else (0.8, 0.8, 1, 1)
            )
            btn.bind(on_press=lambda x, p=protocol: self.select_protocol(p))
            protocol_list.add_widget(btn)

    def select_protocol(self, protocol):
        # Reset connection lost flag when switching protocols
        self.connection_lost_shown = False
        # Cleanup previous protocol if exists
        if self.current_protocol and hasattr(self.protocol_handlers[self.current_protocol], 'cleanup'): 
            print("Cleaning up previous protocol")
            cleanup_msg = self.protocol_handlers[self.current_protocol].cleanup()
            if cleanup_msg:
                self.add_message_bubble("System", cleanup_msg, False)
            
        self.current_protocol = protocol
        self.setup_protocol_list()
        
        # Initialize new protocol
        handler = self.protocol_handlers[protocol]
        #if hasattr(handler, 'initialize'):
        status_message = handler.initialize()

        self.load_chat_history()
        self.add_message_bubble("System", status_message, False)

    def start_receiving(self):
        # Schedule periodic checking for new messages
        Clock.schedule_interval(self._check_messages, 0.1)  # Check every 100ms

    def _check_messages(self, dt):
        if not self.current_protocol:
            return
        
        if self.current_protocol.startswith("Ethernet"):
            handler = self.protocol_handlers[self.current_protocol]
            
            # Check if client lost connection
            if isinstance(handler, EthernetClientHandler) and not handler.connected:
                if not self.connection_lost_shown:
                    self.add_message_bubble("System", "Lost connection to server", False)
                    self.connection_lost_shown = True
                return
                
            # Reset the flag when connected
            if isinstance(handler, EthernetClientHandler) and handler.connected:
                self.connection_lost_shown = False
                
            response = handler.receive()
            if response != "No messages":
                # Save received message to database
                data = {
                    "protocol": self.current_protocol,
                    "sender": "Client" if isinstance(handler, EthernetMasterHandler) else "Master",
                    "recipient": "You",
                    "message": response
                }
                try:
                    requests.post(self.base_url, json=data)
                    self.add_message_bubble(data["sender"], response, False)
                except requests.exceptions.RequestException:
                    pass  # Silently fail database updates

    def send_message(self):
        if not self.current_protocol:
            return
            
        message_input = self.root.ids.message_input.text.strip()
        if not message_input:
            return

        handler = self.protocol_handlers.get(self.current_protocol)
        if handler:
            result = handler.send(message_input)
            if result and isinstance(result, str):  # Check for error message
                self.add_message_bubble("System", result, False)
                # If client lost connection, clear current protocol
                if isinstance(handler, EthernetClientHandler) and not handler.connected:
                    self.current_protocol = None
                    self.setup_protocol_list()
                return
            
            # Update database via API
            data = {
                "protocol": self.current_protocol,
                "sender": "You",
                "recipient": "Device",
                "message": message_input,
            }
            try:
                requests.post(self.base_url, json=data)
                self.add_message_bubble("You", message_input, True)
                self.root.ids.message_input.text = ""
            except requests.exceptions.RequestException as e:
                self.add_message_bubble("Error", str(e), False)

    def add_message_bubble(self, sender, message, is_sender):
        chat_history = self.root.ids.chat_history
        wrapper = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            spacing=5,  # Reduced spacing
            padding=[0, 2]  # Reduced padding
        )
        
        # Left spacing for receiver, right spacing for sender
        if is_sender:
            wrapper.add_widget(Widget(size_hint_x=0.43))
        else:
            wrapper.add_widget(Widget(size_hint_x=0.02))
            
        bubble = MessageBubble(
            text=f"{sender}:\n{message}",
            bubble_color=(0.2, 0.5, 0.8, 1) if is_sender else (0.25, 0.25, 0.25, 1),
            size_hint_x=0.55,
            size_hint_y=None,  # Allow height to adjust to content
            color=(0.95, 0.95, 0.95, 1)
        )
        
        # Bind bubble height to wrapper height
        def update_height(*args):
            wrapper.height = bubble.height
        bubble.bind(height=update_height)
        
        wrapper.add_widget(bubble)
        
        # Right spacing for receiver, left spacing for sender
        if is_sender:
            wrapper.add_widget(Widget(size_hint_x=0.02))
        else:
            wrapper.add_widget(Widget(size_hint_x=0.43))
            
        chat_history.add_widget(wrapper)
        self.scroll_to_bottom()

    def load_chat_history(self):
        if not self.current_protocol:
            return
            
        chat_history = self.root.ids.chat_history
        chat_history.clear_widgets()
        
        try:
            response = requests.get(f"{self.base_url}?protocol={self.current_protocol}")
            messages = response.json()

            for msg in messages:
                is_sender = msg['sender'] == 'You'
                self.add_message_bubble(msg['sender'], msg['message'], is_sender)
            
            self.scroll_to_bottom()
                
        except requests.exceptions.RequestException as e:
            self.add_message_bubble("Error", str(e), False)

    def on_stop(self):
        Clock.unschedule(self._check_messages)  # Stop message checking
        # Cleanup all handlers when app closes
        for handler in self.protocol_handlers.values():
            if hasattr(handler, 'cleanup'):
                handler.cleanup()

if __name__ == "__main__":
    ChatApp().run()
