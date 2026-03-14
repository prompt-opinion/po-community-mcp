from mcp.server.fastmcp import FastMCP
from mcp.types import ServerCapabilities

mcp = FastMCP("Python Template", stateless_http=True, host="0.0.0.0")
mcp._mcp_server.experimental.update_capabilities(
    ServerCapabilities(experimental={"fhir_context_required": {"value": True}})
)
