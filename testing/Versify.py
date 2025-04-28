from dotenv import load_dotenv
import tiktoken
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import langchain
langchain.verbose = False
langchain.debug = False
langchain.llm_cache = False
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

# Initialize environment and model
_ = load_dotenv()
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
memory = MemorySaver()




# Prompts for relevant and non-relevant tasks
RELEVANT_PROMPT = """RELEVANT_PROMPT

You are a Bible expert. Your task is to evaluate whether the user's input (the task) is relevant to Christianity, the Bible, or Jesus, considering the context provided by the conversation history. Even if the user's task doesn’t explicitly mention the Bible or Christianity, you should assess whether it connects to any previous conversation that relates to those topics.

Based on the provided conversation history and the task, respond with:

"True" if the task is relevant to Christianity, the Bible, or Jesus, or if it connects to previous discussions about them.
"False" if the task is not relevant to Christianity, the Bible, or Jesus, even indirectly.
Here is the conversation history:
{state['conversation_history']}

Here is the user's task:
{state['task']}

Make sure to only respond with "True" or "False" based on the relevance of the task in the context of the conversation history.
"""

NON_RELEVANT_PROMPT = """You are a Bible expert with a deep understanding of Christianity and the Bible. Your task is to respond in a respectful and thoughtful manner if the user’s input is not directly related to Christianity, the Bible, or Jesus, and includes discussions of other religions or arguments about other religions.

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

Here is the user's input:
{task}

{task}
"""
AGENT_RESPONSE_PROMPT = """""


Prompt

You are a Bible study guide, theologian, and pastor, here to help the user explore God’s Word in a way that feels personal and meaningful. Your goal is to help them not only understand what the Bible says but also reflect on how it can shape their life today.

When responding, take one of these two approaches:

If the user mentions or refers to a Bible verse: Break down what the verse really means, but don’t just stop there. Help them think about how it applies to their life right now. For example, ask, “How does this verse relate to where you are today?” or “What do you feel God might be saying to you through this passage?”

If the user doesn’t mention a verse but shares an idea or concept: Find a Bible verse that fits the topic and explain what it teaches. Then, ask something like, “What do you think God might be trying to say to us here?” or “How does this passage challenge us to live differently?”

In both cases, your goal is to make the conversation feel like a real, thoughtful exchange. Encourage the user to reflect on how God’s Word speaks to their life personally, helping them connect their faith with everyday living.
Here is the conversation history and the user's task:
"""


SUMMARIZE_NOTES = """You are a Bible expert. If a bible verse is explicitely mentioned in the explanation,  summarize the explanation of each Bible verse into these bulletin points (within the context of the explanation), with each bulletin point being one sentence (max 3 bulletin points). If there is no mention of a specific Bible verse, simply leave the response with no text or any character at all. Make sure you state the verse BEFORE the bulletin summary, and do ONLY what the example says if there are any specific bible verses in the explanation :


Example:

Verse: John 3:16 - "For God so loved the world, that He gave His only Son, that whoever believes in Him should not perish but have eternal life."



-God gave His Son to offer eternal life through belief.
-Belief in Jesus leads to salvation.
-Trusting in Jesus gives hope and transforms my life.


Here is the explanation you have to summarize:

"""


# Define the AgentState class for type safety
class AgentState(TypedDict):
    task: str #used
    relevancy: bool #used
    cycle_count: int #used
    
   
    response: str
    conversation_history: List[str]
    notes_history: List[str]
    






def user_input(state: AgentState):
    history = state.get('conversation_history', [])
    if len(history) == 0:
        AI_input = SystemMessage(content="Hello! I am an AI assistant specializing in Bible-related topics. How can I assist you today?")
    else:
        #history = truncate_conversation_history(history)
        AI_input = SystemMessage(content=history[-1]['content'])  # Get the last AI message
    #print(AI_input.content)  
    user = input("User: ")  
    state['task'] = user  
    history.append({'role': 'user', 'content': user})
    
    
    return state

def is_relevant(state: AgentState):
    print("is relevant activated ")
    messages = [
        SystemMessage(content=RELEVANT_PROMPT),
        HumanMessage(content=f"Based on the conversation history: {state['conversation_history']}, and the user task: {state['task']}, respond with 'True' if the task is relevant or 'False' if not in the context of the conversation history .")
    ]
    
    response = model.invoke(messages)
  
    state['conversation_history'].append({'role': 'system', 'content': response.content})

   
    state['relevancy'] = (response.content == "True")
    
  
    if state['relevancy']:
        return state["relevancy"]
    return state["relevancy"]

def if_irrelevant(state: AgentState):
    messages = [
        SystemMessage(content=NON_RELEVANT_PROMPT),
        HumanMessage(content=state['task'])
    ]

    response = model.invoke(messages)
    state['response'] = response.content
    state['conversation_history'].append({'role': 'system', 'content': response.content})
    print("Response######### " ,response.content)
    
    return state  

def if_relevant(state: AgentState):
    print("if relevant is activated")
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
    

    state['response'] = response.content
    print("Response############################    ", state['response'])
    return state
def note_summary(state:AgentState):
    notes_history = state.get('notes_history', [])
    messages = [
        SystemMessage(content=SUMMARIZE_NOTES),
        SystemMessage(content=state['response'])
    ]

    response = model.invoke(messages)
    print("response ", response.content)
    print("Summary############# ")
    notes_history.append(response.content)
    state['notes_history'] = notes_history
    for i in state['notes_history']:
        print(" ")
        print(i)
   
    return state
   
state = {
    'task': "",  # User's input task
    'relevancy': False,  # Initially assume the task is not relevant
     'cycle_count': 0,
    'conversation_history': []  # Start with an empty conversation history
}



# Build the graph using StateGraph
builder = StateGraph(AgentState)

# Add nodes
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
builder.add_edge("irrelevancy_node", "note_node")
builder.add_edge("note_node", "user")
builder.add_edge("relevancy_node", "note_node")

# Set the entry point to "user"
builder.set_entry_point("user")

# Compile the graph
graph = builder.compile(checkpointer=memory)

# Initialize the thread and start the conversation flow
thread = {"configurable": {"thread_id": "1"}}
i = 0
for s in graph.stream(state, thread):
    print()
    #print(state['cycle_count'])  # Debug: Print each state during the stream



