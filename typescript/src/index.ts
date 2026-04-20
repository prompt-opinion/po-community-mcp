import "dotenv/config";
import { loadConfig } from "./config";
import { logger } from "./logger";
import { createServer } from "./server";

const config = loadConfig();
logger.configure(config);

const app = createServer(config);

app.listen(config.PORT, () => {
  logger.info(`MCP server listening on port ${config.PORT}`, {
    env: config.PO_ENV,
    port: config.PORT,
  });
});
