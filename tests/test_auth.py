import unittest
import os
# import json # No longer needed for users.json
from flask import session

# Ensure the app path is correct for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from app.app import app # app is imported in BaseTestCase
from tests.base_test import BaseTestCase # This already imports app and db


class AuthTestCase(BaseTestCase):

    def test_01_register_new_user(self):
        """Test registration of a new user."""
        response = self.register_user('testuser1', 'password123')
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b'Login', response.data) 

        user = self.get_user_from_db('testuser1')
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser1')

    def test_02_register_existing_user(self):
        """Test registration with an existing username."""
        self.register_user('testuser2', 'password123') # First registration
        user_before_reregister = self.get_user_from_db('testuser2')
        self.assertIsNotNone(user_before_reregister)

        response = self.register_user('testuser2', 'anotherpassword') # Attempt to re-register
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Username already exists', response.data)
        
        # Verify user data in DB hasn't changed (e.g., password hash)
        user_after_reregister = self.get_user_from_db('testuser2')
        self.assertIsNotNone(user_after_reregister)
        self.assertEqual(user_before_reregister['password_hash'], user_after_reregister['password_hash'])
        # Ensure only one user with this username
        # This is implicitly handled by UNIQUE constraint, but can double check count if needed
        # For example, if get_all_users were a helper:
        # all_users_with_name = [u for u in self.get_all_users_from_db() if u['username'] == 'testuser2']
        # self.assertEqual(len(all_users_with_name), 1)

    def test_02a_register_validation_errors(self):
        """Test registration with various validation errors."""
        # Empty username
        response = self.register_user('', 'password123')
        self.assertIn(b'Username is required', response.data)
        
        # Username too short
        response = self.register_user('us', 'password123')
        self.assertIn(b'Username must be between 3 and 20 characters', response.data)

        # Username too long
        response = self.register_user('u' * 21, 'password123')
        self.assertIn(b'Username must be between 3 and 20 characters', response.data)

        # Username invalid characters
        response = self.register_user('user name', 'password123') # space
        self.assertIn(b'Username can only contain letters, numbers, and underscores', response.data)
        response = self.register_user('user!', 'password123') # exclamation
        self.assertIn(b'Username can only contain letters, numbers, and underscores', response.data)

        # Empty password
        response = self.register_user('validuser1', '')
        self.assertIn(b'Password is required', response.data)

        # Password too short
        response = self.register_user('validuser2', 'pass')
        self.assertIn(b'Password must be at least 6 characters long', response.data)
        
        # Check that no users were actually created
        self.assertIsNone(self.get_user_from_db('validuser1'))
        self.assertIsNone(self.get_user_from_db('validuser2'))
        self.assertIsNone(self.get_user_from_db(''))
        self.assertIsNone(self.get_user_from_db('us'))


    def test_03_login_correct_credentials(self):
        """Test login with correct credentials."""
        # Use add_user_directly_to_db for more controlled setup if needed,
        # or rely on self.register_user which uses the app's endpoint.
        self.register_user('testuser3', 'password123') 
        
        response = self.login_user('testuser3', 'password123')
        self.assertEqual(response.status_code, 200) 
        # The chat page content might change, so checking for username in session is more robust
        # self.assertIn(b'Welcome, testuser3!', response.data) 
        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('username'))
            self.assertEqual(sess['username'], 'testuser3')
            # Ensure the response data for chat page contains the username
            # This depends on how chat.html displays it.
            self.assertIn(bytes(f"Welcome, {sess['username']}", 'utf-8'), response.data)

    def test_03a_login_validation_errors(self):
        """Test login with empty fields."""
        # Empty username
        response = self.login_user('', 'password123')
        self.assertIn(b'Username is required', response.data)

        # Empty password
        response = self.login_user('testuser', '')
        self.assertIn(b'Password is required', response.data)


    def test_04_login_incorrect_credentials(self):
        """Test login with incorrect credentials."""
        self.register_user('testuser4', 'password123')
        response = self.login_user('testuser4', 'wrongpassword')
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b'Invalid username or password', response.data)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('username'))

    def test_05_logout(self):
        """Test logout."""
        self.register_user('testuser5', 'password123')
        self.login_user('testuser5', 'password123') 

        with self.client.session_transaction() as sess:
            self.assertTrue(sess.get('username'))

        response = self.logout_user()
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b'Login', response.data)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('username'))

    def test_06_login_required_decorator_unauthenticated(self):
        """Test login_required decorator for unauthenticated user."""
        response = self.client.get('/chat', follow_redirects=False) # Don't follow redirect yet
        self.assertEqual(response.status_code, 302) # Should redirect
        self.assertIn('/login', response.location)

        # Follow the redirect
        response = self.client.get('/chat', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data) # Ends up on login page

    def test_07_login_required_decorator_authenticated(self):
        """Test login_required decorator for authenticated user."""
        self.register_user('testuser7', 'password123')
        self.login_user('testuser7', 'password123')

        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome, testuser7!', response.data)

if __name__ == '__main__':
    unittest.main()
