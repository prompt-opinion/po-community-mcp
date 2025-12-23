using Hl7.Fhir.Model;
using Hl7.Fhir.Rest;
using Microsoft.AspNetCore.Http;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Po.Community.Core.Extensions;
using Po.Community.Core.Models;
using Po.Community.Core.Utilities;

namespace Po.Community.Core.McpTools;

public class PatientIdTool : IMcpTool
{
    private const string FirstNameParameter = "firstName";
    private const string LastNameParameter = "lastName";

    public string Name { get; } = "FindPatientId";

    public string? Description { get; } = "Finds a patient id given a first name and last name";

    public List<McpToolArgument> Arguments { get; } =
    [
        new McpToolArgument
        {
            Type = "string",
            Name = FirstNameParameter,
            Description = "The patient's first name",
            IsRequired = true,
        },
        new McpToolArgument
        {
            Type = "string",
            Name = LastNameParameter,
            Description = "The patient's last name. This is optional",
            IsRequired = false,
        },
    ];

    public async Task<CallToolResult> HandleAsync(
        HttpContext httpContext,
        McpServer mcpServer,
        IServiceProvider serviceProvider,
        CallToolRequestParams context
    )
    {
        var firstName = context.GetRequiredArgumentValue(FirstNameParameter);
        var lastName = context.GetArgumentValueOrNull(LastNameParameter);

        var fhirClient = httpContext.CreateFhirClientWithContext();

        var (firstError, firstPatient) = await SearchPatientAsync(fhirClient, firstName, lastName);
        if (firstError is not null)
        {
            return firstError;
        }

        if (firstPatient is not null)
        {
            return McpToolUtilities.CreateTextToolResponse(firstPatient.Id.GetOrThrowIfNull());
        }

        var (secondError, secondPatient) = await SearchPatientAsync(
            fhirClient,
            lastName,
            firstName
        );

        if (secondError is not null)
        {
            return secondError;
        }

        return secondPatient is not null
            ? McpToolUtilities.CreateTextToolResponse(secondPatient.Id.GetOrThrowIfNull())
            : McpToolUtilities.CreateTextToolResponse(
                "No patient could be found with that name",
                isError: true
            );
    }

    private async Task<(CallToolResult? errorResponse, Patient? patient)> SearchPatientAsync(
        FhirClient fhirClient,
        string? firstName,
        string? lastName
    )
    {
        var parameters = new List<string>();
        if (!string.IsNullOrWhiteSpace(firstName))
        {
            parameters.Add($"given={firstName}");
        }

        if (!string.IsNullOrWhiteSpace(lastName))
        {
            parameters.Add($"family={lastName}");
        }

        var response = await fhirClient.SearchAsync<Patient>([.. parameters]);
        if (
            response?.Entry is not { Count: > 0 }
            || response.Entry[0].Resource is not Patient patient
        )
        {
            return (null, null);
        }

        if (response.Entry.Count > 1)
        {
            return (
                McpToolUtilities.CreateTextToolResponse(
                    "More than one patient found. Provide additional details.",
                    isError: true
                ),
                null
            );
        }

        return (null, patient);
    }
}
