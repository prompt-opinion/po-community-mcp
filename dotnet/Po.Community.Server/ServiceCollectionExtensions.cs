using System.Text.Json;
using System.Text.Json.Serialization;
using ModelContextProtocol.Protocol;
using Po.Community.Core;
using Po.Community.Core.Extensions;
using Po.Community.Core.Models;

namespace Po.Community.Server;

public static class ServiceCollectionExtensions
{
    private const string FhirContextExtensionName = "ai.promptopinion/fhir-context";
    private static readonly JsonSerializerOptions SerializerOptions = new JsonSerializerOptions
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public static IServiceCollection AddMcpServices(this IServiceCollection services)
    {
        services
            .AddMcpServer(options =>
            {
                var extensionModel = new FhirContextExtensionModel
                {
                    Scopes =
                    [
                        new FhirContextExtensionModelScope("patient/Patient.rs", required: true),
                        new FhirContextExtensionModelScope("offline_access"),
                        new FhirContextExtensionModelScope("patient/Observation.rs"),
                        new FhirContextExtensionModelScope("patient/MedicationStatement.rs"),
                        new FhirContextExtensionModelScope("patient/Condition.rs"),
                    ],
                };

                options.Capabilities ??= new ServerCapabilities();

#pragma warning disable MCPEXP001
                options.Capabilities.Extensions ??= new Dictionary<string, object>();
                options.Capabilities.Extensions.Add(
                    FhirContextExtensionName,
                    JsonSerializer
                        .SerializeToNode(extensionModel, SerializerOptions)
                        .GetOrThrowIfNull()
                        .AsObject()
                );
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
