using System.Text.Json.Nodes;
using ModelContextProtocol.Protocol;
using Po.Community.Core;

namespace Po.Community.Server;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddMcpServices(this IServiceCollection services)
    {
        services
            .AddMcpServer(options =>
            {
                options.Capabilities ??= new ServerCapabilities();
                options.Capabilities.Experimental ??= new Dictionary<string, object>();
                options.Capabilities.Experimental.Add(
                    "fhir_context_required",
                    new JsonObject { ["value"] = true }
                );
            })
            .WithHttpTransport()
            .WithListToolsHandler(McpClientListToolsService.Handler)
            .WithCallToolHandler(McpClientCallToolService.Handler);

        var mcpToolTypes = new List<Type>();
        foreach (var type in typeof(IMcpTool).Assembly.GetTypes())
        {
            if (type.IsInterface || type.IsAbstract)
            {
                continue;
            }

            if (type.IsAssignableTo(typeof(IMcpTool)))
            {
                mcpToolTypes.Add(type);
            }
        }

        foreach (var mcpToolType in mcpToolTypes)
        {
            services.AddScoped(typeof(IMcpTool), mcpToolType);
        }

        return services;
    }
}
