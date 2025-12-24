import * as tools from "./tools";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp";
import { IMcpTool } from "./IMcpTool";
import cors from "cors";

const env = process.env["PO_ENV"]?.toString();
const allowedHosts: string[] = [];

switch (env) {
  case "dev":
    allowedHosts.push("ts.fhir-mcp.dev.promptopinion.ai");
    break;
  case "prod":
    allowedHosts.push("ts.fhir-mcp.promptopinion.ai");
    break;
  default:
    allowedHosts.push("localhost");
}

const app = createMcpExpressApp({
  host: "0.0.0.0",
  allowedHosts,
});

const port = process.env["PORT"] || 5000;

app.use(cors());

app.get("/hello-world", async (_, res) => {
  res.send("Hello World");
});

app.post("/mcp", async (req, res) => {
  try {
    const server = new McpServer(
      {
        name: "Typescript Template",
        version: "1.0.0",
      },
      {
        capabilities: {
          experimental: {
            fhir_context_required: {
              value: true,
            },
          },
        },
      },
    );

    for (const tool of Object.values<IMcpTool>(tools)) {
      tool.registerTool(server, req);
    }

    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
    });

    res.on("close", () => {
      console.log("Request closed");

      transport.close();
      server.close();
    });

    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.log("Error handling MCP request:", error);
    if (!res.headersSent) {
      res.status(500).json({
        jsonrpc: "2.0",
        error: {
          code: -32603,
          message: "Internal server error",
        },
        id: null,
      });
    }
  }
});

app.listen(port, () => {
  console.log(`MCP server listening on port ${port}`);
});
