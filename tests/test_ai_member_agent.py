import unittest
from unittest.mock import MagicMock, patch
import datetime
import random

# Ensure the app path is correct for imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ai_member_agent import AIMemberAgent

class TestAIMemberAgent(unittest.TestCase):

    def setUp(self):
        self.mock_socketio = MagicMock()
        self.mock_db = MagicMock()
        
        self.ai_def_eco = {
            "username": "AI_EcoSocialist_Rep_Test",
            "political_view": "Advocates for strong environmental regulations, green energy, and social ownership of key industries like water and power. Believes in universal basic income.",
            "persona": "Speaks formally, often citing ecological data and social justice principles. Uses terms like 'sustainability', 'equity', 'collective good'."
        }
        self.agent_eco = AIMemberAgent(
            **self.ai_def_eco, 
            socketio_instance=self.mock_socketio, 
            db_module=self.mock_db
        )
        # print(f"Eco Agent keywords: {self.agent_eco.interest_keywords}")


        self.ai_def_hawk = {
            "username": "AI_FiscalHawk_Rep_Test",
            "political_view": "Prioritizes balanced budgets, reduced government spending, and free-market capitalism. Supports deregulation and lower taxes.",
            "persona": "Direct and data-driven, often questions the cost implications of proposals. Emphasizes 'fiscal responsibility', 'economic growth', 'individual liberty'."
        }
        self.agent_hawk = AIMemberAgent(
            **self.ai_def_hawk,
            socketio_instance=self.mock_socketio,
            db_module=self.mock_db
        )
        # print(f"Hawk Agent keywords: {self.agent_hawk.interest_keywords}")


    def test_generate_response_no_messages(self):
        """Test that agent returns None if no messages are provided."""
        response = self.agent_eco.generate_response([])
        self.assertIsNone(response)

    def test_generate_response_ignore_self_moderator_other_ai(self):
        """Test that agent ignores messages from self, ModeratorBot, or other AIs."""
        senders_to_ignore = [self.agent_eco.username, "ModeratorBot", "AI_SomeOtherAgent"]
        for sender in senders_to_ignore:
            messages = [{"sender_username": sender, "text": "Some environmental topic"}]
            response = self.agent_eco.generate_response(messages)
            self.assertIsNone(response, f"Agent should ignore message from {sender}")

    @patch('random.random') # Mock random.random to control speak probability
    def test_generate_response_triggered_by_keywords(self, mock_random_random):
        """Test that agent is more likely to respond when keywords match."""
        # Force agent to speak (random.random() < triggered_speak_probability)
        mock_random_random.return_value = 0.1 # Less than triggered_speak_probability (0.6)
        
        # Keywords for eco agent: 'environmental', 'regulations', 'green', 'energy', 'social', 'ownership'
        # 'sustainability', 'equity', 'collective'
        relevant_message_text = "We need to discuss environmental regulations for sustainability."
        messages = [{"sender_username": "user1", "recipient_username": "general", "text": relevant_message_text}]
        
        response = self.agent_eco.generate_response(messages)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        # Check if response contains some part of its persona or view
        self.assertTrue(any(kw in response.lower() for kw in ["environmental", "regulations", "sustainability", "equity", "collective", "eco", "social", "green"]))
        
        # Check that the print statement for keyword trigger was called (indirectly)
        # This requires capturing stdout or checking logs if using actual print,
        # or mocking print if it's critical to assert. For now, focus on response.

    @patch('random.random')
    def test_generate_response_base_probability_no_keywords(self, mock_random_random):
        """Test agent speaking based on base probability with no keyword match."""
        mock_random_random.return_value = 0.05 # Less than base_speak_probability (0.1)
        
        irrelevant_message_text = "Let's talk about sports."
        messages = [{"sender_username": "user1", "recipient_username": "general", "text": irrelevant_message_text}]
        
        response = self.agent_eco.generate_response(messages)
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

    @patch('random.random')
    def test_generate_response_does_not_speak_if_random_too_high(self, mock_random_random):
        """Test agent does not speak if random number is too high."""
        mock_random_random.return_value = 0.9 # Higher than any speak probability
        
        relevant_message_text = "This is about environmental regulations."
        messages = [{"sender_username": "user1", "recipient_username": "general", "text": relevant_message_text}]
        
        response = self.agent_eco.generate_response(messages)
        self.assertIsNone(response)

    def test_send_message_calls_db_and_socketio(self):
        """Test that send_message correctly calls db.add_message and socketio.emit."""
        self.mock_db.add_message.return_value = True # Simulate successful DB write
        
        recipient = "general"
        text = "Test message from AI agent."
        self.agent_eco.send_message(recipient, text)

        # Check if db.add_message was called correctly
        self.mock_db.add_message.assert_called_once()
        db_args, _ = self.mock_db.add_message.call_args
        self.assertEqual(db_args[0], self.agent_eco.username)
        self.assertEqual(db_args[1], recipient)
        self.assertEqual(db_args[2], text)
        self.assertIsInstance(db_args[3], str) # Timestamp

        # Check if socketio.emit was called correctly
        self.mock_socketio.emit.assert_called_once()
        socket_args, socket_kwargs = self.mock_socketio.emit.call_args
        self.assertEqual(socket_args[0], 'new_message') # Event name
        emitted_message = socket_args[1]
        self.assertEqual(emitted_message['sender_username'], self.agent_eco.username)
        self.assertEqual(emitted_message['recipient_username'], recipient)
        self.assertEqual(emitted_message['text'], text)
        self.assertTrue(socket_kwargs.get('broadcast'))

    def test_send_message_db_failure(self):
        """Test that send_message handles DB failure (no emit)."""
        self.mock_db.add_message.return_value = False # Simulate failed DB write
        
        self.agent_eco.send_message("general", "Another test")
        
        self.mock_db.add_message.assert_called_once()
        self.mock_socketio.emit.assert_not_called() # Should not emit if DB save fails

if __name__ == '__main__':
    unittest.main()
