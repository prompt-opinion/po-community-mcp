using Hl7.Fhir.Model;
using Microsoft.AspNetCore.Http;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;
using Po.Community.Core.Extensions;
using Po.Community.Core.Models;
using Po.Community.Core.Utilities;

namespace Po.Community.Core.McpTools;

public class PatientAgeTool : IMcpTool
{
    private const string PatientIdParameter = "patientId";

    public string Name { get; } = "GetPatientAge";

    public string? Description { get; } = "Gets the age of a patient.";

    public List<McpToolArgument> Arguments { get; } =
    [
        new McpToolArgument
        {
            Type = "string",
            Name = PatientIdParameter,
            Description =
                "The id of the patient. This is optional if patient context already exists",
            IsRequired = false,
        },
    ];

    public List<string> FhirScopes { get; } = ["patient/Patient.read"];

    public async Task<CallToolResult> HandleAsync(
        HttpContext httpContext,
        McpServer mcpServer,
        IServiceProvider serviceProvider,
        CallToolRequestParams context
    )
    {
        var patientId = httpContext.GetPatientIdIfContextExists();
        if (string.IsNullOrWhiteSpace(patientId))
        {
            patientId = context.GetRequiredArgumentValue(PatientIdParameter);
        }

        var fhirClient = httpContext.CreateFhirClientWithContext();
        var patient = await fhirClient.ReadAsync<Patient>($"Patient/{patientId}");

        if (patient is null)
        {
            return McpToolUtilities.CreateTextToolResponse(
                "The patient could not be found.",
                isError: true
            );
        }

        var patientDob = patient.BirthDateElement?.ToSystemDate();
        if (patientDob?.Years is null)
        {
            return McpToolUtilities.CreateTextToolResponse(
                "This patient does not have a birth date set or no year information is present.",
                isError: true
            );
        }

        return McpToolUtilities.CreateTextToolResponse(
            $"The patient's age is: {patientDob.ToDateTimeOffset(TimeSpan.Zero).GetAge()}"
        );
    }
}
