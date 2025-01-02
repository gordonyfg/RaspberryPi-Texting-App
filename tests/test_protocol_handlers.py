import unittest
from unittest.mock import Mock, patch
from protocols.ethernet_handler import EthernetMasterHandler, EthernetClientHandler
from protocols.uart_handler import UARTHandler
import socket
import json

class TestEthernetMasterHandler(unittest.TestCase):
    def setUp(self):
        self.handler = EthernetMasterHandler("localhost", 5000)
        self.status_messages = []
        self.handler.set_status_callback(lambda msg: self.status_messages.append(msg))

    @patch('socket.socket')
    def test_initialize(self, mock_socket):
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        
        result = self.handler.initialize()
        
        mock_socket_instance.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mock_socket_instance.bind.assert_called_with(("localhost", 5000))
        mock_socket_instance.listen.assert_called_with(1)
        self.assertTrue(self.handler.is_running)
        self.assertIn("Server listening", result)

    def test_send_no_clients(self):
        result = self.handler.send("test message")
        self.assertEqual(result, "No clients connected")

    @patch('socket.socket')
    def test_send_with_client(self, mock_socket):
        mock_client = Mock()
        client_address = ("127.0.0.1", 5000)
        self.handler.connected_clients[client_address] = mock_client
        
        self.handler.send("test message")
        
        expected_data = json.dumps({
            "content": "test message",
            "type": "message"
        }).encode()
        mock_client.send.assert_called_with(expected_data)

    def test_cleanup(self):
        mock_client = Mock()
        client_address = ("127.0.0.1", 5000)
        self.handler.connected_clients[client_address] = mock_client
        self.handler.server_socket = Mock()
        
        result = self.handler.cleanup()
        
        self.assertFalse(self.handler.is_running)
        mock_client.close.assert_called()
        self.handler.server_socket.close.assert_called()
        self.assertEqual(result, "Server stopped")

class TestEthernetClientHandler(unittest.TestCase):
    def setUp(self):
        self.handler = EthernetClientHandler("localhost", 5000)

    @patch('socket.socket')
    def test_initialize_success(self, mock_socket):
        # Setup mock socket
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        
        # Mock successful connection
        mock_socket_instance.connect.return_value = None  # Successful connection
        mock_socket_instance.recv.return_value = json.dumps({
            "type": "message",
            "content": "test"
        }).encode()
        
        # Execute
        result = self.handler.initialize()
        
        # Assert
        mock_socket_instance.connect.assert_called_with(("localhost", 5000))
        self.assertTrue(self.handler.connected)
        self.assertTrue(self.handler.is_running)
        self.assertIn("Client connected", result)

    @patch('socket.socket')
    def test_initialize_connection_refused(self, mock_socket):
        mock_socket_instance = Mock()
        mock_socket_instance.connect.side_effect = ConnectionRefusedError
        mock_socket.return_value = mock_socket_instance
        
        result = self.handler.initialize()
        
        self.assertFalse(self.handler.connected)
        self.assertFalse(self.handler.is_running)
        self.assertIn("Failed to connect", result)

    def test_send_not_connected(self):
        result = self.handler.send("test message")
        self.assertEqual(result, "Not connected to server")

    @patch('socket.socket')
    def test_cleanup(self, mock_socket):
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        self.handler.client_socket = mock_socket_instance
        self.handler.connected = True
        self.handler.is_running = True
        
        result = self.handler.cleanup()
        
        self.assertFalse(self.handler.connected)
        self.assertFalse(self.handler.is_running)
        mock_socket_instance.close.assert_called()
        self.assertEqual(result, "Client disconnected")

class TestUARTHandler(unittest.TestCase):
    def setUp(self):
        self.handler = UARTHandler("/dev/ttyUSB0", 9600)

    def test_send(self):
        result = self.handler.send("test message")
        self.assertIsNone(result)

    def test_receive(self):
        result = self.handler.receive()
        self.assertEqual(result, "UART: Message received!")

if __name__ == '__main__':
    unittest.main()
