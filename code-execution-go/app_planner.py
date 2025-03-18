from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)

llm_smart = ChatOpenAI(model="gpt-4o", temperature=0.2)

# Define planner
from typing import Annotated
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    
class CreateFunctionPlanner:
    def __init__(self, llm: BaseChatModel, prompt: ChatPromptTemplate):
        self.runnable = prompt | llm

    def __call__(self, state: State) -> dict:
        return {"messages": [self.runnable.invoke({"messages": state["messages"]})]}
    
from langchain_core.output_parsers import StrOutputParser
create_function_plan_prompt = ChatPromptTemplate.from_messages([
      ("system",
      """
      You are professional golang developer that excel in TDD.
      You will be provided with high level requirements.
      Let's first understand provided requirements then create application blueprint.
      Please create plan for implementation of functions needed to complete the requirements.
      Each function should have a clear purpose and should be named descriptively.
      If any function is too complex, you can break it down into smaller functions.
      The output will be 2 parts, the first part will be the list of functions and
      the second part will be flow of how these functions will interact with each other.
      The first part output will start with "Functions:" and followed by this format,
      - Signature:
        Purpose:
      The second part output will start with "Flow:" followed by the flow of functions.
      After you get human feedback on the plan, you will revise the plan based on the feedback.
      No preamble or explanation is needed, just the plan.
      """),
      ("user",
      """
      {messages}
      """),
  ])
def create_function_plan(requirement: str) -> str:
  chain = create_function_plan_prompt | llm | StrOutputParser()
  test_cases = chain.invoke({"input": requirement})
  return test_cases

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

requirement = """
Given 2 list of objects, list A and B, that each object consist of key is_main, order, and image_id.
Return a list of change that need to be made to transform list A to list B.
"""

planner = CreateFunctionPlanner(llm, create_function_plan_prompt)
# Define a new graph
workflow = StateGraph(State)
workflow.add_node("planner", planner)
workflow.set_entry_point("planner")
workflow.add_edge("planner", END)

app = workflow.compile(checkpointer=MemorySaver())

from langchain.schema import AIMessage, HumanMessage
import gradio as gr
from langchain_core.messages import HumanMessage
import uuid
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

def predict(message, history):
    for output in app.stream({"messages": [HumanMessage(content=message)]}, config):
        for key, value in output.items():
            message = value.get("messages")
            if message and isinstance(message, list):
                message = message[-1]
            yield message.content

gr.ChatInterface(predict,
                retry_btn=None,
                undo_btn=None,
                clear_btn=None,).launch()