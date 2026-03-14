from abc import ABC, abstractmethod

from mcp.server.fastmcp import FastMCP


class IMcpTool(ABC):
    @abstractmethod
    def register_tool(self, mcp: FastMCP) -> None: ...
