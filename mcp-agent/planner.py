from langchain.prompts import ChatPromptTemplate
from executor import list_tools

from llm import llm

prompt = ChatPromptTemplate.from_template("""
You are a tool selection assistant. The user said: "{user_input}"

Available tools:
{tool_list}

Select the most appropriate tool name and the input parameters as a JSON object.

Format your response as:
Tool: <tool_name>
Input: <json input>
""")

async def plan(user_input):
    tools = await list_tools()
    tool_list_str = "\n".join(
        f"- {tool['name']}: {tool['description']}" for tool in tools
    )

    chain = prompt | llm
    response = await chain.ainvoke({
        "user_input": user_input,
        "tool_list": tool_list_str
    })

    lines = response.content.strip().splitlines()
    tool_line = next(line for line in lines if line.startswith("Tool:"))
    input_line = next(line for line in lines if line.startswith("Input:"))

    tool_name = tool_line.replace("Tool:", "").strip()
    input_json = eval(input_line.replace("Input:", "").strip())  # TODO: use json.loads safely

    return tool_name, input_json
