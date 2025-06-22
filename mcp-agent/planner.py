from langchain.prompts import ChatPromptTemplate
from executor import list_tools
import json
from jsonschema import validate, ValidationError
import re

from llm import llm

prompt = ChatPromptTemplate.from_template("""
You are an AI agent tasked with selecting the correct tool from a list of available tools and mapping a user query to the tool's input schema. The tools are provided in a JSON format, including tool names, descriptions, and input schemas. Your goal is to:

1. Analyze the user query to identify the intended task.
2. Select the most appropriate tool based on the query's intent and the tool's description.
3. Extract relevant parameters from the query and map them to the tool's input schema, ensuring the output is a valid JSON object conforming to the schema.
4. If no suitable tool is found or the query is ambiguous, return an error message.

**Tools List:**
{tools_json}

**User Query:**
{user_query}

**Instructions:**
- Carefully read the user query to understand the task.
- Match the query to a tool by comparing the query's intent to the tool descriptions. Use keywords, context, and semantic understanding to make the best match.
- For the selected tool, extract the required parameters from the query to populate the input schema. Ensure the parameter types (e.g., number, string) match the schema.
- If the query contains insufficient information for the required parameters, infer reasonable defaults or return an error if defaults are not possible.
- Output a JSON object with the following structure:
  ```json
  {{
    "name": "<tool_name>",
    "arguments": <input_schema_filled>
  }}
  ```
- If no tool matches or the query is invalid, output:
  ```json
  {{
    "error": "<error_message>"
  }}
  ``` 

**Output:**
Return the JSON object as a single, valid JSON string.
""")

async def plan(user_query):
    tools = await list_tools()
    if not tools:
      raise ValueError("No tools available.")
    tools_json = json.dumps(tools)

    # Create the chain
    chain = prompt | llm
    
    # Invoke LLM with query and tools
    response = await chain.ainvoke({
        "user_query": user_query,
        "tools_json": tools_json
    })
    
    # Strip Markdown and extract JSON
    content = response.content.strip()
    
    # Remove json and delimiters using regex
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, content, re.DOTALL)
    if not match:
      raise ValueError(f"LLM response does not contain valid JSON in Markdown code block: {content}")

    json_str = match.group(1).strip()    
      
    try:
      tool_call = json.loads(json_str)
      print(f"tool call: {tool_call}")
    except json.JSONDecodeError:
      raise ValueError(f"LLM response is not valid JSON: {response.content}")
    
    # Handle error response
    if "error" in tool_call:
      raise ValueError(f"LLM returned an error: {tool_call['error']}")
    
    # Validate response structure
    if not isinstance(tool_call, dict) or "name" not in tool_call or "arguments" not in tool_call:
      raise ValueError("LLM response missing required fields: 'name' and 'arguments'.")

    tool_name = tool_call["name"]
    arguments = tool_call["arguments"]
    
    # Verify tool exists
    selected_tool = next((tool for tool in tools if tool["name"] == tool_name), None)
    if not selected_tool:
      raise ValueError(f"Selected tool '{tool_name}' not found in tools list.")
    
    # Validate arguments against tool's input schema
    try:
      validate(instance=arguments, schema=selected_tool["inputSchema"])
    except ValidationError as e:
      raise ValueError(f"Arguments do not match tool schema: {e.message}")
  
    return tool_name, arguments