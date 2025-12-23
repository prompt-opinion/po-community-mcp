using System.Diagnostics.CodeAnalysis;

namespace Po.Community.Core.Extensions;

public static class ObjectExtensions
{
    public static T GetOrThrowIfNull<T>([NotNull] this T? value)
    {
        return value
            ?? throw new InvalidOperationException(
                "Null found for value when non-null value expected"
            );
    }
}
