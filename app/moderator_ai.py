import json
import datetime
import os

class ModeratorAI:
    def __init__(self, username="ModeratorBot"):
        self.ai_username = username
        self.rules = {}  # For now, empty
        self.MESSAGES_FILE = 'data/messages.json' # Default, can be overridden

    def send_message(self, recipient, text, messages_file=None):
        """Allows the AI to send messages to the chat."""
        if messages_file is None:
            messages_file = self.MESSAGES_FILE
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_message = {
            "sender": self.ai_username,
            "recipient": recipient,
            "text": text,
            "timestamp": timestamp
        }

        messages = self._load_messages(messages_file)
        messages.append(new_message)
        self._save_messages(messages, messages_file)
        print(f"ModeratorAI: Message sent to {recipient}: '{text}'")

    def process_message(self, message_dict):
        """Analyzes a message and reacts. Placeholder for now."""
        # For now, just prints the message to the console
        print(f"ModeratorAI: Processing message from {message_dict['sender']} to {message_dict['recipient']}: '{message_dict['text']}'")
        # Future logic will go here, e.g., rule checking, responding, etc.

    def _load_messages(self, messages_file):
        if not os.path.exists(messages_file):
            with open(messages_file, 'w') as f:
                json.dump([], f)
            return []
        try:
            with open(messages_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_messages(self, messages, messages_file):
        with open(messages_file, 'w') as f:
            json.dump(messages, f, indent=4)

if __name__ == '__main__':
    # Example Usage (for testing ModeratorAI independently)
    moderator = ModeratorAI()
    
    # Test sending a message
    # moderator.send_message("general", "Hello everyone! This is ModeratorBot.")
    # moderator.send_message("user123", "This is a private test message to user123.")

    # Test processing a message
    sample_message = {
        "sender": "user_test", 
        "recipient": "general", 
        "text": "This is a test message for the moderator to process.", 
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # moderator.process_message(sample_message)
    
    print("ModeratorAI basic test complete. Check data/messages.json if you ran send_message.")
