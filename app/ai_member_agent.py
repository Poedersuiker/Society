import json
import datetime
import os
import random

class AIMemberAgent:
    def __init__(self, username, political_view, persona=None):
        self.username = username
        self.political_view = political_view
        self.persona = persona if persona else "A political representative."
        self.MESSAGES_FILE = 'data/messages.json' # Default, can be overridden
        self.speak_probability = 0.2 # Chance to speak after a relevant message
        self.keywords = self._extract_keywords(political_view)

    def _extract_keywords(self, view):
        # Simple keyword extraction (can be improved)
        # Takes words longer than 5 chars, not common words
        common_words = {"advocates", "focuses", "prioritizes", "social", "strong", "reduced", "government", "market", "values", "protection", "often", "general", "stance", "describing", "their", "related", "consider", "think", "should"}
        words = view.lower().replace('.', '').replace(',', '').split()
        return [word for word in words if len(word) > 5 and word not in common_words]


    def generate_response(self, all_messages):
        """
        Generates a response based on message history and political view.
        Simple initial logic: randomly decides to speak, formulates a simple message.
        """
        if not all_messages:
            return None

        # Only respond to messages not from other AI agents (including self) or ModeratorBot
        last_message = all_messages[-1]
        # We need a list of AI usernames to check against. For now, hardcode common AI prefixes.
        # This should ideally be passed or managed centrally.
        ai_prefixes_to_ignore = ("AI_", "ModeratorBot")
        if last_message['sender'].startswith(ai_prefixes_to_ignore):
            return None # Don't respond to other AI messages

        if random.random() < self.speak_probability:
            if self.keywords:
                keyword = random.choice(self.keywords)
                possible_phrases = [
                    f"Considering our stance on {keyword}, we should analyze this further.",
                    f"The principle of {keyword} is very relevant here.",
                    f"Let's not forget the importance of {keyword} in this discussion.",
                    f"I believe {keyword} should be a key factor in our decision.",
                    f"From my perspective, {keyword} is paramount."
                ]
                return random.choice(possible_phrases)
            else:
                # Fallback if no keywords extracted
                return f"I am reflecting on this from the perspective of: {self.political_view}"
        return None

    def send_message(self, recipient, text, messages_file=None):
        """Allows the AI member to send messages to the chat."""
        if messages_file is None:
            messages_file = self.MESSAGES_FILE
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_message = {
            "sender": self.username,
            "recipient": recipient,
            "text": text,
            "timestamp": timestamp
        }

        messages = self._load_messages(messages_file)
        messages.append(new_message)
        self._save_messages(messages, messages_file)
        print(f"AIMemberAgent ({self.username}): Message sent to {recipient}: '{text}'")

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
    # Example Usage (for testing AIMemberAgent independently)
    ai_def1 = {
        "username": "AI_Test_Eco",
        "political_view": "Advocates for strong environmental regulations and social ownership of key industries.",
        "persona": "Speaks formally, often citing ecological data and social justice principles."
    }
    agent1 = AIMemberAgent(**ai_def1)

    # Simulate a message history
    sample_messages = [
        {"sender": "user1", "recipient": "general", "text": "I think we need more parks.", "timestamp": "2023-01-01 10:00:00"},
        {"sender": "user2", "recipient": "general", "text": "What about the budget for that?", "timestamp": "2023-01-01 10:01:00"}
    ]
    
    response = agent1.generate_response(sample_messages)
    if response:
        print(f"Agent {agent1.username} generated response: {response}")
        # agent1.send_message("general", response) # Uncomment to test file writing
    else:
        print(f"Agent {agent1.username} chose not to respond.")

    # Test with a message from another AI (should not respond)
    sample_messages_from_ai = [
        {"sender": "AI_Another_Bot", "recipient": "general", "text": "I agree with more parks.", "timestamp": "2023-01-01 10:02:00"}
    ]
    response_to_ai = agent1.generate_response(sample_messages_from_ai)
    if response_to_ai:
        print(f"Agent {agent1.username} generated response to AI: {response_to_ai} (ERROR: Should not respond)")
    else:
        print(f"Agent {agent1.username} correctly chose not to respond to another AI.")
        
    print("AIMemberAgent basic test complete.")
