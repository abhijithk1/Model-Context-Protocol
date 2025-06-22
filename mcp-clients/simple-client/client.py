import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
# import json

async def main():
    url = "http://127.0.0.1:3003/mcp"
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # await session.initialize()            # JSON-RPC „initialize“
            response = await session.list_tools()
            tool_lists = response.tools
            for tool in tool_lists:
                print(f"{tool.name}: {tool.description}")
                # print(f"{json.dumps(tool.inputSchema, indent=2)}")
                # result = await session.call_tool(f"{tool.name}", {"a": 21, "b": 21})
                # print(f"{tool.name} result: ", result.content)

if __name__ == "__main__":
    asyncio.run(main())