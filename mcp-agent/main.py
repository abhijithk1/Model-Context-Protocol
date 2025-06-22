# main.py

import asyncio
from langgraph.graph import StateGraph, END
from planner import plan
from executor import call_tool

async def planner_node(state):
    tool_name, input_data = await plan(state["user_input"])
    return {"tool_name": tool_name, "input_data": input_data}

async def executor_node(state):
    result = await call_tool(state["tool_name"], state["input_data"])
    return {"output": result}

def create_graph():
    builder = StateGraph()
    
    builder.add_node("plan", planner_node)
    builder.add_node("execute", executor_node)

    builder.set_entry_point("plan")
    builder.add_edge("plan", "execute")
    builder.add_edge("execute", END)

    return builder.compile()

async def run_agent(user_query):
    graph = create_graph()
    result = await graph.invoke({"user_input": user_query})
    print("Final Output:", result["output"])

if __name__ == "__main__":
    user_prompt = input("Ask something: ")
    asyncio.run(run_agent(user_prompt))
