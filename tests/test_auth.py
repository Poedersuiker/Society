import unittest
import os
import json
from flask import session

# Ensure the app path is correct for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app, USERS_FILE
from tests.base_test import BaseTestCase


class AuthTestCase(BaseTestCase):

    def test_01_register_new_user(self):
        """Test registration of a new user."""
        response = self.register_user('testuser1', 'password123')
        self.assertEqual(response.status_code, 200) # Should redirect to login, which is 200
        self.assertIn(b'Login', response.data) # Check if it's the login page

        users = self.get_users()
        self.assertTrue(any(u['username'] == 'testuser1' for u in users))

    def test_02_register_existing_user(self):
        """Test registration with an existing username."""
        self.register_user('testuser2', 'password123') # First registration
        response = self.register_user('testuser2', 'anotherpassword') # Attempt to re-register
        self.assertEqual(response.status_code, 200)
        # Check for error message (or appropriate behavior)
        self.assertIn(b'Username already exists', response.data)
        
        users = self.get_users()
        # Count occurrences of 'testuser2'
        count = sum(1 for u in users if u['username'] == 'testuser2')
        self.assertEqual(count, 1, "Username should only exist once.")


    def test_03_login_correct_credentials(self):
        """Test login with correct credentials."""
        self.register_user('testuser3', 'password123')
        response = self.login_user('testuser3', 'password123')
        self.assertEqual(response.status_code, 200) # Redirects to chat
        self.assertIn(b'Welcome, testuser3!', response.data) # Check if it's the chat page

        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get('username'))
            self.assertEqual(sess['username'], 'testuser3')

    def test_04_login_incorrect_credentials(self):
        """Test login with incorrect credentials."""
        self.register_user('testuser4', 'password123')
        response = self.login_user('testuser4', 'wrongpassword')
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'Invalid username or password', response.data)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('username'))

    def test_05_logout(self):
        """Test logout."""
        self.register_user('testuser5', 'password123')
        self.login_user('testuser5', 'password123') # Log in first

        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get('username'))

        response = self.logout_user()
        self.assertEqual(response.status_code, 200) # Redirects to login
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
