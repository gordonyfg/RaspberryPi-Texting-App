# protocols/ethernet_handler.py
from protocols.protocol_handler import ProtocolHandler
import socket
import threading
from queue import Queue
import json

class EthernetMasterHandler(ProtocolHandler):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self._lock = threading.Lock()
        self.status_callback = None
        self.connected_clients = {}  # Store client sockets
        self.message_queue = Queue()
        self.last_message = None  # Add this for handling received messages

    def set_status_callback(self, callback):
        self.status_callback = callback

    def _notify_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def initialize(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Add socket reuse options
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.is_running = True
            threading.Thread(target=self._listen_for_connections, daemon=True).start()
            return f"Server listening on {self.host}:{self.port}"
        except Exception as e:
            return f"Failed to start server: {str(e)}"

    def _handle_client(self, client_socket, address):
        while self.is_running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                self.message_queue.put(message)
                self.last_message = message['content']  # Store last message
                self._notify_status(f"Message from {address[0]}:{address[1]}: {message['content']}")
            except json.JSONDecodeError:
                self._notify_status(f"Invalid message format from {address[0]}:{address[1]}")
            except Exception as e:
                self._notify_status(f"Error handling client {address[0]}:{address[1]}: {str(e)}")
                break
        
        # Clean up client connection
        with self._lock:
            if address in self.connected_clients:
                del self.connected_clients[address]
        client_socket.close()
        self._notify_status(f"Client {address[0]}:{address[1]} disconnected")

    def _listen_for_connections(self):
        while self.is_running:
            try:
                client_socket, address = self.server_socket.accept()
                with self._lock:
                    self.connected_clients[address] = client_socket
                self._notify_status(f"Client connected from {address[0]}:{address[1]}")
                # Start a new thread to handle client communication
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
            except Exception as e:
                if self.is_running:
                    self._notify_status(f"Connection error: {str(e)}")

    def send(self, message: str):
        with self._lock:
            if not self.connected_clients:
                return "No clients connected"
            
            data = json.dumps({
                "content": message,
                "type": "message"
            }).encode()
            
            # Send to all connected clients
            for addr, client in self.connected_clients.items():
                try:
                    client.send(data)
                except Exception as e:
                    self._notify_status(f"Failed to send to {addr[0]}:{addr[1]}: {str(e)}")

    def receive(self) -> str:
        try:
            message = self.message_queue.get_nowait()
            return message['content']
        except:
            return "No messages"

    def cleanup(self):
        with self._lock:
            self.is_running = False
            if self.server_socket:
                try:
                    # Close all client connections first
                    for client in self.connected_clients.values():
                        try:
                            client.shutdown(socket.SHUT_RDWR)
                            client.close()
                        except:
                            pass
                    self.connected_clients.clear()
                    
                    # Then close server socket
                    self.server_socket.shutdown(socket.SHUT_RDWR)
                    self.server_socket.close()
                except:
                    pass
                finally:
                    self.server_socket = None
        return "Server stopped"

class EthernetClientHandler(ProtocolHandler):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.client_socket = None
        self.is_running = False
        self.message_queue = Queue()
        self._lock = threading.Lock()
        self.connected = False  # Add connection state
        self.last_message = None  # Add this for handling received messages

    def initialize(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
            self.is_running = True
            self.connected = True
            # Start receiving thread
            threading.Thread(target=self._receive_messages, daemon=True).start()
            return f"Client connected to {self.host}:{self.port}"
        except ConnectionRefusedError:
            self.connected = False
            self.is_running = False
            return f"Failed to connect to {self.host}:{self.port} - No server found"
        except Exception as e:
            self.connected = False
            self.is_running = False
            return f"Connection error: {str(e)}"

    def _receive_messages(self):
        while self.is_running:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    self.connected = False
                    self.is_running = False
                    print("Server disconnected")
                    break
                message = json.loads(data.decode())
                self.message_queue.put(message)
                self.last_message = message['content']  # Store last message
            except ConnectionResetError:
                self.connected = False
                self.is_running = False
                print("Connection reset by server")
                break
            except Exception as e:
                print(f"Receive error: {str(e)}")
                self.connected = False
                self.is_running = False
                break

    def send(self, message: str):
        if not self.is_running or not self.client_socket or not self.connected:
            return "Not connected to server"
        
        try:
            # Test connection before sending
            self.client_socket.settimeout(1.0)  # Set timeout for connection test
            self.client_socket.send(b"")  # Test send
            self.client_socket.settimeout(None)  # Reset timeout
            
            data = json.dumps({
                "content": message,
                "type": "message"
            }).encode()
            self.client_socket.send(data)
        except (ConnectionResetError, BrokenPipeError):
            self.connected = False
            self.is_running = False
            return "Server connection lost"
        except socket.timeout:
            self.connected = False
            self.is_running = False
            return "Server not responding"
        except Exception as e:
            self.connected = False
            self.is_running = False
            return f"Send error: {str(e)}"

    def receive(self) -> str:
        try:
            message = self.message_queue.get_nowait()
            return message['content']
        except:
            return "No messages"

    def cleanup(self):
        self.is_running = False
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.client_socket.close()
            self.client_socket = None
        return "Client disconnected"
