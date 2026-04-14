namespace Po.Community.Core.Models;

public class FhirContextExtensionModel
{
    public List<FhirContextExtensionModelScope> Scopes { get; set; } = [];
}

public class FhirContextExtensionModelScope(string name, bool? required = null)
{
    public string Name { get; set; } = name;

    public bool? Required { get; set; } = required;
}
