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
        self.graph = graph.compile(checkpointer = checkpointer) # calling and invoking the graph
        self.tools = {t.name: t for t in tools}#creates a dictionary where each object's name in the list tools is the key and the object itself as the value
        self.model = model.bind_tools(tools) #letting the model know that it has these tools available to call
    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0
    def call_openai(self, state: AgentState):#llm node
        messages = state['messages'] #extracts the list 'messages' of the state
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages #if there is a system message, it adds to the messages list, ensuring proper order
        message = self.model.invoke(messages) #messages is the list of messages
        return {'messages': [message]}
    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
prompt = """You are a smart research assistant. Use the search engine to look up information. \
You are allowed to make multiple calls (either together or in sequence). \
Only look up information when you are sure of what you want. \
If you need to look up some information before asking a follow up question, you are allowed to do that!
"""
model = ChatOpenAI(model="gpt-4-turbo")
abot = Agent(model, [tool], system=prompt, checkpointer=memory)

messages = [HumanMessage(content="What are some verses in the bible that help with finding my purpose?")]
thread = {"configurable": {"thread_id": "1"}} # keep track of threads inside persistence checkpointer, has one key called configurable,

# Async function to run the agent
for event in abot.graph.stream({"messages": messages},thread):
    for v in event.values():
        print(v['messages'])

# Run the agent within an async event loop
