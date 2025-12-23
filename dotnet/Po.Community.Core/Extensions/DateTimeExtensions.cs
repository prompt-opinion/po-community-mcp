namespace Po.Community.Core.Extensions;

public static class DateTimeExtensions
{
    public static int GetAge(this DateTimeOffset offset, TimeProvider? timeProvider = null)
    {
        var now = timeProvider?.GetUtcNow() ?? DateTimeOffset.UtcNow;
        var age = now.Year - offset.Year;
        if (offset > now.AddYears(-age))
        {
            age--;
        }

        return age;
    }
}
