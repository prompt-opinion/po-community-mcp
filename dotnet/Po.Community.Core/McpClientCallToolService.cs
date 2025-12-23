using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Po.Community.Core.Utilities;

namespace Po.Community.Core;

public static class McpClientCallToolService
{
    public static async ValueTask<CallToolResult> Handler(
        RequestContext<CallToolRequestParams> context,
        CancellationToken cancellationToken
    )
    {
        if (context.Services is null)
        {
            return McpToolUtilities.CreateTextToolResponse(
                "An unexpected server error occurred. Services were not found.",
                isError: true
            );
        }

        if (context.Params is null)
        {
            return McpToolUtilities.CreateTextToolResponse(
                "An unexpected server error occurred. No tool parameters found.",
                isError: true
            );
        }

        var poMcpTools = context.Services.GetRequiredService<IEnumerable<IMcpTool>>();
        var contextAccessor = context.Services.GetRequiredService<IHttpContextAccessor>();
        var logger = context.Services.GetRequiredService<ILogger<IMcpTool>>();

        if (contextAccessor.HttpContext is null)
        {
            return McpToolUtilities.CreateTextToolResponse(
                "An unexpected server error occurred. The HTTP context could not be determined.",
                isError: true
            );
        }

        foreach (var poMcpTool in poMcpTools)
        {
            if (poMcpTool.Name != context.Params.Name)
            {
                continue;
            }

            try
            {
                return await poMcpTool.HandleAsync(
                    contextAccessor.HttpContext,
                    context.Server,
                    context.Services,
                    context.Params
                );
            }
            catch (Exception exception)
            {
                logger.LogError(
                    exception,
                    "An error occurred while executing tool: {ToolName}",
                    poMcpTool.Name
                );

                return McpToolUtilities.CreateTextToolResponse(
                    $"An internal exception occurred with message: {exception.Message}",
                    isError: true
                );
            }
        }

        return McpToolUtilities.CreateTextToolResponse(
            $"A tool handler was not found for the tool: {context.Params.Name}.",
            isError: true
        );
    }
}
