using ModelContextProtocol.Protocol;

namespace Po.Community.Core.Utilities;

public static class McpToolUtilities
{
    public static CallToolResult CreateTextToolResponse(string text, bool isError = false)
    {
        return new CallToolResult
        {
            Content = [new TextContentBlock { Text = text }],
            IsError = isError,
        };
    }

    public static CallToolResult CreateTextToolResponse(
        IEnumerable<string> texts,
        bool isError = false
    )
    {
        return new CallToolResult
        {
            Content = texts
                .Select(x => new TextContentBlock { Text = x })
                .Cast<ContentBlock>()
                .ToList(),
            IsError = isError,
        };
    }
}
