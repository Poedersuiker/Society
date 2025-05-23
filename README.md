# Flask Chat Application

This is a simple web-based chat application built with Flask.

## Features

- User registration and login
- General (public) chat messages
- Private messages between users
- Moderator AI (basic placeholder)
- AI Member Agents (basic placeholder political representatives)

## Project Structure

```
.
├── app/                    # Main application package
│   ├── __init__.py         # (Can be empty if app.py is the main module)
│   ├── app.py              # Flask application, routes, and core logic
│   ├── moderator_ai.py     # ModeratorAI class
│   ├── ai_member_agent.py  # AIMemberAgent class
│   ├── static/             # Static files (CSS, JS, images)
│   │   └── style.css
│   └── templates/          # HTML templates
│       ├── chat.html
│       ├── login.html
│       └── register.html
├── data/                   # Data files (simulating a database)
│   ├── chat.db             # SQLite database file
│   └── ai_members.json     # Definitions for AI member agents
├── tests/                  # Unit tests
│   ├── base_test.py        # Base test case with helper methods
│   ├── test_ai_member_agent.py # Tests for AIMemberAgent
│   ├── test_database.py    # Tests for database functions
│   ├── test_moderator_ai.py # Tests for ModeratorAI
│   ├── test_auth.py        # Authentication tests
│   └── test_chat.py        # Chat functionality tests
├── venv/                   # Virtual environment (optional, if used)
├── requirements.txt        # Python dependencies (to be created)
└── README.md               # This file
```

## Setup and Running

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    (First, ensure `requirements.txt` is created and populated. See below for a more complete list)
    ```bash
    pip install -r requirements.txt
    ```
    A `requirements.txt` should include:
    ```
    Flask>=2.0
    Werkzeug==2.3.7 # Pinned for Flask-SocketIO compatibility
    Flask-SocketIO>=5.0
    eventlet # For SocketIO async mode
    # Add other dependencies as needed
    ```

4.  **Initialize the Database (if not already done):**
    The application will attempt to initialize the database on first run. Alternatively, you can initialize it manually from the project root:
    ```bash
    python -m app.database 
    ```

5.  **Run the application:**
    To run the chat application, navigate to the project root directory (`Society/`) in your terminal and execute the following command:
    ```bash
    python -m app.app
    ```
    This method runs the application as a Python module and correctly handles the package structure, preventing import errors. The application will typically be available at `http://127.0.0.1:5000/` in your web browser.


## Running Tests

To run the automated tests:

1.  Ensure you are in the project's root directory.
2.  Make sure your virtual environment is activated (if you are using one).
3.  Run the following command:

    ```bash
    python -m unittest discover -s tests
    ```

    This command will discover and run all test files (named `test_*.py`) in the `tests` directory.

## Data Files

-   `data/chat.db`: An SQLite database file that stores user credentials and chat messages.
-   `data/ai_members.json`: Contains definitions for the AI agents that participate in the chat.

## AI Components

-   **ModeratorAI (`app/moderator_ai.py`):** A basic AI that can process messages. Currently, its main function is to send a welcome message.
-   **AIMemberAgent (`app/ai_member_agent.py`):** Represents AI political members who can participate in discussions. They have defined political views and personas and can generate responses based on the conversation.

## Further Development Ideas

-   Implement actual AI logic for ModeratorAI (e.g., content moderation, rule enforcement).
-   Enhance AIMemberAgent response generation (e.g., using LLMs or more sophisticated NLP).
-   Use WebSockets for real-time chat updates (Flask-SocketIO).
-   Uses an SQLite database for data persistence.
-   Features improved UI/UX and styling.
-   Includes comprehensive server-side and client-side input validation and error handling.
-   Has expanded testing coverage for various components.
```
