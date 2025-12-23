using System.Text.Json;
using System.Text.Json.Nodes;
using ModelContextProtocol.Protocol;

namespace Po.Community.Core.Extensions;

public static class McpToolExtensions
{
    public static string? GetArgumentValueOrNull(
        this CallToolRequestParams context,
        string parameterName
    )
    {
        ArgumentNullException.ThrowIfNull(context.Arguments);

        return context.Arguments.TryGetValue(parameterName, out var element)
            ? element.GetString()
            : null;
    }

    public static string GetRequiredArgumentValue(
        this CallToolRequestParams context,
        string parameterName
    )
    {
        ArgumentNullException.ThrowIfNull(context.Arguments);

        var value = GetArgumentValueOrNull(context, parameterName);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException(
                $"The following parameter is required: {parameterName}"
            );
        }

        return value;
    }

    public static JsonElement ToInputSchema(this IMcpTool tool)
    {
        var requiredProps = new List<string>();
        var propertiesObj = new JsonObject();

        foreach (var argument in tool.Arguments)
        {
            if (argument.IsRequired)
            {
                requiredProps.Add(argument.Name);
            }

            var typeObj = new JsonObject { ["type"] = argument.IsArray ? "array" : argument.Type };
            if (argument.IsArray)
            {
                typeObj.Add("items", new JsonObject { ["type"] = argument.Type });
            }

            if (!string.IsNullOrWhiteSpace(argument.Description))
            {
                typeObj.Add("description", argument.Description);
            }

            propertiesObj.Add(argument.Name, typeObj);
        }

        var schema = new JsonObject { ["type"] = "object", ["properties"] = propertiesObj };
        if (requiredProps.Count > 0)
        {
            schema.Add("required", new JsonArray([.. requiredProps]));
        }

        return JsonSerializer.SerializeToElement(schema);
    }
}
