using Microsoft.Extensions.DependencyInjection;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Po.Community.Core.Extensions;

namespace Po.Community.Core;

public static class McpClientListToolsService
{
    public static ValueTask<ListToolsResult> Handler(
        RequestContext<ListToolsRequestParams> context,
        CancellationToken cancellation
    )
    {
        ArgumentNullException.ThrowIfNull(context.Services);

        var poMcpTools = context.Services.GetRequiredService<IEnumerable<IMcpTool>>();
        var responseTools = poMcpTools
            .Select(x => new Tool
            {
                Name = x.Name,
                Description = x.Description,
                InputSchema = x.ToInputSchema(),
            })
            .ToList();

        return ValueTask.FromResult(new ListToolsResult { Tools = responseTools });
    }
}
