# Contributing DotNet Tools

## Overview

You can contribute to the default dotnet MCP server in this directory. Contribution
is limited to creating tools in the `/DarenaHealth.Community.McpTools` project and modifications
outside of this project are not allowed.

If you require more control over your MCP server with your own nuget packages and
your own programming rules, consider [creating your own MCP server](../servers) instead
of contributing to the default MCP server.

## Restrictions

- In the `/DarenaHealth.Community.McpTools` project, create a directory that represents
  you as an individual or an organization. For example `/DarenaHealth.Community.McpTools/DarenaSolutions`.
  - Follow c# conventions and ensure this directory is pascal-cased.
- Add your tools and any additional code that your tool requires to run.
- All MCP tools in the directory must implement the `IMcpTool` interface located
  in `DarenaHealth.Community.Mcp.Core`.

### Registering MCP Tools

After you have created your tools, you will need to update the top level `/DarenaHealth.Community.McpTools/ServiceCollectionExtensions.cs` file so that the tool can be registered.

In the file, create a new private extension method. This method must begin with
`Add` and end with `McpTool` or `McpTools`. This method should register all your
tools and dependent services. Finally, update the public extension method `AddMcpTools`
so that it calls your private extension.

Your tools should not be registered as a singleton.

Here is an example:

```csharp
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddMcpTools(this IServiceCollection services)
    {
        return services.AddPatientAgeMcpTool();
    }

    private static IServiceCollection AddPatientAgeMcpTool(this IServiceCollection services)
    {
        return services
            .AddSingleton<IPatientSearchService, PatientSearchService>()
            .AddScoped<IMcpTool, PatientAgeTool>();
    }
}
```

This method above registers a scoped MCP tool and registers an `IPatientSearchService`
service.

### Formatting

This repository uses [csharpier](https://csharpier.com/) for formatting. Set this
up in your IDE and ensure your code is formatted before creating a PR.

### Package Dependencies

You are limited to the packages listed in `/DarenaHealth.Community.McpTools//DarenaHealth.Community.McpTools.csproj`
and you cannot install additional packages. If you require an additional package
that is not listed there, contact us and we will review the package and make a determination.

[Creating your own MCP server](../servers) is also an option which does not have
this limitation.

## Pull Requests

Once you are ready with your project, you can create a PR to the main branch. Several
github workflows will begin ensuring that your submission follows the restrictions.
A Darena Solutions maintainer will review your PR. Once any comments or changes
have been resolved and the PR has been approved, you may merge your changes.
