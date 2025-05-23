import sqlite3
import os

DATABASE_FILE = os.path.join('data', 'chat.db')

def get_db_connection():
    """Creates a database connection."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_username TEXT NOT NULL,
            recipient_username TEXT NOT NULL, -- "general" for general assembly messages
            text TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    
    # Add an index on messages.timestamp for faster sorting
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# --- User Management Functions ---

def add_user(username, password_hash):
    """Adds a new user to the users table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        print(f"User {username} added successfully.")
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Username {username} already exists.")
        return False
    finally:
        conn.close()

def get_user(username):
    """Retrieves a user by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user # Returns a sqlite3.Row object or None

# --- Message Management Functions ---

def add_message(sender_username, recipient_username, text, timestamp):
    """Adds a new message to the messages table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (sender_username, recipient_username, text, timestamp) VALUES (?, ?, ?, ?)",
            (sender_username, recipient_username, text, timestamp)
        )
        conn.commit()
        # print(f"Message from {sender_username} to {recipient_username} added successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Database error when adding message: {e}")
        return False
    finally:
        conn.close()

def get_messages_for_user(username, limit=50):
    """
    Retrieves messages for a specific user:
    - General messages.
    - Private messages sent by the user.
    - Private messages received by the user.
    Orders by timestamp (most recent first or last, depending on desired display).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages
        WHERE recipient_username = 'general' 
           OR sender_username = ? 
           OR recipient_username = ?
        ORDER BY timestamp ASC 
        LIMIT ?
    ''', (username, username, limit))
    messages = cursor.fetchall() # List of sqlite3.Row objects
    conn.close()
    # Convert sqlite3.Row objects to dictionaries for easier use in templates/json
    return [dict(row) for row in messages]


def get_all_messages(limit=None):
    """Retrieves all messages, optionally limited. Ordered by timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM messages ORDER BY timestamp ASC"
    params = []
    if limit:
        query += " LIMIT ?"
        params.append(limit)
    
    cursor.execute(query, params)
    messages = cursor.fetchall()
    conn.close()
    return [dict(row) for row in messages]


def check_if_moderator_has_spoken(moderator_username="ModeratorBot"):
    """Checks if the moderator has sent any messages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM messages WHERE sender_username = ? LIMIT 1", (moderator_username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


if __name__ == '__main__':
    # This allows running `python app/database.py` to initialize the DB manually
    init_db()
    
    # Example Usage (uncomment to test directly)
    # print("Testing database functions...")
    # add_user("testuser1", "hash1")
    # add_user("testuser2", "hash2")
    # user1 = get_user("testuser1")
    # print(f"User 1: {dict(user1) if user1 else 'Not found'}")

    # from datetime import datetime
    # add_message("testuser1", "general", "Hello general chat!", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # add_message("testuser2", "testuser1", "Hello user1, private message!", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # add_message("ModeratorBot", "general", "Moderator says hi!", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    # print("\nMessages for testuser1:")
    # for msg in get_messages_for_user("testuser1", limit=10):
    #     print(msg)

    # print("\nAll messages:")
    # for msg in get_all_messages(limit=5):
    #     print(msg)
        
    # print(f"\nHas ModeratorBot spoken? {check_if_moderator_has_spoken()}")
    
    # print("\nAttempting to add existing user testuser1:")
    # add_user("testuser1", "hash_new") # Should fail
