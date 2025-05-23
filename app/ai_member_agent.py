import json
import datetime
import os
import random
import google.generativeai as genai # Added for Gemini
import re # For potential use in cleaning responses, though not explicitly in prompt

# No longer need to import json or os if not using JSON files directly

class AIMemberAgent:
    def __init__(self, username, political_view, persona, db_module, api_key=None, socketio_instance=None): # Added api_key
        self.username = username
        self.political_view = political_view
        self.persona = persona # Persona is now expected to be provided
        self.socketio = socketio_instance
        self.db = db_module 
        self.api_key = api_key
        self.model = None

        # Removed old keyword logic and speak probabilities as Gemini will handle response generation.
        # self.base_speak_probability = 0.1 
        # self.triggered_speak_probability = 0.6
        # self.common_stopwords = set([...]) # No longer needed for this agent's core logic
        # self.interest_keywords = self._extract_interest_keywords() # No longer needed

        if self.api_key:
            # Ensure genai is configured.
            try:
                # Attempt to get a model to see if API key is already configured and valid.
                # This is a simple check; a more robust one might involve listing models.
                genai.get_model('gemini-pro') 
            except Exception: # Broad exception if not configured or key is invalid
                try:
                    print(f"AIMemberAgent ({self.username}): Attempting to configure Gemini.")
                    genai.configure(api_key=self.api_key)
                except Exception as e:
                    print(f"AIMemberAgent ({self.username}): Error configuring Gemini with API key: {e}")
                    self.api_key = None # Nullify API key if configuration fails

            if self.api_key: # Re-check API key status after potential configuration attempt
                try:
                    self.model = genai.GenerativeModel('gemini-pro')
                    print(f"AIMemberAgent ({self.username}): Gemini model initialized successfully.")
                except Exception as e:
                    print(f"AIMemberAgent ({self.username}): Error initializing Gemini model: {e}")
                    self.model = None
        else:
            print(f"AIMemberAgent ({self.username}): No API key provided. AI responses will be disabled for this agent.")

    # Removed _extract_interest_keywords and _extract_message_keywords as they are part of the old logic

    def generate_response(self, all_messages):
        if not self.model: # If Gemini model is not available, agent does not respond
            print(f"AIMemberAgent ({self.username}): No model available, cannot generate response.")
            return None

        history_limit = 5
        # Filter out messages from this agent itself and also ModeratorBot from history to Gemini
        recent_messages = [
            msg for msg in all_messages 
            if msg['sender_username'] != self.username and msg['sender_username'] != "ModeratorBot"
        ][-history_limit:]
        
        formatted_chat_history = "\n".join([f"{msg['sender_username']}: {msg['text']}" for msg in recent_messages])
        if not recent_messages: # Check if list is empty
            formatted_chat_history = "No recent messages relevant for you to respond to. You can make an opening statement if relevant to your views, or introduce a new topic according to your political agenda."

        prompt = f'''You are an AI Member of a parliamentary assembly simulation.
Your Name: {self.username}
Your Political View: {self.political_view}
Your Persona: {self.persona}

Recent chat history (last few messages):
{formatted_chat_history}

Considering your role, political views, persona, and the ongoing discussion:
Generate a single, concise, and directly speakable chat message (around 20-50 words) to contribute to the parliamentary debate.
Your message should be in plain text, without any markdown or prefixes like your name.
If the current discussion is not relevant to your mandate, if you have no substantive contribution, or if another member is clearly being addressed, respond with only the word "PASS".'''
        
        try:
            # print(f"AIMemberAgent ({self.username}) Prompt: {prompt[:300]}...") # For debugging
            response = self.model.generate_content(prompt)
            
            if response and response.parts:
                generated_text = "".join(part.text for part in response.parts).strip()
            elif response and hasattr(response, 'text') and response.text: # Fallback for simpler text responses
                 generated_text = response.text.strip()
            else: # No valid response content
                print(f"AIMemberAgent ({self.username}): Gemini response had no valid parts or text.")
                generated_text = "PASS"
                
        except Exception as e:
            print(f"AIMemberAgent ({self.username}): Error calling Gemini API: {e}")
            return None # Return None on API error

        if generated_text.upper() == "PASS" or not generated_text:
            # print(f"AIMemberAgent ({self.username}): Decided to PASS or generated empty response.")
            return None
        
        # Basic filter for self-mentioning if Gemini doesn't obey the prompt
        # This could be made more robust with regex if needed
        generated_text = generated_text.replace(f"{self.username}:", "").replace(f"{self.username} says:", "").strip()
        
        # Further ensure conciseness (though prompt asks for max 50 words)
        # This is a soft limit, actual enforcement might need token counting or stricter post-processing.
        # For now, let's assume the model tries to adhere to the word count.
        
        return generated_text

    def send_message(self, recipient, text): 
        """Saves AI message to DB and returns message dictionary for emission."""
        if not self.db:
            print(f"AIMemberAgent ({self.username}) Error: Database module not configured.")
            return

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.db.add_message(self.username, recipient, text, timestamp_str):
            print(f"AIMemberAgent ({self.username}): Message to {recipient} saved to DB.")
            
            emitted_message = {
                "sender_username": self.username,
                "recipient_username": recipient,
                "text": text,
                "timestamp": timestamp_str
            }
            # Removed direct socketio.emit call
            # if self.socketio:
            #     self.socketio.emit('new_message', emitted_message) 
            #     print(f"AIMemberAgent ({self.username}): Message emitted via SocketIO to {recipient}: '{text}' (intended for all)")
            # else:
            #     print(f"AIMemberAgent ({self.username}): SocketIO instance not available. Message not emitted.")
            return emitted_message # Return the message dictionary
        else:
            print(f"AIMemberAgent ({self.username}): Failed to save message to {recipient} to DB.")
            return None # Return None if saving failed

    # Removed _load_messages and _save_messages as they are no longer needed

if __name__ == '__main__':
    # Example Usage (for testing AIMemberAgent independently)
    # Note: For direct testing of send_message with SocketIO and DB, 
    # mock socketio and db_module objects would be needed.
    
    # Basic instantiation test
    # agent = AIMemberAgent("AI_Test", "Neutral", "Test Persona")
    # print(f"Agent initialized with username: {agent.username}")

    # Example of how generate_response might be tested (needs mock db and socketio)
    # class MockDB:
    #     def add_message(self, s, r, t, ts): return True
    # class MockSocketIO:
    #     def emit(self, event, data, broadcast): pass
        
    # agent_with_mocks = AIMemberAgent(
    #     "AI_Test_Eco", 
    #     "Advocates for strong environmental regulations and social ownership of key industries.",
    #     persona="Speaks formally, often citing ecological data and social justice principles.",
    #     socketio_instance=MockSocketIO(), 
    #     db_module=MockDB()
    # )
    # sample_messages_db_format = [
    #     {"sender_username": "user1", "recipient_username": "general", "text": "I think we need more parks and environmental focus.", "timestamp": "2023-01-01 10:00:00"},
    #     {"sender_username": "user2", "recipient_username": "general", "text": "What about the budget for that?", "timestamp": "2023-01-01 10:01:00"}
    # ]
    # response = agent_with_mocks.generate_response(sample_messages_db_format)
    # if response:
    #     print(f"Agent {agent_with_mocks.username} generated response: {response}")
    # else:
    #     print(f"Agent {agent_with_mocks.username} chose not to respond.")
        
    print("AIMemberAgent basic structure test complete. For full test, run the Flask app.")
