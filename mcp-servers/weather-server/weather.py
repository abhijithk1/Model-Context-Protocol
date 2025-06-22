from mcp.server.fastmcp import FastMCP
from typing import Dict

# Mock weather data for testing
MOCK_WEATHER_DATA: Dict[str, Dict] = {
    "new york": {"temperature": 20, "humidity": 65, "condition": "cloudy"},
    "london": {"temperature": 15, "humidity": 80, "condition": "rainy"},
    "tokyo": {"temperature": 25, "humidity": 70, "condition": "sunny"},
}

# Create an MCP server as a global variable
server = FastMCP("Weather Info Server", host="127.0.0.1", port=3002, stateless_http=True,)
print("settings: ", server.settings)
print("streamable app: ", server.streamable_http_app())

@server.tool()
def get_current_weather(city: str) -> Dict[str, str | int]:
    """Retrieve current weather data for a specified city.
    
    Args:
        city: Name of the city (e.g., 'New York', 'London').
    
    Returns:
        A dictionary containing temperature (Celsius), humidity (%), and condition.
        If the city is not found, returns an error message.
    """
    city = city.lower().strip()
    if city not in MOCK_WEATHER_DATA:
        return {"error": f"No weather data available for city '{city}'"}
    return MOCK_WEATHER_DATA[city]

@server.tool()
def get_temperature(city: str) -> int | str:
    """Retrieve the current temperature for a specified city.
    
    Args:
        city: Name of the city (e.g., 'New York', 'London').
    
    Returns:
        The temperature in Celsius, or an error message if the city is not found.
    """
    city = city.lower().strip()
    if city not in MOCK_WEATHER_DATA:
        return f"No temperature data available for city '{city}'"
    return MOCK_WEATHER_DATA[city]["temperature"]

if __name__ == "__main__":
    print("Starting Weather Info Server...")
    server.run(transport="streamable-http")
