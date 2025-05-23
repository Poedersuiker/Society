import json
import datetime
import os
import google.generativeai as genai # Added for Gemini

# No longer need to import json if not using JSON files directly

class ModeratorAI:
    def __init__(self, db_module, api_key=None, socketio_instance=None, username="ModeratorBot"): # Added api_key, ensure other params like db_module are there
        self.db = db_module
        self.ai_username = username
        self.rules = {}  # For now, empty
        self.offensive_keywords = ["badword1", "offensive_term2", "example_curse", "hate_speech", "darn", "heck"] # Keep for fallback
        self.socketio = socketio_instance # Still here, though send_message doesn't use it directly
        self.api_key = api_key
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel('gemini-pro')
                print("ModeratorAI: Gemini model initialized successfully.")
            except Exception as e:
                print(f"ModeratorAI: Error initializing Gemini model: {e}")
                self.model = None
        else:
            print("ModeratorAI: No API key provided. AI moderation will use keyword fallback.")


    def send_message(self, recipient, text): 
        """Saves AI message to DB and returns message dictionary for emission."""
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
        original_text = message_dict.get('text', '')

        # Don't moderate own messages or messages from other AI agents
        if sender == self.ai_username or (sender and sender.startswith("AI_")):
            return None

        if self.model:
            prompt = f'''You are an AI moderator for a parliamentary assembly chat. Your primary goal is to maintain respectful discourse and enforce chat rules.
Rules:
1. Messages must not contain offensive language or hate speech.
2. Messages must not contain personal attacks (ad hominem attacks).
3. Discussion should remain respectful; avoid excessive sarcasm or language that derails productive conversation.

Analyze the following message from user '{sender}':
Message: "{original_text}"

Does this message violate any of the above rules? 
Respond strictly in the format: "Violation: Yes/No. Reason: [Provide a very brief reason if Yes, or 'None' if No]."'''
            
            try:
                response = self.model.generate_content(prompt)
                # Ensure response and response.text are not None before stripping
                response_text = response.text.strip() if response and hasattr(response, 'text') and response.text else "Violation: No. Reason: Error processing AI response."
            except Exception as e:
                print(f"ModeratorAI: Error calling Gemini API: {e}")
                response_text = "Violation: No. Reason: Error calling AI." # Fallback response

            # Parse Gemini's response
            if response_text.startswith("Violation: Yes"):
                reason_start = response_text.find("Reason:")
                reason = response_text[reason_start + len("Reason:"):].strip() if reason_start != -1 else "Violated assembly rules."
                warning_text = f"ModeratorBot: @{sender}, your message has been flagged for review. Reason: {reason} (AI Assessment)"
                return self.send_message("general", warning_text) # send_message returns the dict
            
            return None # No violation detected by Gemini
        else:
            # Fallback to keyword-based moderation
            text_lower = original_text.lower()
            for keyword in self.offensive_keywords:
                if keyword in text_lower:
                    warning_text = f"ModeratorBot: @{sender}, your message contains potentially inappropriate language ('{keyword}'). Please maintain a respectful environment. (Keyword fallback)"
                    return self.send_message("general", warning_text)
            return None

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
