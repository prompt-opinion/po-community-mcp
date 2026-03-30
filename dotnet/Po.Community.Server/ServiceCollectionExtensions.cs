using System.Text.Json.Nodes;
using ModelContextProtocol.Protocol;
using Po.Community.Core;

namespace Po.Community.Server;

public static class ServiceCollectionExtensions
{
    private const string FhirContextExtensionName = "ai.promptopinion/fhir-context";

    public static IServiceCollection AddMcpServices(this IServiceCollection services)
    {
        services
            .AddMcpServer(options =>
            {
                options.Capabilities ??= new ServerCapabilities();

#pragma warning disable MCPEXP001
                options.Capabilities.Extensions ??= new Dictionary<string, object>();
                options.Capabilities.Extensions.Add(FhirContextExtensionName, new JsonObject());
#pragma warning restore MCPEXP001
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
