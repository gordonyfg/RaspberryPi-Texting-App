import requests
import sqlite3
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
from flask import Flask, request, jsonify
import threading
from werkzeug.serving import make_server
import socket

def find_free_port(start_port=5000, max_attempts=100):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port after {max_attempts} attempts")

class FlaskThread(threading.Thread):
    def __init__(self, app, port):  # Add port parameter
        threading.Thread.__init__(self, daemon=True)
        # Allow connections from other devices
        self.srv = make_server('0.0.0.0', port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.port = port  # Store port number

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

class MessageBubble(Label):
    bubble_color = ListProperty([0, 0, 0, 0])

class ChatApp(App):
    def initialize_database(self):
        """Initialize the database if it doesn't exist"""
        connection = sqlite3.connect("database/chat_history.db")
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocol TEXT NOT NULL,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        connection.commit()
        connection.close()

    def setup_api(self):
        """Initialize and setup Flask API"""
        self.flask_app = Flask(__name__)

        @self.flask_app.route('/messages', methods=['GET'])
        def get_messages():
            protocol = request.args.get('protocol')
            connection = sqlite3.connect("database/chat_history.db")
            connection.row_factory = sqlite3.Row
            try:
                cursor = connection.cursor()
                if protocol:
                    messages = cursor.execute(
                        'SELECT * FROM messages WHERE protocol = ? ORDER BY timestamp',
                        [protocol]
                    ).fetchall()
                else:
                    messages = cursor.execute(
                        'SELECT * FROM messages ORDER BY timestamp'
                    ).fetchall()
                return jsonify([dict(msg) for msg in messages])
            finally:
                connection.close()

        @self.flask_app.route('/messages', methods=['POST'])
        def add_message():
            try:
                data = request.get_json()
                
                # Check for required fields
                required_fields = ['protocol', 'sender', 'recipient', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400

                connection = sqlite3.connect("database/chat_history.db")
                cursor = connection.cursor()
                
                cursor.execute('''
                    INSERT INTO messages (protocol, sender, recipient, message)
                    VALUES (?, ?, ?, ?)
                ''', [data['protocol'], data['sender'], data['recipient'], data['message']])
                
                message_id = cursor.lastrowid
                connection.commit()
                connection.close()
                
                return jsonify({'id': message_id}), 201
                
            except Exception as e:
                return jsonify({'error': str(e)}), 400

    def build(self):
        # Initialize database before starting the app
        self.initialize_database()
        
        # Find a free port for the API server
        self.api_port = find_free_port()
        
        # Setup and start API server
        self.setup_api()
        self.flask_thread = FlaskThread(self.flask_app, self.api_port)
        self.flask_thread.start()
        
        # Get the actual IP address of this device
        hostname = socket.gethostname()
        self.host_ip = socket.gethostbyname(hostname)
        
        # Update base URL to use actual IP
        self.base_url = f"http://{self.host_ip}:{self.api_port}/messages"
        
        # Initialize protocol handlers with actual IP
        self.protocol_port = 5001  # Fixed port for easier configuration
        self.protocol_handlers = {
            "TCP/IP(Server)": EthernetMasterHandler(host="0.0.0.0", port=self.protocol_port),
            "TCP/IP(Client)": EthernetClientHandler(host="<MASTER_PI_IP>", port=self.protocol_port),
            "UART/Serial": UARTHandler(port="/dev/ttyUSB0", baudrate=9600),
            # Future protocols:
            # "SPI": SPIHandler(bus=0, device=0),
            # "I2C": I2CHandler(bus=1, address=0x48),
            # "CAN": CANHandler(channel="can0", bitrate=500000),
            # "EtherCAT": EtherCATHandler(interface="eth0"),
        }
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
        
        if self.current_protocol.startswith("TCP/IP"):  # Update condition
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
        # Shutdown Flask server
        if hasattr(self, 'flask_thread'):
            self.flask_thread.shutdown()

if __name__ == "__main__":
    ChatApp().run()
