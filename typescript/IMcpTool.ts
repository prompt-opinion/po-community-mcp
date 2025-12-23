import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { Request } from "express";

export interface IMcpTool {
  registerTool: (server: McpServer, req: Request) => void;
}
