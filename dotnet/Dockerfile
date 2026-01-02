FROM mcr.microsoft.com/dotnet/sdk:10.0 as build
WORKDIR /app

COPY ./dotnet ./
RUN dotnet restore
RUN dotnet publish -c Release -o out

FROM mcr.microsoft.com/dotnet/aspnet:10.0
WORKDIR /app
COPY --from=build /app/out ./

ENV ASPNETCORE_ENVIRONMENT LocalDocker
ENTRYPOINT ["dotnet", "Po.Community.Server.dll"]
