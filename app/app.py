import json
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import re # For input validation
from flask_socketio import SocketIO, emit, disconnect
from app.moderator_ai import ModeratorAI
from app.ai_member_agent import AIMemberAgent
import app.database as db 
import sqlite3 # For catching database errors

app = Flask(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize SocketIO
socketio = SocketIO(app, async_mode='eventlet')

# Initialize Moderator AI
# Pass socketio instance, and database module for message saving
moderator = ModeratorAI(socketio_instance=socketio, db_module=db)

# AI Member Definitions (still from JSON for this iteration, but they will use DB for sending messages)
AI_MEMBERS_FILE = 'data/ai_members.json'
ai_agents = [] # Global list to hold AI agent instances

def load_ai_member_definitions():
    # This part remains the same as AI definitions are not in the primary DB
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
            # Pass socketio instance and db_module to AIMemberAgent
            agent = AIMemberAgent(
                username=definition['username'],
                political_view=definition['political_view'],
                persona=definition.get('persona'),
                socketio_instance=socketio,
                db_module=db
            )
            ai_agents.append(agent)
            print(f"Initialized AI Agent: {agent.username}")
        except KeyError as e:
            print(f"Error initializing AI agent from definition {definition}: Missing key {e}")

# Removed load_users, save_users, load_messages, save_messages as they are replaced by db functions

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
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username:
            return render_template('login.html', error="Username is required.")
        if not password:
            return render_template('login.html', error="Password is required.")

        user_data = db.get_user(username) 

        if user_data and check_password_hash(user_data['password_hash'], password):
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Username validation
        if not username:
            return render_template('register.html', error="Username is required.")
        if not (3 <= len(username) <= 20):
            return render_template('register.html', error="Username must be between 3 and 20 characters.")
        if not re.match(r"^\w+$", username): # Alphanumeric plus underscore
             return render_template('register.html', error="Username can only contain letters, numbers, and underscores.")
        
        # Password validation
        if not password:
            return render_template('register.html', error="Password is required.")
        if len(password) < 6:
            return render_template('register.html', error="Password must be at least 6 characters long.")

        if db.get_user(username): 
            return render_template('register.html', error="Username already exists.")

        hashed_password = generate_password_hash(password)
        try:
            if db.add_user(username, hashed_password):
                # flash('Registration successful! Please log in.', 'success') # Consider using flash for redirect
                return redirect(url_for('login'))
            else: # Should be caught by IntegrityError in db.add_user if username is unique
                return render_template('register.html', error="Registration failed. Username might be taken or other issue.")
        except sqlite3.Error as e:
            print(f"Database error during registration: {e}")
            return render_template('register.html', error="A database error occurred. Please try again later.")
            
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
    # Load messages from DB for the current user
    # Timestamps from DB are strings; they might need conversion if complex manipulation is needed,
    # but for display, string format is often fine. sqlite3.Row objects converted to dicts in db.py.
    user_messages = db.get_messages_for_user(current_user, limit=100) # Load more messages initially
    return render_template('chat.html', username=current_user, messages=user_messages)

# The old /send_message POST route is removed as its logic is moved to SocketIO handler.

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    # Optionally, emit something to the connected client, like a welcome or session ID.
    # emit('connection_ack', {'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('send_chat_message')
def handle_send_chat_message(data):
    if 'username' not in session:
        emit('message_error', {'message': 'Authentication required. Please log in.'}, room=request.sid)
        disconnect() # Optionally disconnect unauthenticated user trying to send messages
        return

    sender = session['username']
    message_text = data.get('message_text', '').strip()
    recipient_type = data.get('recipient_type', 'general')
    private_recipient_username = data.get('private_recipient_username', '').strip()

    # Message text validation
    if not message_text:
        emit('message_validation_error', {'field': 'message_text', 'message': 'Message text cannot be empty.'}, room=request.sid)
        return
    if len(message_text) > 5000: # Max length
        emit('message_validation_error', {'field': 'message_text', 'message': 'Message is too long (max 5000 characters).'}, room=request.sid)
        return

    # Recipient type validation
    if recipient_type not in ['general', 'private']:
        emit('message_validation_error', {'field': 'recipient_type', 'message': 'Invalid recipient type.'}, room=request.sid)
        return

    recipient = "general"
    if recipient_type == 'private':
        if not private_recipient_username:
            emit('message_validation_error', {'field': 'private_recipient_username', 'message': 'Private recipient username cannot be empty.'}, room=request.sid)
            return
        if private_recipient_username == sender:
            emit('message_validation_error', {'field': 'private_recipient_username', 'message': 'You cannot send a private message to yourself.'}, room=request.sid)
            return
        if not db.get_user(private_recipient_username):
            emit('message_validation_error', {'field': 'private_recipient_username', 'message': f'User "{private_recipient_username}" does not exist.'}, room=request.sid)
            return
        recipient = private_recipient_username
    
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        if db.add_message(sender, recipient, message_text, timestamp_str):
            emitted_message = {
                "sender_username": sender,
                "recipient_username": recipient,
                "text": message_text,
                "timestamp": timestamp_str
            }
            socketio.emit('new_message', emitted_message, broadcast=True)
            # print(f"Message from {sender} to {recipient} saved and emitted.")

            moderator.process_message(emitted_message)
            
            all_current_messages = db.get_all_messages() 
            for agent in ai_agents:
                if emitted_message['recipient_username'] == 'general' or emitted_message['recipient_username'] == agent.username:
                    response_text = agent.generate_response(all_current_messages)
                    if response_text:
                        response_recipient = "general"
                        if emitted_message['recipient_username'] == agent.username:
                            response_recipient = sender
                        agent.send_message(response_recipient, response_text)
        else:
            # This case might be rare if db.add_message itself raises exceptions for failures
            print(f"Failed to save message from {sender} to {recipient} (db.add_message returned False).")
            emit('message_error', {'message': 'Failed to save message due to an unknown database issue.'}, room=request.sid)
    except sqlite3.Error as e:
        print(f"Database error when sending message: {e}")
        emit('message_error', {'message': 'A database error occurred while sending your message.'}, room=request.sid)
    except Exception as e: # Catch any other unexpected errors
        print(f"Unexpected error when sending message: {e}")
        emit('message_error', {'message': 'An unexpected server error occurred.'}, room=request.sid)


def send_initial_moderator_message_if_needed():
    # Check DB if moderator has spoken
    if not db.check_if_moderator_has_spoken(moderator.ai_username):
        welcome_text = (
            "ModeratorBot is now active. Basic content moderation for offensive language is in effect. "
            "This General Assembly starts with no predefined laws or voting systems. "
            "These must be established through discussion and agreement. "
            "All messages are public in 'General Assembly' unless sent as a 'Private Message' to a specific user."
        )
        # Moderator's send_message method will use db.add_message and socketio.emit
        moderator.send_message("general", welcome_text) # Removed messages_file arg
        print("ModeratorAI: Initial welcome message sent using DB.")


if __name__ == '__main__':
    db.init_db() # Initialize database

    # Ensure AI agents and moderator have socketio and db instances correctly set
    # This is important if they were initialized before main block or if app is structured differently
    if moderator.socketio is None: moderator.socketio = socketio
    if moderator.db is None: moderator.db = db # Ensure db module is passed
    
    for agent in ai_agents:
        if agent.socketio is None: agent.socketio = socketio
        if agent.db is None: agent.db = db # Ensure db module is passed to each agent

    initialize_ai_agents() # AI agents are initialized here, now with db module passed
    send_initial_moderator_message_if_needed()

    print("Starting Flask-SocketIO server...")
    socketio.run(app, debug=True, use_reloader=False)
