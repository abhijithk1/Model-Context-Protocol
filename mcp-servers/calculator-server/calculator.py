from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP(name="Calculator Server", stateless_http=True, host="127.0.0.1", port=3001)

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


if __name__ == "__main__":
    print("Hello from Calculator Server!")
    mcp.run(transport="streamable-http")
  
    