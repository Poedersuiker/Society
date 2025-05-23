import unittest
import os
import json # Still needed for AI members file
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app, socketio # Import socketio for potential direct handler calls
import app.database as db
from app.database import DATABASE_FILE as TEST_DATABASE_FILE # Use the same DB file path for consistency or override
from werkzeug.security import generate_password_hash # For adding users directly if needed

# Override DATABASE_FILE for testing to use an in-memory or specific test file
# For simplicity here, we might let it create the default 'data/chat.db' and clear it.
# Or, better for isolation, use a dedicated test DB file or in-memory.
# Let's assume for now we will use the default and ensure it's clean.
# If using a separate test DB file:
# TEST_DATABASE_FILE = os.path.join('data', 'test_chat.db')
# db.DATABASE_FILE = TEST_DATABASE_FILE # Monkey patch for testing

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Set up for all tests in the class """
        # Ensure data directory exists
        os.makedirs(os.path.dirname(TEST_DATABASE_FILE), exist_ok=True)
        # If using a specific test DB file, ensure it's clean before starting tests
        if os.path.exists(TEST_DATABASE_FILE):
            os.remove(TEST_DATABASE_FILE)
        db.init_db() # Initialize the database schema for all tests

    @classmethod
    def tearDownClass(cls):
        """ Clean up after all tests in the class """
        # If using a specific test DB file, remove it after tests
        # if os.path.exists(TEST_DATABASE_FILE) and TEST_DATABASE_FILE != db.DATABASE_FILE:
        #     os.remove(TEST_DATABASE_FILE)
        pass # DB is initialized once and tables cleared per test method

    def setUp(self):
        """Set up test client and initialize database before each test."""
        self.app_context = app.app_context()
        self.app_context.push() # Push an application context

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        # Use a separate test database or ensure the main one is clean
        # db.DATABASE_FILE = TEST_DATABASE_FILE # Ensure db module uses test DB
        self.client = app.test_client()
        
        # AI Members file still used from JSON
        self.ai_members_file = os.path.join('data', 'ai_members.json') # app.AI_MEMBERS_FILE
        self._ensure_ai_members_file()

        self.clear_db_tables()


    def tearDown(self):
        """Clear database tables after each test."""
        self.clear_db_tables()
        self.app_context.pop()


    def clear_db_tables(self):
        """Clear all rows from users and messages tables."""
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM users")
        # Reset autoincrement counters if needed (SQLite specific)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='messages'")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        conn.commit()
        conn.close()

    def _ensure_ai_members_file(self):
        """Ensure AI members JSON file exists with some default content."""
        if not os.path.exists(self.ai_members_file):
            os.makedirs(os.path.dirname(self.ai_members_file), exist_ok=True)
            with open(self.ai_members_file, 'w') as f:
                json.dump([
                    {
                        "username": "AI_EcoSocialist_Rep_Test",
                        "political_view": "Test Eco View", "persona": "Test Eco Persona"
                    },
                    {
                        "username": "AI_FiscalHawk_Rep_Test",
                        "political_view": "Test Fiscal View", "persona": "Test Fiscal Persona"
                    }
                ], f)

    def register_user(self, username, password):
        """Helper function to register a user via HTTP POST."""
        return self.client.post('/register', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def login_user(self, username, password):
        """Helper function to log in a user via HTTP POST."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout_user(self):
        """Helper function to log out a user via HTTP GET."""
        return self.client.get('/logout', follow_redirects=True)

    # send_message helper is removed as it's now a SocketIO event.
    # Tests needing to send messages will either:
    # 1. Call the server-side handler directly (if appropriate for the test).
    # 2. Use a SocketIO test client (more complex, for later if needed).
    # 3. Check DB state after actions that indirectly cause messages.

    def get_user_from_db(self, username):
        """Helper to get a user directly from the database."""
        user_row = db.get_user(username)
        return dict(user_row) if user_row else None

    def get_messages_from_db(self, username=None, limit=100):
        """Helper to get messages directly from the database."""
        if username:
            return db.get_messages_for_user(username, limit=limit)
        return db.get_all_messages(limit=limit)
    
    def add_user_directly_to_db(self, username, password):
        """Adds a user directly to the DB for test setup."""
        hashed_password = generate_password_hash(password)
        db.add_user(username, hashed_password)


if __name__ == '__main__':
    unittest.main()
