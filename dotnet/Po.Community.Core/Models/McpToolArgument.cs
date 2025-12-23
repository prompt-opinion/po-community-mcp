namespace Po.Community.Core.Models;

public class McpToolArgument
{
    public bool IsArray { get; set; }

    public required string Name { get; set; }

    public required string Type { get; set; }

    public bool IsRequired { get; set; }

    public string? Description { get; set; }
}
