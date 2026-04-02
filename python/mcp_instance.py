from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Python Template", stateless_http=True, host="0.0.0.0")

_original_get_capabilities = mcp._mcp_server.get_capabilities

def _patched_get_capabilities(notification_options, experimental_capabilities):
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {"ai.promptopinion/fhir-context": {}}
    return caps

mcp._mcp_server.get_capabilities = _patched_get_capabilities
