using Po.Community.Server;

const string corsPolicyName = "PromptOpinionCorsPolicy";

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder
    .Services.AddOpenApi()
    .AddMcpServices()
    .AddCors(options =>
    {
        options.AddPolicy(
            corsPolicyName,
            policy => policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()
        );
    });

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();
app.UseCors(corsPolicyName);
app.MapMcp("/mcp");
app.Run();
