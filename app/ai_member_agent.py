import json
import datetime
import os
import random
# No longer need to import json or os if not using JSON files directly

class AIMemberAgent:
    def __init__(self, username, political_view, persona=None, socketio_instance=None, db_module=None):
        self.username = username
        self.political_view = political_view
        self.persona = persona if persona else "A political representative."
        self.socketio = socketio_instance
        self.db = db_module # Store the database module instance
        
        self.base_speak_probability = 0.1  # Lower base probability
        self.triggered_speak_probability = 0.6 # Higher probability if triggered by keyword
        
        self.common_stopwords = set([
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
            "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
            "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
            "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
            "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", 
            "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", 
            "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", 
            "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", 
            "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", 
            "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", 
            "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", 
            "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", 
            "than", "that", "that's", "the", "their", "theirs", "them", "themselves", 
            "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", 
            "they've", "this", "those", "through", "to", "too", "under", "until", "up", 
            "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", 
            "weren't", "what", "what's", "when", "when's", "where", "where's", "which", 
            "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", 
            "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", 
            "yourself", "yourselves"
        ])
        self.interest_keywords = self._extract_interest_keywords()


    def _extract_interest_keywords(self):
        # Extract significant words from political_view and persona
        raw_keywords = (self.political_view + " " + self.persona).lower().replace('.', '').replace(',', '').split()
        
        # More refined list of stopwords specific to political discourse or common in descriptions
        # self.common_stopwords is already defined, so we can use it directly.
        discourse_stopwords = {
            "advocates", "focuses", "prioritizes", "government", "policy", "impact", "issues",
            "social", "strong", "reduced", "market", "values", "protection", "often", "general",
            "stance", "describing", "their", "related", "consider", "think", "should", "believe",
            "perspective", "approach", "system", "development", "economic", "national", "public",
            "support", "rights", "freedom", "justice", "equality", "community", "growth", "well-being"
        }
        # The original self.common_stopwords was a small set. The new one is comprehensive.
        # We'll use the comprehensive one and add discourse_stopwords to it for this method's purpose.
        combined_stopwords = self.common_stopwords.union(discourse_stopwords)

        # Keep words longer than 3 characters and not in combined_stopwords
        interest_keywords = [word for word in raw_keywords if len(word) > 3 and word not in combined_stopwords]
        return list(set(interest_keywords))

    def _extract_message_keywords(self, message_text):
        words = message_text.lower().replace('.', '').replace(',', '').split()
        # Use the comprehensive self.common_stopwords here as well.
        return [word for word in words if word not in self.common_stopwords and len(word) > 3]

    def generate_response(self, all_messages):
        if not all_messages:
            return None

        last_message = all_messages[-1]
        # In generate_response, last_message structure will depend on how it's passed.
        # Assuming it's a dict from db.get_all_messages() which now aligns with db columns.
        last_message_sender = last_message.get('sender_username', '')
        last_message_text = last_message.get('text', '')

        # Do not respond to self, ModeratorBot, or other AI agents
        if last_message_sender == self.username or \
           last_message_sender == "ModeratorBot" or \
           (last_message_sender and last_message_sender.startswith("AI_")): # Added check for None
            return None

        message_keywords = self._extract_message_keywords(last_message_text)
        matched_keywords = [kw for kw in self.interest_keywords if kw in message_keywords]

        current_speak_probability = self.base_speak_probability
        if matched_keywords:
            current_speak_probability = self.triggered_speak_probability
            print(f"Agent {self.username} triggered by keywords: {matched_keywords} in message: '{last_message_text}'")


        if random.random() < current_speak_probability:
            topic_keyword = random.choice(matched_keywords) if matched_keywords else random.choice(self.interest_keywords) if self.interest_keywords else "the current topic"
            
            # Simple way to get a snippet of the political view for responses
            view_snippet_words = [w for w in self.political_view.lower().split() if w not in self.common_stopwords and len(w) > 4]
            view_snippet = " ".join(random.sample(view_snippet_words, min(len(view_snippet_words), 3))) if view_snippet_words else "our core principles"


            response_templates = [
                f"Regarding '{topic_keyword}', my perspective is that we should focus on {view_snippet}.",
                f"The recent point about '{topic_keyword}' aligns with my view on {random.choice(self.interest_keywords) if self.interest_keywords else view_snippet}.",
                f"I'd like to add that {self.persona.split('.')[0]}, especially concerning '{topic_keyword}'.",
                f"Considering '{topic_keyword}', it's crucial to remember our commitment to {view_snippet}.",
                f"This discussion on '{topic_keyword}' directly relates to {random.choice(self.interest_keywords) if self.interest_keywords else 'our broader agenda'}. We must ensure {view_snippet}."
            ]
            
            if not self.interest_keywords and not matched_keywords: # Fallback if no keywords at all
                 return f"I am reflecting on the discussion. {self.persona.split('.')[0]}."

            return random.choice(response_templates)
            
        return None

    def send_message(self, recipient, text): # Removed messages_file argument
        """Allows the AI member to send messages to the chat, save to DB, and emit via SocketIO."""
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
