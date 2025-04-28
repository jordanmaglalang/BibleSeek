import os
import schedule
import time
import threading
from datetime import datetime
from flask import Flask, render_template
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph
from db import notes_collection



model_two = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define AgentState (TypedDict) to structure our state
class AgentState2(TypedDict):
    notes_reference: str
    summary: str  # We'll store the summary here
    

# Fetch the latest notes from the database
def get_latest_notes():
    latest_note = notes_collection.find().sort('_id', -1).limit(1)  # limit to 1 document
    latest_notes = latest_note[0]['notes']  # Extract the 'notes' value from the document
    return latest_notes

# Summarization Prompt (using user's notes)
SUMMARY_PROMPT = """
You are a Bible expert and a spiritual guide tasked with transforming a large text of Bible notes into a concise, self-reflective, and encouraging devotional. Your goal is to condense these notes into a brief summary that highlights key spiritual insights, themes, and Bible verses while inspiring and encouraging the reader to deepen their faith and understanding.

### Instructions:
1. **Review the user's notes** carefully, reflecting on the deeper meaning and wisdom they contain.
2. **Summarize the content** in a clear, straightforward, and reflective manner, highlighting the lessons and encouragement it offers.
3. The summary should be **brief yet meaningful**, easy to read, and accessible to a broad audience.
4. The tone should be **uplifting, inspiring, and reflective**, fostering spiritual growth and encouraging a closer relationship with God.
5. Consider how the insights and Bible verses can **apply to daily life**, offering practical encouragement for the reader’s spiritual journey.

### Notes to Summarize:
{notes_reference}

### Summary Output:
"""

# Devotional Prompt (based on the summary)
DEVOTIONAL_PROMPT = """
Imagine you are a spiritual guide helping someone deepen their understanding of the Bible. Your task is to take the Bible notes summary provided by the user and use them as a reference to create a detailed, applicable, compelling, and easy-to-read daily devotional.

### Instructions:
1. Begin by reviewing the user's summary.
2. Use a Bible verse to support the devotional's key message.
3. Provide a detailed explanation and practical application.
4. Conclude with a reflection or prayer prompt.

User's Summary:
{summary}

### Devotional Output:
"""

# Define the Devotional class
class Devotional:
    def __init__(self, model, system):
        self.model = model
        self.system = system
        # Create the graph and assign it to the instance variable self.graph
        graph = StateGraph(AgentState)
        graph.add_node("summarize_notes", self.summary)
        graph.add_node("create_devotional", self.create_devotional)
        graph.add_edge("summarize_notes", "create_devotional")
        # Set the entry point to "summarize_notes"
        graph.set_entry_point("summarize_notes")
        self.graph = graph.compile()

    def summary(self, state: AgentState2):
        # Use the model to summarize the user's notes
        summary_prompt = SUMMARY_PROMPT.format(notes_reference=state['notes_reference'])
        messages = [SystemMessage(content=summary_prompt)]
        summary_response = self.model.invoke(messages)
        state['summary'] = summary_response.content
        return state

    def create_devotional(self, state: AgentState2):
        # Debug: Print the state to check if summary exists
        print("State before creating devotional:", state["summary"])
        
        if 'summary' in state:
            # Use the summary to generate the devotional
            devotional_prompt = self.system.format(summary=state['summary'])
            messages = [SystemMessage(content=devotional_prompt)]
            devotional_response = self.model.invoke(messages)
            
            # Debug: Check the response from the model
            print("Devotional generated:", devotional_response.content)
            
            return {"devotional": devotional_response.content}
        else:
            # If summary doesn't exist, return an error or a default message
            return {"error": "Summary is missing. Please ensure summary generation step is successful."}

# Function to run the graph at 8:00 AM every day
def run_devotional():
    latest_notes = get_latest_notes()  # Fetch latest notes from the database
    state = AgentState2(notes_reference=latest_notes)  # Prepare the state with the latest notes

    # Instantiate the Devotional class
    devotional_generator = Devotional(model=model_two, system=DEVOTIONAL_PROMPT)

    # Run the graph, this will first summarize the notes and then generate the devotional
    result = devotional_generator.graph.invoke(state)
    global devotional_string 
    devotional_string = result.get('devotional', "No devotional generated.")

    print(result)



def schedule_devotional():
# Schedule the function to run at 8:00 AM every day
    schedule.every().day.at("12:03").do(run_devotional)


    # Keep the script running and check every minute if the scheduled time has arrived
    while True:
        schedule.run_pending()  # Check if the scheduled time has arrived and run the task
        time.sleep(60)  # Wait for 60 seconds before checking again







"""schedule_thread = threading.Thread(target=schedule_devotional)
    schedule_thread.daemon = True
    schedule_thread.start()
    print("he devotional string is ", devotional_string)"""





