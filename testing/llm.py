import openai
import re
import httpx
import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=os.getenv("API"))
completion = client.chat.completions.create(
    model="gpt-4",  # Ensure the correct model name
    messages=[{"role": "user", "content": "Hello world"}]
)
#print("hello world")

#print(completion.choices[0].message.content)

class Agent:
    def __init__(self, system=""):
        self.system = system # assigns the member variable system of instance self to system 
        self.messages = []
        if self.system:# if system is not empty append to messages list
            self.messages.append({"role": "system", "content": system})
    def __call__(self, message):# allows for a call to an instance of agent to be called like a function, accepting the object and the message
        
        self.messages.append({"role": "user", "content": message}) # appends the message to messages list
        result = self.execute()# execute() will generate a response based on the current messages list, which includes the user's messages and any previous messages
        self.messages.append({"role": "assistant", "content": result}) # append to result list
        return result# returns result
        

    def execute(self):
        completion = client.chat.completions.create(
                        model="gpt-4o", 
                        temperature=0,
                        messages=self.messages)
        return completion.choices[0].message.content
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

Example session:

Question: How much does a Bulldog weigh?
Thought: I should look the dogs weight using average_dog_weight
Action: average_dog_weight: Bulldog
PAUSE

You will be called again with this:

Observation: A Bulldog weights 51 lbs

You then output:

Answer: A bulldog weights 51 lbs
""".strip()
def calculate(what):
    return eval(what)

def average_dog_weight(name):
    if name in "Scottish Terrier": 
        return("Scottish Terriers average 20 lbs")
    elif name in "Border Collie":
        return("a Border Collies average weight is 37 lbs")
    elif name in "Toy Poodle":
        return("a toy poodles average weight is 7 lbs")
    else:
        return("An average dog weights 50 lbs")

known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight
}

abot = Agent(prompt)#calls init
"""
result = abot("How much does a toy poodle weigh?") #calls the call 
#print("resultttt is " , result)

result = average_dog_weight("Toy Poodle") 
print(result)


next_prompt = "Observation: {}".format(result)
#print(next_prompt)

print(abot(next_prompt)) #calls the call 

print(abot.messages)
"""
action_re = re.compile('^Action: (\w+): (.*)$')   # python regular expression to selection action

def query(question, max_turns=5):
    i = 0
    bot = Agent(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = bot(next_prompt)
        print(result)
        actions = [
            action_re.match(a) 
            for a in result.split('\n') 
            if action_re.match(a) #identifies if string matches regex
        ]
        if actions: #if there are actions in actions list
            # There is an action to run
            action, action_input = actions[0].groups() #extracts first action and action input
            if action not in known_actions:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            print(" -- running {} {}".format(action, action_input))
            observation = known_actions[action](action_input) #call one of the functions based on the action extracted and action input is the parameter to call
            print("Observation:", observation) #new prompt
            next_prompt = "Observation: {}".format(observation)
        else:
            return
question = """I have 2 dogs, a border collie and a scottish terrier. 
What is their combined weight"""
query(question)