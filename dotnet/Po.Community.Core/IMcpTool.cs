using Microsoft.AspNetCore.Http;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Po.Community.Core.Models;

namespace Po.Community.Core;

public interface IMcpTool
{
    string Name { get; }

    string? Description { get; }

    List<McpToolArgument> Arguments { get; }

    Task<CallToolResult> HandleAsync(
        HttpContext httpContext,
        McpServer mcpServer,
        IServiceProvider serviceProvider,
        CallToolRequestParams context
    );
}
