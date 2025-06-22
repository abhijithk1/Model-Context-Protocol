from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import asyncio
import json
import asyncio

CACHE_LOCK = asyncio.Lock()

# In a real-world scenario, this would be dynamic
SERVER_REGISTRY = {
    "calculator": "http://localhost:3001/mcp/",
    "weather": "http://localhost:3002/mcp/",
    "filesystem": "http://localhost:3003/mcp/"
}

# A cache to map a tool name to its server URL. This is populated on startup.
TOOL_TO_SERVER_CACHE = {}

# A cache to map a tool name to it's metadata
TOOL_METADATA_CACHE = {}  # tool_name → metadata dict

# This dictionary will hold our application's state, including the httpx client.
# This is the modern way to manage state in FastAPI.
lifespan_context = {}

async def periodic_tool_refresher(interval_seconds: int = 300):
    """Periodically refreshes the tool cache every `interval_seconds`."""
    while True:
        try:
            print("[Tool Refresher] Refreshing tool cache...")
            async with CACHE_LOCK:
                await populate_tool_cache()
        except Exception as e:
            print(f"[Tool Refresher] Error refreshing tools: {e}")
        
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run on startup ---
    # Create a single, long-lived AsyncClient. It will manage a connection pool internally.
    client_headers = {
        "Accept": 'application/json, text/event-stream',
        "Content-Type": 'application/json'
    }
    lifespan_context["http_client"] = httpx.AsyncClient(timeout=30.0, headers=client_headers)
    print("Gateway starting up: HTTP Client created.")
    
    # Populate the tool cache on startup
    async with CACHE_LOCK:
        await populate_tool_cache()
    
    # Start periodic refresher task
    app.state._refresh_task = asyncio.create_task(periodic_tool_refresher())
    
    yield  # The application is now running
    
    # --- Code to run on shutdown ---
    
    # Shutdown: cancel background task and close client
    app.state._refresh_task.cancel()
    try:
        await app.state._refresh_task
    except asyncio.CancelledError:
        pass
    
    # Gracefully close the client and its connections.
    await lifespan_context["http_client"].aclose()
    print("Gateway shutting down: HTTP Client closed.")


app = FastAPI(title="MCP Gateway", lifespan=lifespan)


def extract_json_body_from_response(res):
    raw = res.text
    if raw.startswith("event:"):
        # Extract the JSON from the data: line
        for line in raw.splitlines():
            if line.startswith("data:"):
                json_part = line.removeprefix("data:").strip()
                break
        else:
            raise ValueError("No data: line found in SSE response.")
        
        json_body = json.loads(json_part)
    else:
        # Normal JSON response
        json_body = res.json()
    
    return json_body


def build_error_response(message: str, error_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": error_id,
        "result": {
            "content": [
                {"type": "text", "text": message}
            ],
            "isError": True
        }
    }


async def populate_tool_cache():
    """Discovers tools from all registered servers and populates the cache."""
    global TOOL_TO_SERVER_CACHE
    global TOOL_METADATA_CACHE
    TOOL_TO_SERVER_CACHE.clear()
    TOOL_METADATA_CACHE.clear()
    
    client = lifespan_context["http_client"]
    discover_tasks = [
        client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        for name, url in SERVER_REGISTRY.items()
    ]
    
    results = await asyncio.gather(*discover_tasks, return_exceptions=True)

    for server_name, res in zip(SERVER_REGISTRY.keys(), results):
        if isinstance(res, httpx.Response) and res.status_code == 200:
            try:
                json_body = extract_json_body_from_response(res)
                
                tools = json_body["result"]["tools"]
                for tool in tools:
                    TOOL_TO_SERVER_CACHE[tool["name"]] = SERVER_REGISTRY[server_name]
                    TOOL_METADATA_CACHE[tool["name"]] = tool
            except (KeyError, IndexError, TypeError):
                print(f"Warning: Could not parse tools from server: {server_name}")
            except ValueError as e:
                print(f"Data response from {server_name} not found: {e}")
        else:
            print(f"Warning: Could not discover tools from server: {server_name}. Error: {res}")
            
    print("Tool cache populated:", TOOL_TO_SERVER_CACHE)


@app.post("/mcp")
async def mcp_gateway(request: Request):
    """The main gateway endpoint that routes MCP requests using the shared client."""
    client = lifespan_context["http_client"]
    
    try:
        body = await request.json()
        method = body.get("method")
        
        if method == "tools/list":
            return JSONResponse(
                status_code=200, 
                content={
                            "jsonrpc": "2.0",
                            "id": body.get("id"),
                            "result": {
                                    "tools": list(TOOL_METADATA_CACHE.values())
                                }
                        }
                )

        if method == "tools/call":
            tool_name = body.get("params", {}).get("name")
            if not tool_name:
                raise HTTPException(status_code=400, detail="Tool name not provided in MCP tools/call")

            server_url = TOOL_TO_SERVER_CACHE.get(tool_name)
            if not server_url:
                return JSONResponse(status_code=404, content=build_error_response(f"Tool '{tool_name}' not found.", body.get("id")))

            print(f"Tool {tool_name} is present in the server {server_url}")
            # Proxy the request to the identified server using the shared client
            proxy_response = await client.post(server_url, json=body)
            json_response = extract_json_body_from_response(proxy_response)
            proxy_response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return JSONResponse(content=json_response, status_code=proxy_response.status_code)
    
        else:
            # For a production gateway, you might want to proxy other valid MCP methods too
            raise HTTPException(status_code=400, detail="Unsupported MCP method: {method}")

    except httpx.HTTPStatusError as e:
         return JSONResponse(content={"jsonrpc": "2.0", "error": {"code": -32000, "message": f"Upstream server error: {e}"}, "id": body.get("id")}, status_code=e.response.status_code)
    except Exception as e:
        return JSONResponse(content={"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}, status_code=500)


if __name__ == "__main__":
    print("Hello from MCP Gateway!")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
