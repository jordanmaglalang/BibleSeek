

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
# Use a context manager properly for async SQLite saver (if required by the framework)
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
memory = MemorySaver()



tool = TavilySearchResults(max_results=2)


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        print("initialization")
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END} #if function returns true, go to the action node, if false, go to the end node
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer = checkpointer, interrupt_before=["action"]) # calling and invoking the graph
        self.tools = {t.name: t for t in tools}#creates a dictionary where each object's name in the list tools is the key and the object itself as the value
        self.model = model.bind_tools(tools) #letting the model know that it has these tools available to call
    def exists_action(self, state: AgentState):
        print("exists action check")
        result = state['messages'][-1]
        print("Last message in state:", result)
        return len(result.tool_calls) > 0
    def call_openai(self, state: AgentState):#llm node
        print("call_openai activated")
        messages = state['messages'] #extracts the list 'messages' of the state
        print("Messages at OpenAI step:", messages)
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages #if there is a system message, it adds to the messages list, ensuring proper order
        message = self.model.invoke(messages) #messages is the list of messages
        print("Model output:", message)
        return {'messages': [message]}
    def take_action(self, state: AgentState):
        print("take action activated")
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling tool: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("Bad tool name detected")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])  # Call the tool with the arguments
                print(f"Tool result: {result}")
            
            # Append the result for the current tool call
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        
        print("Returning results to model")
        return {'messages': results}


prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""
model = ChatOpenAI(model="gpt-4-turbo")
abot = Agent(model, [tool], system=prompt, checkpointer=memory)

messages = [HumanMessage(content="What is the weather in LA??")]
thread = {"configurable": {"thread_id": "1"}} # keep track of threads inside persistence checkpointer, has one key called configurable,
#result = abot.graph.invoke({"messages": messages})
# Async function to run the agent

for event in abot.graph.stream({"messages": messages},thread):
    for v in event.values():
      print(v)

# Run the agent within an async event loop

"""
print("#######################")

print(abot.graph.get_state(thread).values['messages'][-1])
"""

# Before updating state, check the state
current_values = abot.graph.get_state(thread)

# Ensure the correct tool call is in place before updating
_id = current_values.values['messages'][-1].tool_calls[0]['id']
current_values.values['messages'][-1].tool_calls = [
    {'name': 'tavily_search_results_json', 'args': {'query': 'current weather in Maryland'}, 'id': _id}
]

# Update the state after making changes
abot.graph.update_state(thread, current_values.values)

for event in abot.graph.stream(None,thread):
    for v in event.values():
      print(v)
      