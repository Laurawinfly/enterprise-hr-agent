"""MCP client adapter. MCP SDK is imported lazily so local mode stays independent."""
class HRMCPClient:
    def __init__(self, url):
        self.url = url

    async def list_tools(self):
        from mcp import Client
        async with Client(self.url) as client:
            result = await client.list_tools()
            return [{"name": t.name, "description": t.description or "", "inputSchema": t.inputSchema}
                    for t in result.tools]

    async def call_tool(self, name, arguments):
        from mcp import Client
        async with Client(self.url) as client:
            result = await client.call_tool(name, arguments)
            if result.structured_content is not None:
                return result.structured_content
            for block in result.content or []:
                value = getattr(block, "text", None)
                if value:
                    return {"content": value}
            return {}
