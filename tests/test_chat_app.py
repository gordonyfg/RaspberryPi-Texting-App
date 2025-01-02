import unittest
from unittest.mock import Mock, patch, PropertyMock
from chatapp import ChatApp, MessageBubble

class TestChatApp(unittest.TestCase):
    def setUp(self):
        # Create the app
        self.app = ChatApp()
        
        # Setup protocol handlers before initializing the app
        self.app.protocol_handlers = {
            "Ethernet(Master)": Mock(),
            "Ethernet(Client)": Mock(),
            "UART": Mock()
        }
        
        # Mock Kivy properties
        self.app.current_protocol = None
        self.app.connection_lost_shown = False
        
        # Create a proper mock structure for Kivy widgets
        chat_history = Mock()
        message_input = Mock()
        type(message_input).text = PropertyMock(return_value="")
        protocol_list = Mock()
        chat_scroll = Mock()
        
        # Create a root widget mock with proper ids structure
        root = Mock()
        root.ids = {
            'chat_history': chat_history,
            'message_input': message_input,
            'protocol_list': protocol_list,
            'chat_scroll': chat_scroll
        }
        self.app.root = root
        
        # Initialize base URL
        self.app.base_url = "http://127.0.0.1:5000/messages"

    def test_select_protocol(self):
        protocol = "Ethernet(Master)"
        handler_mock = self.app.protocol_handlers[protocol]
        handler_mock.initialize.return_value = "Connected successfully"
        
        with patch.object(self.app, 'load_chat_history'):
            self.app.select_protocol(protocol)
            
            self.assertEqual(self.app.current_protocol, protocol)
            handler_mock.initialize.assert_called_once()
            self.app.load_chat_history.assert_called_once()

    @patch('requests.post')
    def test_send_message_no_protocol(self, mock_post):
        self.app.current_protocol = None
        type(self.app.root.ids.message_input).text = PropertyMock(return_value="test message")
        
        self.app.send_message()
        
        mock_post.assert_not_called()

    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        # Setup
        protocol = "Ethernet(Master)"
        self.app.current_protocol = protocol
        message = "test message"
        type(self.app.root.ids.message_input).text = PropertyMock(return_value=message)
        
        # Mock the handler
        handler_mock = self.app.protocol_handlers[protocol]
        handler_mock.send.return_value = None  # Successful send
        
        # Mock successful API response
        mock_post.return_value.status_code = 201
        
        # Execute
        self.app.send_message()
        
        # Assert
        handler_mock.send.assert_called_with(message)
        mock_post.assert_called_once()
        self.app.root.ids.message_input.text = ""

    @patch('requests.get')
    def test_load_chat_history(self, mock_get):
        # Setup
        self.app.current_protocol = "Ethernet(Master)"
        mock_get.return_value.json.return_value = [
            {"sender": "You", "message": "Hello"},
            {"sender": "Client", "message": "Hi"}
        ]
        
        # Execute
        self.app.load_chat_history()
        
        # Assert
        self.app.root.ids.chat_history.clear_widgets.assert_called_once()
        self.assertEqual(self.app.root.ids.chat_history.add_widget.call_count, 2)

    def test_add_message_bubble(self):
        # Setup mock widgets
        chat_history = self.app.root.ids.chat_history
        
        # Execute
        self.app.add_message_bubble("Test", "Hello", True)
        
        # Assert
        chat_history.add_widget.assert_called_once()

if __name__ == '__main__':
    unittest.main()
