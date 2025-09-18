import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    server_params = StdioServerParameters(
        command="C:\\Python313\\python.exe",
        args=["C:\\Users\\Cristian\\Downloads\\Projectscrape\\memory_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("TOOLS:", [tool.name for tool in tools.tools])

            # Call echo tool
            result = await session.call_tool("echo", {"text": "hello"})
            print("ECHO:", result.content[0].text)

            # Call memory_upsert
            result = await session.call_tool("memory_upsert", {"key": "foo", "value": "bar"})
            print("UPSERT:", result.content[0].text)

            # Call memory_get
            result = await session.call_tool("memory_get", {"key": "foo"})
            print("GET:", result.content[0].text)

            # List all memory
            result = await session.call_tool("memory_list", {})
            print("LIST:", result.content[0].text)


if __name__ == "__main__":
    anyio.run(main)
