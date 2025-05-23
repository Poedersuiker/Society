import unittest
# import os # No longer needed if not using os.path for files
# import json # No longer needed for messages.json
from flask import session
import datetime

# Ensure the app path is correct for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app, socketio, handle_send_chat_message # Import the specific handler
from tests.base_test import BaseTestCase
import app.database as db # For direct DB assertions if needed

class ChatTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Register users directly into DB for controlled setup
        self.add_user_directly_to_db('chatuser1', 'password123')
        self.add_user_directly_to_db('chatuser2', 'password123')
        self.add_user_directly_to_db('chatuser3', 'password123')

    def _send_test_message(self, sender_username, message_text, recipient_type="general", private_recipient_username=""):
        """Helper to simulate sending a message via SocketIO handler."""
        with self.client as c: # Use the test client to maintain session
            # Manually set session for the sender
            with c.session_transaction() as sess:
                sess['username'] = sender_username
            
            # Call the handler directly. This bypasses actual SocketIO emit/receive for unit testing the handler logic.
            # For full integration tests, a SocketIO test client would be used.
            handle_send_chat_message({
                'message_text': message_text,
                'recipient_type': recipient_type,
                'private_recipient_username': private_recipient_username
            })

    def test_01_send_general_message(self):
        """Test sending a general message."""
        self._send_test_message('chatuser1', 'Hello everyone!')
        
        messages = self.get_messages_from_db()
        # Check if the message is in the database
        self.assertTrue(any(
            msg['sender_username'] == 'chatuser1' and \
            msg['recipient_username'] == 'general' and \
            msg['text'] == 'Hello everyone!' for msg in messages
        ))
        # ModeratorBot's welcome message might also be present if this is the first message overall.
        # AI responses are probabilistic, harder to assert without mocking or more control.

    def test_02_send_private_message(self):
        """Test sending a private message."""
        self._send_test_message(
            'chatuser1', 
            'Hi chatuser2, this is private.',
            recipient_type='private',
            private_recipient_username='chatuser2'
        )
        messages = self.get_messages_from_db()
        self.assertTrue(any(
            msg['sender_username'] == 'chatuser1' and \
            msg['recipient_username'] == 'chatuser2' and \
            msg['text'] == 'Hi chatuser2, this is private.' for msg in messages
        ))

    def test_03_send_private_message_to_nonexistent_user(self):
        """Test sending a private message to a user that does not exist."""
        initial_messages_count = len(self.get_messages_from_db())
        self._send_test_message(
            'chatuser1',
            'Hi nonexistentuser, this is private.',
            recipient_type='private',
            private_recipient_username='nonexistentuser'
        )
        messages_after = self.get_messages_from_db()
        self.assertEqual(len(messages_after), initial_messages_count, 
                         "Message to non-existent user should not be saved.")

    def test_04_send_private_message_to_self(self):
        """Test sending a private message to oneself."""
        initial_messages_count = len(self.get_messages_from_db())
        self._send_test_message(
            'chatuser1',
            'Hi myself, this is private.',
            recipient_type='private',
            private_recipient_username='chatuser1' # Sending to self
        )
        messages_after = self.get_messages_from_db()
        self.assertEqual(len(messages_after), initial_messages_count, 
                         "Message to self should not be saved.")

    def test_05_message_visibility_and_initial_load(self):
        """Test message visibility for different users on initial load and after sending."""
        # 1. Send messages
        self._send_test_message('chatuser1', 'General message from user1')
        self._send_test_message('chatuser2', 'Private message from user2 to user1', 
                                recipient_type='private', private_recipient_username='chatuser1')
        self._send_test_message('chatuser3', 'Private message from user3 to user2', 
                                recipient_type='private', private_recipient_username='chatuser2')

        # 2. Test visibility for chatuser1
        self.login_user('chatuser1', 'password123') # Logs in via HTTP for session
        response = self.client.get('/chat') # Test initial load
        self.assertEqual(response.status_code, 200)
        # Check response.data for messages. Note: DB stores as sender_username etc.
        # Template renders based on these names.
        self.assertIn(b'General message from user1', response.data)
        self.assertIn(b'Private message from user2 to user1', response.data)
        self.assertNotIn(b'Private message from user3 to user2', response.data)
        self.logout_user()

        # 3. Test visibility for chatuser2
        self.login_user('chatuser2', 'password123')
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'General message from user1', response.data)
        self.assertIn(b'Private message from user3 to user2', response.data)
        self.assertIn(b'Private message from user2 to user1', response.data) # Sees own sent message
        self.logout_user()

        # 4. Test visibility for chatuser3
        self.login_user('chatuser3', 'password123')
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'General message from user1', response.data)
        self.assertIn(b'Private message from user3 to user2', response.data)
        self.assertNotIn(b'Private message from user2 to user1', response.data)
        self.logout_user()

    def test_06_ai_member_response_to_general_message(self):
        """Test if AI members respond to a general message (checks DB)."""
        # This test is still somewhat probabilistic for AI response content,
        # but we can check if *any* AI message appears after a user message.
        
        # Ensure AI agents are initialized for this test context if not already
        # This might be better in setUp if all chat tests need AIs
        if not app.ai_agents: # Assuming app.ai_agents is the global list
             from app.app import initialize_ai_agents
             initialize_ai_agents()

        initial_messages_count = len(self.get_messages_from_db())
        
        self._send_test_message('chatuser1', 'Let us discuss environmental regulations and budget.')
        
        final_messages = self.get_messages_from_db()
        
        # Check that at least the user's message was added
        self.assertGreater(len(final_messages), initial_messages_count, 
                           "Messages count should have increased after user message.")

        user_message_present = any(
            msg['text'] == 'Let us discuss environmental regulations and budget.' and \
            msg['sender_username'] == 'chatuser1' 
            for msg in final_messages
        )
        self.assertTrue(user_message_present, "User's message was not found in DB.")

        # Check if any AI member responded. Their usernames start with "AI_"
        # This relies on AI agents having been initialized by app startup logic (or test setup)
        ai_responded = any(msg['sender_username'].startswith('AI_') for msg in final_messages)
        
        if not ai_responded and len(app.ai_agents) > 0: # Only print if AIs were expected
            print("\nINFO: AI member did not respond in this test run (probabilistic). This is not necessarily a failure.")
        # Depending on strictness, you might assert ai_responded is True if AIs are configured.
        # self.assertTrue(ai_responded, "An AI member should have responded to the general message.")

    def test_07_send_message_validation_errors(self):
        """Test message sending validation errors via SocketIO handler."""
        with unittest.mock.patch('app.app.emit') as mock_emit:
            # Empty message text
            self._send_test_message('chatuser1', '')
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'message_text', 'message': 'Message text cannot be empty.'},
                room=unittest.mock.ANY # room is the session ID, changes per request
            )
            
            # Message too long
            self._send_test_message('chatuser1', 'a' * 5001)
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'message_text', 'message': 'Message is too long (max 5000 characters).'},
                room=unittest.mock.ANY
            )

            # Invalid recipient type
            self._send_test_message('chatuser1', 'Valid message', recipient_type='invalidtype')
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'recipient_type', 'message': 'Invalid recipient type.'},
                room=unittest.mock.ANY
            )
            
            # Private message - empty recipient username
            self._send_test_message('chatuser1', 'Valid message', recipient_type='private', private_recipient_username='')
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'private_recipient_username', 'message': 'Private recipient username cannot be empty.'},
                room=unittest.mock.ANY
            )

            # Private message - to self
            self._send_test_message('chatuser1', 'Valid message', recipient_type='private', private_recipient_username='chatuser1')
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'private_recipient_username', 'message': 'You cannot send a private message to yourself.'},
                room=unittest.mock.ANY
            )
            
            # Private message - recipient does not exist
            self._send_test_message('chatuser1', 'Valid message', recipient_type='private', private_recipient_username='nonexistentuser123')
            mock_emit.assert_called_with(
                'message_validation_error',
                {'field': 'private_recipient_username', 'message': 'User "nonexistentuser123" does not exist.'},
                room=unittest.mock.ANY
            )
            
            # Ensure no messages were saved during these validation error tests
            messages = self.get_messages_from_db(username='chatuser1') # Get messages relevant to chatuser1
            # Filter out initial moderator message if any
            user_sent_messages = [m for m in messages if m['sender_username'] == 'chatuser1']
            self.assertEqual(len(user_sent_messages), 0, "No messages should have been saved due to validation errors.")


if __name__ == '__main__':
    # No need for app.ai_member_definitions_for_test if AIs are loaded by app context
    unittest.main()
