from dotenv import load_dotenv
# Load environment variables
_ = load_dotenv()
from langgraph.graph import StateGraph
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
import langchain
from typing import TypedDict, List
from bson import ObjectId
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph


langchain.verbose = False
langchain.debug = False
langchain.llm_cache = False



chat_history = []
notes=[]


# Initialize the OpenAI model
model = ChatOpenAI()
class AgentState(TypedDict):
    task: str
    relevancy: bool
    
    conversation_history: List[str]
    notes_history: List[str]
    response: str

def initialize_graph(session_data,input):
    # Build the graph using StateGraph
    memory = MemorySaver()
    print("INITTTT ", session_data)
    # Initialize the state dictionary and keep the conversation history persistent
    state = {
        'task': f"{input}",
        'relevancy': False,
        'notes_history':session_data.get('notes_history', []) ,
        'conversation_history': []  # Initialize empty history
    }
    
    # Initialize the graph builder
    builder = StateGraph(AgentState)
    builder.add_node("user", user_input)
    builder.add_node("irrelevancy_node", if_irrelevant)
    builder.add_node("relevancy_node", if_relevant)
    builder.add_node("note_node", note_summary)
   
    # Add conditional edges for decision-making
    builder.add_conditional_edges(
        "user",
        is_relevant,
        {True: "relevancy_node", False: "irrelevancy_node"}
    )
    # Add edges to loop back to user node for further conversation
    builder.add_edge("relevancy_node", "note_node")
   
    # Set the entry point to "user"
    builder.set_entry_point("user")

    return run_graph_step(builder, memory, state, input, session_data)

def run_graph_step(builder, memory, state, input, session_data):
    print("RUN GRAPHHHHHHHHHHH")
    # Ensure conversation history is retained and updated within state
    graph = builder.compile(checkpointer=memory)
    thread = {"configurable": {"thread_id": "1"}}

    for s in graph.stream(state, thread):
        pass
     # Ensure AI response is appended to the conversation history
    ai_response = state.get('response', "No response generated.")
    state['conversation_history'].append(ai_response)
    # Return the response and full conversation history
    print("initilize graph session data ", session_data['notes_history']) 
    return {
        'response': chat_history[-1]['content'],  # This should be the AI response
        'notes_history': session_data['notes_history'],  # Make sure 'notes_history' is returned here
        'conversation_history': state['conversation_history']  # Return updated history
    }








# Prompts for relevant and non-relevant tasks

NON_RELEVANT_PROMPT = """You are a Bible expert with a deep understanding of Christianity and the Bible. Your job is to respond in a respectful and thoughtful manner if the User Task is not directly related to Christianity, the Bible, or Jesus, and includes discussions of other religions or arguments about other religions.

In your response:
1. **Acknowledge the user’s perspective** with respect and kindness, ensuring no offense is given.
2. **Gently guide the conversation back** to the focus of learning about the Bible, Christianity, or Jesus. If necessary, you can provide brief and non-confrontational clarifications using scripture or Christian teachings, but always in a way that respects the user's beliefs.
3. **Redirect the conversation** by either:
   - Offering a biblical perspective on a similar topic that aligns with Christianity.
   - Or, if the topic is unrelated, politely suggesting that the discussion focus on the Bible or Christianity. If the topic cannot be connected, gracefully close the conversation.
4. **Be empathetic and non-judgmental**: Respond in a manner that feels compassionate, and avoid sounding preachy or dismissive.

Here are some variations in how you can craft your response:

- "I appreciate your sharing your views. While we focus here on understanding Christianity and the Bible, let me offer a scripture that could be related to this discussion..."
- "Thank you for sharing. Christianity teaches us to love and respect all people. However, to guide this conversation, let me share what the Bible says about this..."
- "It's important to respect all beliefs. Let me take a moment to share how the Bible addresses this topic, focusing on Jesus' teachings about love and truth."
- "I hear your thoughts and appreciate the perspective. While we’re here to discuss Christianity, let me share what scripture has to say about this..."

User Task:

"""

SUMMARIZE_NOTES = """You are a Bible expert. Identify any specific bible verses in the explanation, and summarize the explanation of all Bible verses in the explanation into these bulletin points (within the context of the explanation), with each bulletin point being one sentence (max 3 bulletin points). If there is no mention of any specific Bible verses, simply leave the response with no text or any character at all. Make sure you quote the verse BEFORE the bulletin summary, and do ONLY what the example says if there are any specific bible verses in the explanation :

Example:

Verse: John 3:16 - "For God so loved the world, that He gave His only Son, that whoever believes in Him should not perish but have eternal life."

-God gave His Son to offer eternal life through belief.
-Belief in Jesus leads to salvation.
-Trusting in Jesus gives hope and transforms my life.

Verse: Ephesians 6:3 - "So that it may go well with you and that you may enjoy long life on the earth"

-The verse emphasizes that honoring one's parents leads to a long and blessed life.
-It is one of the Ten Commandments with a promise attached, highlighting its importance in Christian life.
-This verse underscores the value of respect and obedience within the family structure as ordained by God

Here is the explanation you have to summarize:

"""
def user_input(state: AgentState):
    
    print("chat history", len(chat_history))
    if len(chat_history) == 0:
        AI_input = SystemMessage(content="Hello! I am an AI assistant specializing in Bible-related topics. How can I assist you today?")
    else:
        AI_input = SystemMessage(content=chat_history[-1]['content'])  # Get the last AI message
    
    state['conversation_history'] = chat_history  # Update state with the latest conversation history
    return state

def is_relevant(state: AgentState):
    messages = [
        SystemMessage(content=f"""
You are a Bible expert and guide. Your job is to evaluate whether the user's input (User Task) is relevant to Christianity, the Bible, or Jesus based on the conversation history.

Even if the user doesn't directly mention the Bible, Christianity, or Jesus, look for connections to themes, values, or teachings related to Christianity, the Bible, or Jesus from earlier in the conversation. Even if a word, phrase, or idea doesn't seem explicitly related to the Bible, if it connects in any way to Christian principles, it should be considered relevant.

Here is the conversation history:
{state['conversation_history']}

User Task:
{state['task']}

Respond with:
- "True" if the task is related to Christianity, the Bible, or Jesus in any way, even indirectly, or connects to the themes discussed earlier in the conversation.
- "False" if the task is completely unrelated to the topics mentioned above and doesn't connect to any Christian-related context from the conversation history.

Make sure to think broadly about Christian ideas or principles that may have been discussed and how they relate to the current task, even if it's just a subtle connection.

""")
        
    ]
    
    response = model.invoke(messages)
    chat_history.append({'role': 'user', 'content': state['task']})
    chat_history.append({'role': 'system', 'content': response.content})
    state['conversation_history'] = chat_history
    state['relevancy'] = (response.content == "True")
    return state['relevancy']

def if_irrelevant(state: AgentState):
    messages = [
        SystemMessage(content=NON_RELEVANT_PROMPT),
        HumanMessage(content=state['task'])
    ]

    response = model.invoke(messages)
    state['response'] = response.content
   
    chat_history.append({'role': 'system', 'content': response.content})
    state['conversation_history'] = chat_history

    print("Response######### " ,response.content)
    
    return state  

def if_relevant(state: AgentState):
    state['relevancy'] = True
    messages = [
        SystemMessage(content=f"""You are a Bible expert here to guide the user in their Bible study. Respond to their questions in a thoughtful, clear, and compassionate way, using scripture to support your answers. Keep your responses concise and easy to understand, while being warm and empathetic.

Incorporate the conversation history below to provide a personalized and relevant response. Reflect on any previous themes or insights that could enrich your reply. Encourage the user to think deeply about the Bible and their spiritual journey, without overwhelming them, and ask questions if need be to keep them engaged.

Here’s the conversation history:
{state['conversation_history']}

User's Current Question:
{state['task']}
""")

       
    ]
    
    response = model.invoke(messages)
    chat_history.append({'role': 'system', 'content': response.content})
    state['conversation_history'] = chat_history  # Update state with the latest conversation history
    state['response'] = response.content
   
    
    return state
def note_summary(state:AgentState):
    print("notes summary")
    notes_history = state.get('notes_history', [])
    messages = [
        SystemMessage(content=SUMMARIZE_NOTES),
        SystemMessage(content=state['response'])
    ]

    response = model.invoke(messages)
    print("Summary############# ")
    notes_history.append(response.content)

    state['notes_history'] = notes_history
    notes = state['notes_history']
    for i in notes:
        print(" ")
        print(i)
   
    return state
