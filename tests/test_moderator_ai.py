import unittest
from unittest.mock import MagicMock, patch
import datetime

# Ensure the app path is correct for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.moderator_ai import ModeratorAI
# Assuming app.database is available for mocking if ModeratorAI directly uses it.
# For this test, we'll mock the send_message method of ModeratorAI itself.

class TestModeratorAI(unittest.TestCase):

    def setUp(self):
        # Create a mock socketio instance if needed for send_message,
        # but we are mocking send_message itself.
        # If db_module is used by process_message (it's not directly), mock it.
        self.mock_socketio = MagicMock()
        self.mock_db = MagicMock() 
        self.moderator = ModeratorAI(socketio_instance=self.mock_socketio, db_module=self.mock_db)
        # Replace the send_message method with a mock for testing process_message
        self.moderator.send_message = MagicMock()

    def test_process_message_with_offensive_keyword(self):
        """Test processing a message containing an offensive keyword."""
        self.moderator.offensive_keywords = ["darn", "heck"] # Set specific keywords for test
        
        offensive_message = {
            "sender_username": "user123",
            "recipient_username": "general",
            "text": "This is a darn bad message!",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.moderator.process_message(offensive_message)

        # Assert that send_message was called
        self.moderator.send_message.assert_called_once()
        
        # Assert that send_message was called with the correct arguments
        args, _ = self.moderator.send_message.call_args
        self.assertEqual(args[0], "general") # Recipient of warning
        expected_warning_text_part = "your recent message contains inappropriate language (e.g., related to 'darn')"
        self.assertIn(expected_warning_text_part, args[1])
        self.assertIn("@user123", args[1])

    def test_process_message_clean(self):
        """Test processing a clean message without offensive keywords."""
        self.moderator.offensive_keywords = ["darn", "heck"]
        clean_message = {
            "sender_username": "user456",
            "recipient_username": "general",
            "text": "This is a perfectly fine message.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.moderator.process_message(clean_message)
        self.moderator.send_message.assert_not_called()

    def test_process_message_from_moderator_bot_itself(self):
        """Test that ModeratorBot does not moderate its own messages."""
        self.moderator.offensive_keywords = ["darn"]
        message_from_bot = {
            "sender_username": self.moderator.ai_username, # Sender is ModeratorBot
            "recipient_username": "general",
            "text": "This is a darn message from the bot itself.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.moderator.process_message(message_from_bot)
        self.moderator.send_message.assert_not_called()

    def test_process_message_from_ai_agent(self):
        """Test that ModeratorBot does not moderate messages from other AI agents."""
        self.moderator.offensive_keywords = ["darn"]
        message_from_ai_agent = {
            "sender_username": "AI_EcoSocialist_Rep", # Sender is an AI agent
            "recipient_username": "general",
            "text": "AI says something darn important.",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.moderator.process_message(message_from_ai_agent)
        self.moderator.send_message.assert_not_called()

    def test_process_message_case_insensitivity(self):
        """Test offensive keyword detection is case-insensitive."""
        self.moderator.offensive_keywords = ["offensive"]
        offensive_message_caps = {
            "sender_username": "user789",
            "recipient_username": "general",
            "text": "This is OFFENSIVE!",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.moderator.process_message(offensive_message_caps)
        self.moderator.send_message.assert_called_once()
        args, _ = self.moderator.send_message.call_args
        self.assertIn("related to 'offensive'", args[1].lower()) # Check for lowercase keyword in warning

if __name__ == '__main__':
    unittest.main()
