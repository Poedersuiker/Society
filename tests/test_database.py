import unittest
import os
import sqlite3 # For IntegrityError
import datetime

# Ensure the app path is correct for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app.database as db
from app.database import DATABASE_FILE as TEST_DATABASE_FILE # Use the actual path or override
from werkzeug.security import generate_password_hash


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Set up for all tests in the class """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(TEST_DATABASE_FILE), exist_ok=True)
        # Ensure a clean database for this test suite
        if os.path.exists(TEST_DATABASE_FILE):
            os.remove(TEST_DATABASE_FILE)
        db.init_db()

    @classmethod
    def tearDownClass(cls):
        """ Clean up after all tests in the class """
        # Remove the test database file after all tests in this class run
        # if os.path.exists(TEST_DATABASE_FILE):
        #     os.remove(TEST_DATABASE_FILE)
        pass # Keep DB for inspection if needed, or clean up

    def setUp(self):
        """ Clear data from tables before each test method """
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM users")
        # Reset autoincrement counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='messages'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        conn.commit()
        conn.close()

        # Add some common users
        self.user1_hash = generate_password_hash("pass1")
        self.user2_hash = generate_password_hash("pass2")
        self.user3_hash = generate_password_hash("pass3")
        db.add_user("user1", self.user1_hash)
        db.add_user("user2", self.user2_hash)
        db.add_user("user3", self.user3_hash)

    def test_add_user_unique_constraint(self):
        """Test unique constraint on usernames."""
        with self.assertRaises(sqlite3.IntegrityError):
            # This call should fail because db.add_user wraps the execute in a try-except
            # that prints and returns False. To test the constraint directly, we'd need to
            # call cursor.execute without the try-except.
            # Instead, we test the behavior of our add_user function.
            conn = db.get_db_connection()
            cursor = conn.cursor()
            # Directly try to insert a duplicate to ensure the DB constraint itself works
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("user1", "newhash"))
            conn.commit() # This line should not be reached if IntegrityError is raised by execute
            # The above direct execute will raise IntegrityError.
            # Testing our function's handling:
            self.assertFalse(db.add_user("user1", "another_hash"))


    def test_get_user(self):
        """Test retrieving a user."""
        user = db.get_user("user1")
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "user1")
        self.assertEqual(user['password_hash'], self.user1_hash)

        non_existent_user = db.get_user("nonexistent")
        self.assertIsNone(non_existent_user)

    def test_add_message(self):
        """Test adding a message."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = db.add_message("user1", "general", "Hello world!", timestamp)
        self.assertTrue(res)
        
        messages = db.get_all_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['sender_username'], "user1")
        self.assertEqual(messages[0]['text'], "Hello world!")

    def test_get_messages_for_user(self):
        """Test get_messages_for_user logic thoroughly."""
        now = datetime.datetime.now()
        ts = [ (now + datetime.timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(5)]

        # 1. General message from user1
        db.add_message("user1", "general", "User1 general msg", ts[0])
        # 2. Private message from user1 to user2
        db.add_message("user1", "user2", "User1 to User2 private", ts[1])
        # 3. Private message from user2 to user1
        db.add_message("user2", "user1", "User2 to User1 private", ts[2])
        # 4. General message from user3
        db.add_message("user3", "general", "User3 general msg", ts[3])
        # 5. Private message from user2 to user3 (user1 should not see this)
        db.add_message("user2", "user3", "User2 to User3 private", ts[4])

        # Test for user1
        user1_messages = db.get_messages_for_user("user1", limit=10)
        self.assertEqual(len(user1_messages), 4) # General msg from user1, PM from user1 to user2, PM from user2 to user1, General msg from user3
        
        texts_for_user1 = [m['text'] for m in user1_messages]
        self.assertIn("User1 general msg", texts_for_user1)
        self.assertIn("User1 to User2 private", texts_for_user1) # Sent by user1
        self.assertIn("User2 to User1 private", texts_for_user1) # Received by user1
        self.assertIn("User3 general msg", texts_for_user1)
        self.assertNotIn("User2 to User3 private", texts_for_user1) # Should not be visible

        # Test for user2
        user2_messages = db.get_messages_for_user("user2", limit=10)
        self.assertEqual(len(user2_messages), 5) # Both general, PM from user1, PM to user1, PM to user3
        texts_for_user2 = [m['text'] for m in user2_messages]
        self.assertIn("User1 general msg", texts_for_user2)
        self.assertIn("User3 general msg", texts_for_user2)
        self.assertIn("User1 to User2 private", texts_for_user2) # Received by user2
        self.assertIn("User2 to User1 private", texts_for_user2) # Sent by user2
        self.assertIn("User2 to User3 private", texts_for_user2) # Sent by user2

        # Test for user3
        user3_messages = db.get_messages_for_user("user3", limit=10)
        self.assertEqual(len(user3_messages), 3) # General from user1, General from user3, PM from user2 to user3
        texts_for_user3 = [m['text'] for m in user3_messages]
        self.assertIn("User1 general msg", texts_for_user3)
        self.assertIn("User3 general msg", texts_for_user3) # Sent by user3
        self.assertIn("User2 to User3 private", texts_for_user3) # Received by user3
        self.assertNotIn("User1 to User2 private", texts_for_user3)
        self.assertNotIn("User2 to User1 private", texts_for_user3)


    def test_get_all_messages_ordering_and_limit(self):
        """Test get_all_messages ordering and limit."""
        now = datetime.datetime.now()
        db.add_message("user1", "general", "Msg1", (now + datetime.timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"))
        db.add_message("user2", "general", "Msg2", (now + datetime.timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S"))
        db.add_message("user1", "general", "Msg0", now.strftime("%Y-%m-%d %H:%M:%S")) # Earliest

        all_messages = db.get_all_messages()
        self.assertEqual(len(all_messages), 3)
        self.assertEqual(all_messages[0]['text'], "Msg0")
        self.assertEqual(all_messages[1]['text'], "Msg1")
        self.assertEqual(all_messages[2]['text'], "Msg2")

        limited_messages = db.get_all_messages(limit=2)
        self.assertEqual(len(limited_messages), 2)
        self.assertEqual(limited_messages[0]['text'], "Msg0")
        self.assertEqual(limited_messages[1]['text'], "Msg1")

    def test_check_if_moderator_has_spoken(self):
        """Test checking if moderator has spoken."""
        self.assertFalse(db.check_if_moderator_has_spoken("ModeratorTest"))
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.add_message("ModeratorTest", "general", "I have spoken.", timestamp)
        self.assertTrue(db.check_if_moderator_has_spoken("ModeratorTest"))
        self.assertFalse(db.check_if_moderator_has_spoken("AnotherModerator"))


if __name__ == '__main__':
    unittest.main()
