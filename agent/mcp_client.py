from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys


async def connect_mcp(script_path):

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[script_path]
    )

    async with stdio_client(server_params) as (read, write):

        session = ClientSession(read, write)
        await session.initialize()

        return session