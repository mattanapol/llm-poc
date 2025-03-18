import autogen
from typing import Annotated
import subprocess

WORKING_CODE_DIR = "./code"

def test_code() -> str:
    return execute_sh_command("go test ./...")

def install_go_package(package: Annotated[str, "The package to install."]) -> str:
    return execute_sh_command(f"go get {package}")

def execute_sh_command(command: Annotated[str, "The command you want to execute."]) -> str:
  try:
    output = subprocess.check_output(command.split(), text=True, stderr=subprocess.STDOUT, cwd=WORKING_CODE_DIR)
    return output.strip()  # Remove leading/trailing whitespace
  except subprocess.CalledProcessError as e:
    error_msg = f"Error executing test code: {e.output}"
    return error_msg
  except Exception as e:
    return f"Error executing test code: {str(e)}"

def save_file(file_path: Annotated[str, "The path to the file."],
              content: Annotated[str, "The content to write to the file."]) -> str:
    with open(WORKING_CODE_DIR + "/" + file_path, 'w') as file:
        file.write(content)
    return f"File saved to {file_path}"

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST.json",
)

llm_config = {
    "cache_seed": 47,
    "temperature": 0,
    "config_list": config_list,
    "timeout": 120,
}

user_proxy = autogen.UserProxyAgent(
    name="User",
    system_message="Executor. Execute the code using tools provided and suggest updates if there are errors.",
    human_input_mode="ALWAYS",
    code_execution_config=False,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)

planner = autogen.AssistantAgent(
    name="Planner",
    llm_config=llm_config,
    description="Planner that will plan code architecture.",
    system_message="""You are golang developer that expert in planning code architecture.
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
      After you get feedback on the plan, you will revise the plan based on the feedback.
      No preamble or explanation is needed, just the plan.
    """,
)
coder = autogen.AssistantAgent(
    name="Coder",
    llm_config=llm_config,
    description="Developer that only write code for function.",
    system_message="""You are a developer that expert in golang and TDD.
    If you want the user to save the code in a file before executing it, put // filename: <filename> inside the code block as the first line.
    Coder. Your job is to write only complete golang code without unittest, if a function is too complex break it down to smaller function.
    Each function should be in separate file.
    """,
)
unit_test_coder = autogen.AssistantAgent(
    name="UnitTestCoder",
    llm_config=llm_config,
    description="Developer that only write unittest code.",
    system_message="""You are a developer that expert in golang and TDD.
    If you want the user to save the code in a file before executing it, put // filename: <filename> inside the code block as the first line.
    Every test file will end with _test.go, for example: main.go -> main_1_test.go
    UnitTestCoder. Your job is to write only complete golang unittest code, while each test case should be in separate file.
    Write only unittest code, assuming function already been implemented. Write one file at a time.
    """,
)

tester = autogen.AssistantAgent(
    name="TestcaseWriter",
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    system_message="""You are a software quality assurance.
    Your job is to write test case that cover all scenario of provided requirement, don't need to write any code.
    """,
)

assistant = autogen.ConversableAgent(
    name="Assistant",
    human_input_mode="TERMINATE",
    description="Agent that can save file and test code.",
    system_message="You are agent that will only suggest user to use tools provided. "
                   "Return 'TERMINATE' when the task is done.",
    llm_config={
        "config_list": config_list
    }
)

# Register the tool signature with the assistant agent.
assistant.register_for_llm(name="save_file", description="save file to local storage")(save_file)
assistant.register_for_llm(name="test_code", description="test generated code")(test_code)
assistant.register_for_llm(name="install_go_package", description="install missing go package")(install_go_package)


# Register the tool function with the user proxy agent.
user_proxy.register_for_execution(name="save_file")(save_file)
user_proxy.register_for_execution(name="test_code")(test_code)
user_proxy.register_for_execution(name="install_go_package")(install_go_package)

speaker_transitions_dict = {
    user_proxy: [coder, unit_test_coder, assistant],
    assistant: [user_proxy],
    coder: [user_proxy, assistant],
    unit_test_coder: [user_proxy, assistant],
}

group_chat = autogen.GroupChat(
    agents=[user_proxy, coder, unit_test_coder, assistant], 
    messages=[], 
    max_round=70,
    allowed_or_disallowed_speaker_transitions=speaker_transitions_dict,
    speaker_transitions_type="allowed",
)
manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

# Start logging
logging_session_id = autogen.runtime_logging.start(config={"dbname": "logs.db"})
print("Logging session ID: " + str(logging_session_id))

objective = """
    Requirement: A function that takes 2 array of objects and detect change on those then output the change for auditing purpose. Assuming the object don't have any nested object.
    Example1:
        input:
            arr1 = [{"id": 1, "a": 1, "b": "2"}, {"id": 2, "a": 3, "b": "2"}]
            arr2 = [{"id": 1, "a": 0, "b": "2"}, {"id": 2, "a": 4, "b": "2"}]
        output:
            [
                {"id": 1, 
                    [{"property": "a", "action": "update", "old": "1", "new": "0"}]
                },
                {"id": 2, 
                    [{"property": "a", "action": "update", "old": "3", "new": "4"}]
                }
            ]
    Example2:
        input:
            arr1 = [{"id": 1, "a": 1, "b": "2"}, {"id": 2, "a": 3, "b": "2"}]
            arr2 = [{"id": 1, "a": 1, "b": "2"}, {"id": 3, "a": 3, "b": "2"}]
        output:
            [
                {"id": 3, 
                    [{"property": "a", "action": "create", "old": nil, "new": "3"}, 
                    {"property": "b", "action": "create", "old": nil, "new": "2"}]
                },
                {"id": 2, 
                    [{"property": "a", "action": "delete", "old": "3", "new": nil}, 
                    {"property": "b", "action": "delete", "old": "2", "new": nil}]
                }
            ]
    """

# def start_coding(recipient, messages, sender, config):
#     print("Start coding")
#     return f"{objective} \n\nStart writing code with unittest base on these test cases, then write the function. \n\n"\
#         f"{recipient.chat_messages_for_summary(sender)[-1]['content']} \n\n"\
        

# user_proxy.register_nested_chats(
#     [
#         {
#             "recipient": manager,
#             "message": start_coding,
#             "summary_method": "reflection_with_llm",
#             "max_turns": 1
#          }
#     ],
#     trigger=tester
# )

user_proxy.initiate_chats(
    [
        {"recipient":planner, "message":objective, "summary_method":"last_msg"},
        {"recipient":tester, "message":objective, "summary_method":"last_msg"},
        {"recipient":manager, "message": f"{objective}\n\nWriting golang unittest code base on the test cases, then write the function. Make sure to save every file before executing the code."},
    ]
)

autogen.runtime_logging.stop()