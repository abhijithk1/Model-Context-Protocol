from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = FastMCP("FileSystem Server", stateless_http=True, host="127.0.0.1", port=3003)

@server.tool()
def read_file(path: str) -> str:
    """Reads the content of a file at the given path."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except Exception as e:
        return f"An error occurred: {e}"

@server.tool()
def write_file(path: str, content: str) -> str:
    """Writes content to a file at the given path."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"An error occurred while writing: {e}"


if __name__ == "__main__":
    server.run(transport="streamable-http")
