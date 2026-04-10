import { z } from "zod";

const envSchema = z.object({
  PO_ENV: z.enum(["dev", "prod", "local"]).default("local"),
  PORT: z.coerce.number().default(5000),
  ALLOWED_HOST: z.string().optional(),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

export type Config = z.infer<typeof envSchema>;

export function loadConfig(): Config {
  const result = envSchema.safeParse(process.env);
  if (!result.success) {
    console.error(
      "Invalid environment configuration:",
      result.error.format(),
    );
    process.exit(1);
  }
  return result.data;
}

export function getAllowedHosts(config: Config): string[] {
  switch (config.PO_ENV) {
    case "dev":
      return ["ts.fhir-mcp.dev.promptopinion.ai"];
    case "prod":
      return ["ts.fhir-mcp.promptopinion.ai"];
    default: {
      const hosts = ["localhost"];
      if (config.ALLOWED_HOST) {
        hosts.push(config.ALLOWED_HOST);
      }
      return hosts;
    }
  }
}
