using Po.Community.Core;

namespace Po.Community.Server;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddMcpServices(this IServiceCollection services)
    {
        services
            .AddMcpServer()
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
