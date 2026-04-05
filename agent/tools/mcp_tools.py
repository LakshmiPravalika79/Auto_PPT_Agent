"""
mcp_tools.py

Wrap MCP calls as LangChain tools
"""

def create_tool(session, tool_name):
    def tool_func(input_data=""):
        return session.call(tool_name, input_data)

    return tool_func