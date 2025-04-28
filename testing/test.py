import random

# Define the conversation graph using a dictionary
conversation_graph = {
    'greeting': ['Hi!', 'Hello!', 'Hey there!', 'Greetings!'],
    'how_are_you': ["I'm doing great, thanks!", "I'm good, how about you?", "I'm fine, how about you?"],
    'default_response': ["I see! Tell me more.", "Interesting! Go on.", "Nice! What else is on your mind?"],
    'goodbye': ["Goodbye!", "See you later!", "Catch you later!"]
}

# Function to simulate the conversation
def chatbot_conversation():
    current_node = 'greeting'
    print(f"Chatbot: {random.choice(conversation_graph[current_node])}")
    
    while True:
        user_input = input("You: ")
        
        if 'bye' in user_input.lower():
            print("Chatbot: Goodbye!")
            break

        # Respond based on the current node
        print(f"Chatbot: {random.choice(conversation_graph[current_node])}")
        
        # Transition to the next node
        if 'how are you' in user_input.lower():
            current_node = 'how_are_you'
        else:
            current_node = 'default_response'

# Start chatting
if __name__ == "__main__":
    chatbot_conversation()
