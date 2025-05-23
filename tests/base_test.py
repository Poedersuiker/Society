import unittest
import os
import json
# Ensure the app path is correct for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app, USERS_FILE, MESSAGES_FILE, AI_MEMBERS_FILE

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and initialize data files."""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for simpler form testing
        self.client = self.app.test_client()

        # Define test-specific data file paths if you want to isolate them
        # For now, we'll use the actual data files but clear them.
        self.users_file = USERS_FILE
        self.messages_file = MESSAGES_FILE
        self.ai_members_file = AI_MEMBERS_FILE # Though not directly manipulated in many tests

        self.clear_data_files()
        self.initialize_data_files()


    def tearDown(self):
        """Clear data files after each test."""
        self.clear_data_files()
        self.initialize_data_files() # Re-initialize for a clean state for the next test, if any

    def clear_data_files(self):
        """Clear users and messages JSON files."""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump([], f)
        if os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump([], f)
        # Optionally clear AI members if tests modify them, though current tests primarily read
        # if os.path.exists(self.ai_members_file) and some_condition:
        #     with open(self.ai_members_file, 'w') as f:
        #         json.dump([], f)


    def initialize_data_files(self):
        """Initialize data files with empty lists if they don't exist."""
        if not os.path.exists('data'):
            os.makedirs('data')
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump([], f)
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, 'w') as f:
                json.dump([], f)
        # Ensure AI members file exists with some default if needed by app startup
        if not os.path.exists(self.ai_members_file):
             with open(self.ai_members_file, 'w') as f:
                json.dump([
                    {
                        "username": "AI_EcoSocialist_Rep_Test",
                        "political_view": "Test Eco View",
                        "persona": "Test Eco Persona"
                    },
                    {
                        "username": "AI_FiscalHawk_Rep_Test",
                        "political_view": "Test Fiscal View",
                        "persona": "Test Fiscal Persona"
                    }
                ], f)


    def register_user(self, username, password):
        """Helper function to register a user."""
        return self.client.post('/register', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def login_user(self, username, password):
        """Helper function to log in a user."""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout_user(self):
        """Helper function to log out a user."""
        return self.client.get('/logout', follow_redirects=True)

    def send_message(self, message_text, recipient_type="general", private_recipient_username=""):
        """Helper function to send a message."""
        return self.client.post('/send_message', data=dict(
            message_text=message_text,
            recipient_type=recipient_type,
            private_recipient_username=private_recipient_username
        ), follow_redirects=True)

    def get_users(self):
        if not os.path.exists(self.users_file):
            return []
        with open(self.users_file, 'r') as f:
            return json.load(f)

    def get_messages(self):
        if not os.path.exists(self.messages_file):
            return []
        with open(self.messages_file, 'r') as f:
            return json.load(f)

if __name__ == '__main__':
    unittest.main()
