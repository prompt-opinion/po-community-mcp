import { McpServer } from "@modelcontextprotocol/sdk/server/mcp";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp";
import cors from "cors";
import { Config, getAllowedHosts } from "./config";
import { logger } from "./logger";
import * as tools from "./tools";
import { IMcpTool } from "./mcp/tool.interface";

export function createServer(config: Config) {
  const allowedHosts = getAllowedHosts(config);

  const app = createMcpExpressApp({
    host: "0.0.0.0",
    allowedHosts,
  });

  app.use(cors());

  app.get("/health", (_, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
  });

  app.post("/mcp", async (req, res) => {
    logger.info("Incoming MCP request", {
      fhirServerUrl:
        req.headers["x-fhir-server-url"]?.toString() ?? "(not set)",
      hasFhirToken: !!req.headers["x-fhir-access-token"],
      hasPatientId: !!req.headers["x-patient-id"],
    });

    try {
      const server = new McpServer(
        { name: "DischargePlus", version: "1.0.0" },
        {
          capabilities: {
            extensions: {
              "ai.promptopinion/fhir-context": {},
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
        transport.close();
        server.close();
      });

      await server.connect(transport);
      await transport.handleRequest(req, res, req.body);
    } catch (error) {
      logger.error("Error handling MCP request", {
        error: error instanceof Error ? error.message : String(error),
      });

      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  });

  return app;
}
