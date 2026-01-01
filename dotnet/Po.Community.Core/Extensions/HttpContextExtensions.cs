using Hl7.Fhir.Rest;
using Microsoft.AspNetCore.Http;
using Microsoft.IdentityModel.JsonWebTokens;
using Po.Community.Core.Models;

namespace Po.Community.Core.Extensions;

public static class HttpContextExtensions
{
    public static FhirContext? GetFhirContext(this HttpContext httpContext)
    {
        var headers = httpContext.Request.Headers;
        if (
            !headers.TryGetValue(SharpOnMcpConstants.FhirServerUrlHeaderName, out var url)
            || string.IsNullOrWhiteSpace(url)
        )
        {
            return null;
        }

        var token = headers[SharpOnMcpConstants.FhirAccessTokenHeaderName].ToString();
        if (string.IsNullOrWhiteSpace(token))
        {
            token = null;
        }

        return new FhirContext { Url = url!, Token = token };
    }

    public static string? GetPatientIdIfContextExists(this HttpContext httpContext)
    {
        var fhirToken = httpContext.Request.Headers[SharpOnMcpConstants.FhirAccessTokenHeaderName];
        if (!string.IsNullOrWhiteSpace(fhirToken))
        {
            var handler = new JsonWebTokenHandler();
            var jwtToken = handler.ReadJsonWebToken(fhirToken);
            var patientClaim = jwtToken.Claims.FirstOrDefault(x =>
                string.Equals("patient", x.Type, StringComparison.InvariantCultureIgnoreCase)
            );

            if (!string.IsNullOrWhiteSpace(patientClaim?.Value))
            {
                return patientClaim.Value;
            }
        }

        var headerValue = httpContext.Request.Headers[SharpOnMcpConstants.PatientIdHeaderName];
        return !string.IsNullOrWhiteSpace(headerValue) ? headerValue.ToString() : null;
    }

    public static FhirClient CreateFhirClientWithContext(this HttpContext httpContext)
    {
        var fhirContext = httpContext.GetFhirContext();
        if (fhirContext is null)
        {
            throw new InvalidOperationException("The fhir context could not be retrieved");
        }

        var settings = new FhirClientSettings { PreferredFormat = ResourceFormat.Json };
        return string.IsNullOrWhiteSpace(fhirContext.Token)
            ? new FhirClient(fhirContext.Url, settings)
            : new FhirClient(
                fhirContext.Url,
                settings,
                new FhirClientAuthMessageHandler(fhirContext.Token)
            );
    }
}
