import asyncio
from langgraph.graph import StateGraph, END
from planner import plan
from executor import call_tool
from typing import TypedDict, Optional
import logging


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the state schema
class AgentState(TypedDict):
    user_query: str
    tool_name: Optional[str]
    arguments: Optional[dict]
    output: Optional[any]

async def planner_node(state: AgentState) -> AgentState:
    logger.debug(f"Entering planner_node with state: {state}")
    try:
        tool_name, arguments = await plan(state["user_query"])
        logger.debug(f"Planner selected tool: {tool_name}, arguments: {arguments}")
        return {"tool_name": tool_name, "arguments": arguments}
    except Exception as e:
        logger.error(f"Planner node failed: {str(e)}")
        return {"output": {"error": f"Planning failed: {str(e)}"}, "tool_name": None, "arguments": None}

async def executor_node(state: AgentState) -> AgentState:
    logger.debug(f"Entering executor_node with state: {state}")
    try:
        if state.get("output") and isinstance(state["output"], dict) and "error" in state["output"]:
            logger.debug("Skipping execution due to planner error")
            return state  # Skip execution if planner set an error
        if not state.get("tool_name") or not state.get("arguments"):
            logger.error("Invalid tool or arguments from planner")
            return {"output": {"error": "Invalid tool or arguments from planner"}}
        response = await call_tool(state["tool_name"], state["arguments"])
        
        logger.debug(f"Executor response: {response}")
        
        isError = response["isError"]
        contents = response["content"]
        if isError:
            return {"output": {"error": contents[0]["text"]}}
        
        results = [content.get("text", "") for content in contents]
        
        return {"output": "".join(results)}
    except Exception as e:
        logger.error(f"Executor node failed: {str(e)}")
        return {"output": {"error": f"Execution failed: {str(e)}"}}

def create_graph():
    # Initialize StateGraph with state schema
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("plan", planner_node)
    builder.add_node("execute", executor_node)

    # Set entry point and edges
    builder.set_entry_point("plan")
    builder.add_edge("plan", "execute")
    builder.add_edge("execute", END)

    graph = builder.compile()
    logger.debug(f"Graph compiled with nodes: {list(graph.nodes.keys())}")
    return graph

async def run_agent(user_query: str):
    if not user_query.strip():
        print("Error: Empty query provided")
        return

    graph = create_graph()
    try:
        result = await graph.ainvoke({"user_query": user_query})
        output = result.get("output")
        if output is None:
            print("Error: No output produced")
        elif isinstance(output, dict) and "error" in output:
            print(f"Error: {output['error']}")
        else:
            print("Final Output:", output)
    except Exception as e:
        print(f"Error: Agent execution failed: {str(e)}")

async def main():
    while True:
        try:
            user_prompt = input("\n\nAsk something (or type 'exit' to quit): ")
            if user_prompt.lower() == "exit":
                print("Exiting...")
                break
            await run_agent(user_prompt)
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())