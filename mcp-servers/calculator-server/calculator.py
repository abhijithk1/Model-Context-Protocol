from mcp.server.fastmcp import FastMCP
# from fastapi import FastAPI, Request
# import contextlib
import logging

# Set up logging
logging.basicConfig(level=logging.inf)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP(name="Calculator Server", stateless_http=True, host="127.0.0.1", port=3001)
# mcp = FastMCP(name="CalculatorServer", stateless_http=True)

# Define calculator tools
@mcp.tool(description="Add two numbers")
def add(a: float, b: float) -> float:
    """Add two numbers and return the result."""
    return a + b

@mcp.tool(description="Subtract two numbers")
def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the result."""
    return a - b

@mcp.tool(description="Multiply two numbers")
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the result."""
    return a * b

@mcp.tool(description="Divide two numbers")
def divide(a: float, b: float) -> float:
    """Divide a by b and return the result. Raises error if b is zero."""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


# Create FastAPI app and mount MCP server
# app = FastAPI(redirect_slashes=False)

# # Define lifespan to manage MCP session
# @contextlib.asynccontextmanager
# async def lifespan(app: FastAPI):
#     async with contextlib.AsyncExitStack() as stack:
#         await stack.enter_async_context(mcp.session_manager.run())
#         yield

# app.lifespan = lifespan

# # Mount MCP server and log requests
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     logger.debug(f"Received request: {request.method} {request.url}")
#     response = await call_next(request)
#     logger.debug(f"Response status: {response.status_code}")
#     return response

# app.mount("/", mcp.streamable_http_app())

if __name__ == "__main__":
    print("Hello from Calculator Server!")
    # print("server settings: ", mcp.settings.model_dump_json())
    # print("server transport app: ", mcp.streamable_http_app())
    mcp.run(transport="streamable-http")
    # import uvicorn
    # uvicorn.run(app, host="127.0.0.1", port=3001)
    # uvicorn.run(mcp.streamable_http_app(), host="127.0.0.1", port=3001)
  
    