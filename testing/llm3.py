from dotenv import load_dotenv, find_dotenv
import os
_ = load_dotenv(find_dotenv())  # Load .env file if present

# Import relevant tools
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
tavily_api_key = os.getenv("TAVILY_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
# Initialize the TavilySearchResults tool with the API key
tool = TavilySearchResults(tavily_api_key = tavily_api_key,max_results=2)

# Print information to verify it's working
print(type(tool))  # Check the type of tool instance
print(tool.name)   # Check the name of the tool (if this is an attribute)
class AgentState(TypedDict):
    messages : Annotated[list[AnyMessage], operator.add]
class Agent:
    def __init__(self, model, tools, system=""):
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
        self.graph = graph.compile() # calling and invoking the graph
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

model = ChatOpenAI(model="gpt-4o")  #reduce inference cost
abot = Agent(model, [tool], system=prompt)

messages = [HumanMessage(content="What are some verses in the bible that help with finding my purpose?")]
result = abot.graph.invoke({"messages": messages})
output = result['messages'][-1].content
print(output)