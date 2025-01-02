import unittest
import json
from unittest.mock import patch
from api import app
from database.setup_db import setup_database
import tempfile
import os

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            setup_database()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_get_messages_empty(self):
        response = self.app.get('/messages')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 0)

    def test_get_messages_with_protocol(self):
        # First add a message
        test_message = {
            "protocol": "Ethernet(Master)",
            "sender": "tester",
            "recipient": "test_recipient",
            "message": "test message"
        }
        self.app.post('/messages',
                     data=json.dumps(test_message),
                     content_type='application/json')
        
        # Then retrieve it with protocol filter
        response = self.app.get('/messages?protocol=Ethernet(Master)')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['message'], 'test message')

    def test_add_message_invalid_json(self):
        response = self.app.post('/messages',
                               data="invalid json",
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_add_message_missing_fields(self):
        test_message = {
            "sender": "tester",
            "message": "test message"
        }
        response = self.app.post('/messages',
                               data=json.dumps(test_message),
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_add_message_success(self):
        test_message = {
            "protocol": "test",
            "sender": "tester",
            "recipient": "test_recipient",
            "message": "test message"
        }
        response = self.app.post('/messages',
                               data=json.dumps(test_message),
                               content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue('id' in data)

if __name__ == '__main__':
    unittest.main()
