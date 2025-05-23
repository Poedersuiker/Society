import json
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash # flash is not used yet, but good for future
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from app.moderator_ai import ModeratorAI
from app.ai_member_agent import AIMemberAgent # Added import

app = Flask(__name__)
app.config['TESTING'] = True # Added for testing
app.secret_key = os.urandom(24)

# Initialize Moderator AI
moderator = ModeratorAI()

USERS_FILE = 'data/users.json'
MESSAGES_FILE = 'data/messages.json'
AI_MEMBERS_FILE = 'data/ai_members.json' # Added AI members file

# Initialize AI Member Agents
ai_agents = [] # Global list to hold AI agent instances

def load_ai_member_definitions():
    if not os.path.exists(AI_MEMBERS_FILE):
        print(f"Warning: {AI_MEMBERS_FILE} not found. No AI members will be loaded.")
        return []
    try:
        with open(AI_MEMBERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Error loading or parsing {AI_MEMBERS_FILE}.")
        return []

def initialize_ai_agents():
    global ai_agents
    ai_member_definitions = load_ai_member_definitions()
    for definition in ai_member_definitions:
        try:
            agent = AIMemberAgent(
                username=definition['username'],
                political_view=definition['political_view'],
                persona=definition.get('persona') # Use .get for optional field
            )
            ai_agents.append(agent)
            print(f"Initialized AI Agent: {agent.username}")
        except KeyError as e:
            print(f"Error initializing AI agent from definition {definition}: Missing key {e}")

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
        return []
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_messages():
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)
        return []
    try:
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = next((u for u in users if u['username'] == username), None)

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            # flash('Logged in successfully!', 'success') # Optional: add flash messages
            return redirect(url_for('chat'))
        else:
            # flash('Invalid username or password.', 'danger') # Optional: add flash messages
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if any(u['username'] == username for u in users):
            # flash('Username already exists.', 'danger') # Optional: add flash messages
            return render_template('register.html', error="Username already exists.")

        hashed_password = generate_password_hash(password)
        users.append({'username': username, 'password': hashed_password})
        save_users(users)
        # flash('Registration successful! Please log in.', 'success') # Optional: add flash messages
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    # flash('You have been logged out.', 'info') # Optional: add flash messages
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    current_user = session.get('username')
    all_messages = load_messages()
    user_messages = []
    for msg in all_messages:
        if msg['recipient'] == 'general' or \
           msg['sender'] == current_user or \
           msg['recipient'] == current_user:
            user_messages.append(msg)
    return render_template('chat.html', username=current_user, messages=user_messages)

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    sender = session.get('username')
    message_text = request.form.get('message_text')
    recipient_type = request.form.get('recipient_type') # 'general' or 'private'
    private_recipient_username = request.form.get('private_recipient_username', '').strip()

    if not message_text:
        # Or handle with flash message
        return redirect(url_for('chat'))

    recipient = "general" # Default to general
    if recipient_type == 'private':
        if not private_recipient_username:
            # flash('Private recipient username cannot be empty.', 'danger')
            return redirect(url_for('chat'))
        # Optional: Check if private_recipient_username exists in users.json
        users = load_users()
        if not any(u['username'] == private_recipient_username for u in users):
            # flash(f'User {private_recipient_username} does not exist.', 'danger')
            return redirect(url_for('chat'))
        if private_recipient_username == sender:
            # flash('You cannot send a private message to yourself.', 'danger')
            return redirect(url_for('chat'))
        recipient = private_recipient_username
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = {
        "sender": sender,
        "recipient": recipient,
        "text": message_text,
        "timestamp": timestamp
    }

    messages = load_messages()
    messages.append(new_message)
    save_messages(messages)

    # Let the moderator process the new message
    moderator.process_message(new_message)

    # Let AI Members process the new message and potentially respond
    # Pass all current messages up to this point
    current_messages_for_ai = load_messages() # reload messages to include the latest one
    for agent in ai_agents:
        # AI agents should only respond to messages in 'general' chat for now,
        # and not to themselves or other AIs (basic check in agent.generate_response)
        if new_message['recipient'] == 'general':
            response_text = agent.generate_response(current_messages_for_ai)
            if response_text:
                # AI members send messages to 'general' by default
                agent.send_message("general", response_text, messages_file=MESSAGES_FILE)
    
    return redirect(url_for('chat'))

def send_initial_moderator_message_if_needed():
    messages = load_messages()
    # Check if moderator has sent any message before, or if messages.json is empty
    # A more robust check could be for a specific type of welcome message.
    moderator_has_spoken = any(msg['sender'] == moderator.ai_username for msg in messages)
    
    if not moderator_has_spoken:
        welcome_text = (
            "ModeratorBot is now active. This General Assembly starts with no predefined laws or voting systems. "
            "These must be established through discussion and agreement. "
            "All messages are public in 'General Assembly' unless sent as a 'Private Message' to a specific user."
        )
        moderator.send_message("general", welcome_text, messages_file=MESSAGES_FILE)
        print("ModeratorAI: Initial welcome message sent.")


if __name__ == '__main__':
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    # Ensure users.json and messages.json exist
    load_users() 
    load_messages() # This will create messages.json if it doesn't exist

    # Send initial moderator message
    send_initial_moderator_message_if_needed()

    # Initialize AI Member Agents
    initialize_ai_agents() # Added call

    app.run(debug=True)
