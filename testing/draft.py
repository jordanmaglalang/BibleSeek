 
from dotenv import load_dotenv

_ = load_dotenv()
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage, ChatMessage
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
class AgentState(TypedDict):
    task: str # human input
    plan: str # the planning agent for essay
    draft: str # drafts for the essay
    critique: str # critique agent for the essay
    content: List[str] # list of documents that tavily has researched and come back with
    revision_number: int # number of revisions
    max_revisions: int # maximum revisions 
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
or instructions for the sections."""
WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
Generate the best essay possible for the user's request and the initial outline. \
If the user provides critique, respond with a revised version of your previous attempts. \
Utilize all the information below as needed: 

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following essay. Generate a list of search queries that will gather \
any relevant information. Only generate 3 queries max."""




RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""
from pydantic import BaseModel


class Queries(BaseModel):
    queries: List[str] #results we get back from llm
from tavily import TavilyClient
import os
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def plan_node(state: AgentState): # take in the state
    messages = [# create a list of messages
        SystemMessage(content=PLAN_PROMPT), # the planned prompt from the system message
        HumanMessage(content=state['task']) # the task from the human message
    ]
    response = model.invoke(messages) #pass the message to the model
    return {"plan": response.content} #update the plan key to be this response and return it
def research_plan_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([ # the response we are gonna invoke this with is the pydantic object which has the list of queries
        SystemMessage(content=RESEARCH_PLAN_PROMPT), 
        HumanMessage(content=state['task'])
    ])
    content = state.get('content',[]) # if there is content exists, if not its empty
    for q in queries.queries: #search within the queries object the string list of queries, in which tavily will  search each item in the list of strings containing queries
        response = tavily.search(query=q, max_results=2) #returns a structured response of top 2 answers
        for r in response['results']: #in each response, append to content which is in AgentState
            content.append(r['content'])
    return {"content": content} #list of documents tavily came back with
def generation_node(state: AgentState):
    content = "\n\n".join(state['content'] or []) #joing the list of strings of resources into one
    user_message = HumanMessage( 
        content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")# task is the human input, annd the plan is the plan generated
    messages = [#list of messages combining research and user message 
        SystemMessage(
            content=WRITER_PROMPT.format(content=content) 
        ),
        user_message
        ]
    response = model.invoke(messages) #store response from the model
    return {
        "draft": response.content, #response from the model becomes draft
        "revision_number": state.get("revision_number", 1) + 1 #keep track of revision number to fit criteria of final result
    }


def reflection_node(state: AgentState):
    messages = [
        SystemMessage(content=REFLECTION_PROMPT), 
        HumanMessage(content=state['draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content} #return the critique of the draft
def research_critique_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state['critique']) 
    ])
    content = state['content'] or []
    for q in queries.queries:
        response = tavily.search(query=q, max_results=2)
        for r in response['results']:
            content.append(r['content'])
    return {"content": content} #returns more content
def should_continue(state):
    if state["revision_number"] >= state["max_revisions"]:
        return END
    return"reflect"
builder = StateGraph(AgentState)
builder.add_node("planner", plan_node)
builder.add_node("generate", generation_node)
builder.add_node("reflect", reflection_node)
builder.add_node("research_plan", research_plan_node)
builder.add_node("research_critique", research_critique_node)

builder.add_conditional_edges(
    "generate",
    should_continue,
    {END: END, "reflect": "reflect"} #outcomes after return value
)
builder.set_entry_point("planner")
builder.add_edge("planner", "research_plan")
builder.add_edge("research_plan", "generate")
builder.add_edge("reflect", "research_critique")
builder.add_edge("research_critique", "generate")

graph = builder.compile(checkpointer=memory)

thread = {"configurable": {"thread_id": "1"}}

for s in graph.stream({
    'task': "what is the difference between langchain and langsmith",
    "max_revisions": 2,
    "revision_number": 1,
}, thread):
    print(s)


