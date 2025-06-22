import httpx
from config import GATEWAY_URL

async def list_tools():
    async with httpx.AsyncClient() as client:
        res = await client.post(GATEWAY_URL, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        })
        return res.json()["result"]["tools"]

async def call_tool(tool_name, input_data):
    async with httpx.AsyncClient() as client:
        res = await client.post(GATEWAY_URL, json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": input_data
            }
        })
        return res.json()["result"]
