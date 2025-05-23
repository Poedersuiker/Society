import json
import datetime
import os
# No longer need to import json if not using JSON files directly

class ModeratorAI:
    def __init__(self, username="ModeratorBot", socketio_instance=None, db_module=None):
        self.ai_username = username
        self.rules = {}  # For now, empty
        self.offensive_keywords = ["badword1", "offensive_term2", "example_curse", "hate_speech", "darn", "heck"] # Example offensive keywords
        self.socketio = socketio_instance
        self.db = db_module # Store the database module instance

    def send_message(self, recipient, text): # Removed messages_file argument
        """Allows the AI to send messages to the chat, save to DB, and emit via SocketIO."""
        if not self.db:
            print("ModeratorAI Error: Database module not configured.")
            return

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save message to database
        if self.db.add_message(self.ai_username, recipient, text, timestamp_str):
            print(f"ModeratorAI: Message from {self.ai_username} to {recipient} saved to DB.")
            
            # Construct message object for emitting (consistent with DB structure)
            # It's important that this matches the structure client expects / app.py emits for user messages
            emitted_message = {
                "sender_username": self.ai_username,
                "recipient_username": recipient,
                "text": text,
                "timestamp": timestamp_str
            }

            # No longer directly emits; returns the message dict for the caller to handle emission
            # if self.socketio:
            #     self.socketio.emit('new_message', emitted_message) 
            #     print(f"ModeratorAI: Message emitted via SocketIO to {recipient}: '{text}' (intended for all)")
            # else:
            #     print("ModeratorAI: SocketIO instance not available. Message not emitted.")
            return emitted_message # Return the message dictionary
        else:
            print(f"ModeratorAI: Failed to save message from {self.ai_username} to {recipient} to DB.")
            return None # Return None if saving failed


    def process_message(self, message_dict):
        """
        Analyzes a message for offensive content. 
        If a warning is generated, it's saved via send_message and returned.
        Returns the warning message dictionary or None.
        """
        sender = message_dict.get('sender_username') 
        text_content = message_dict.get('text', '').lower()
        # recipient = message_dict.get('recipient_username') # Not used for warning logic itself

        # Don't moderate own messages or messages from other AI agents
        if sender == self.ai_username or (sender and sender.startswith("AI_")):
            return None

        # print(f"ModeratorAI: Processing message from {sender} to {recipient}: '{message_dict.get('text')}'") # Debugging

        found_offensive_keyword = None
        for keyword in self.offensive_keywords:
            if keyword.lower() in text_content:
                found_offensive_keyword = keyword
                break
        
        if found_offensive_keyword:
            warning_text = (
                f"ModeratorBot: @{sender}, your recent message contains inappropriate language (e.g., related to '{found_offensive_keyword}'). "
                "Please maintain a respectful environment and avoid using offensive terms."
            )
            # Send warning to general chat and get the message dict back
            warning_message_dict = self.send_message("general", warning_text)
            if warning_message_dict:
                print(f"ModeratorAI: Offensive keyword '{found_offensive_keyword}' detected from {sender}. Warning generated and saved.")
                return warning_message_dict # Return the saved warning message
        
        return None # No warning generated

    # Removed _load_messages and _save_messages as they are no longer needed

if __name__ == '__main__':
    # Example Usage (for testing ModeratorAI independently)
    # Note: For direct testing of send_message with SocketIO and DB, 
    # mock socketio and db_module objects would be needed.
    
    # Basic instantiation test
    # moderator = ModeratorAI() 
    # print(f"ModeratorAI initialized with username: {moderator.ai_username}")

    # Example of how process_message might be tested (needs mock db and socketio)
    # class MockDB:
    #     def add_message(self, s, r, t, ts): return True
    # class MockSocketIO:
    #     def emit(self, event, data, broadcast): pass
    
    # moderator_with_mocks = ModeratorAI(socketio_instance=MockSocketIO(), db_module=MockDB())
    # sample_message = {
    #     "sender_username": "user_test", 
    #     "recipient_username": "general", 
    #     "text": "This is a darn test message for the moderator to process.", 
    #     "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # }
    # moderator_with_mocks.process_message(sample_message)
    
    print("ModeratorAI basic structure test complete. For full test, run the Flask app.")
