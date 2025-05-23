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
│   ├── users.json          # Stores user credentials
│   ├── messages.json       # Stores chat messages
│   └── ai_members.json     # Definitions for AI member agents
├── tests/                  # Unit tests
│   ├── base_test.py        # Base test case with helper methods
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
    (First, ensure `requirements.txt` is created and populated)
    ```bash
    pip install Flask Werkzeug
    ```
    A `requirements.txt` would look like:
    ```
    Flask>=2.0
    Werkzeug>=2.0
    ```

4.  **Run the application:**
    ```bash
    python app/app.py
    ```
    The application will typically be available at `http://127.0.0.1:5000/`.

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

-   `data/users.json`: Stores user information, including hashed passwords.
-   `data/messages.json`: Stores all chat messages with sender, recipient, text, and timestamp.
-   `data/ai_members.json`: Contains definitions for the AI agents that participate in the chat.

**Note:** These files are used as a simple database. For a production application, a proper database system (e.g., PostgreSQL, SQLite, MongoDB) would be used.

## AI Components

-   **ModeratorAI (`app/moderator_ai.py`):** A basic AI that can process messages. Currently, its main function is to send a welcome message.
-   **AIMemberAgent (`app/ai_member_agent.py`):** Represents AI political members who can participate in discussions. They have defined political views and personas and can generate responses based on the conversation.

## Further Development Ideas

-   Implement actual AI logic for ModeratorAI (e.g., content moderation, rule enforcement).
-   Enhance AIMemberAgent response generation (e.g., using LLMs or more sophisticated NLP).
-   Implement WebSocket for real-time chat updates.
-   Add a proper database.
-   Improve UI/UX.
-   Add more comprehensive error handling and input validation.
-   Expand testing coverage.
```
