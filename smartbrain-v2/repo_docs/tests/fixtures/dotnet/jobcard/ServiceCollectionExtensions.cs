// Fixture: trimmed reproduction of job-card-service
// src/Jobcard.Infrastructure/Extensions/ServiceCollectionExtensions.cs + JobCardDbContext + an
// IEntityTypeConfiguration and a Dapper stored-procedure repository.
using Dapper;
using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;

namespace Jobcard.Infrastructure.Extensions;

public static class ServiceCollectionExtensions
{
    public static void AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        var connectionString2 = Environment.GetEnvironmentVariable("JOBCARD_DB_CONNECTION");
        services.AddDbContext<JobCardDbContext>(options => options.UseSqlServer(connectionString2));
        services.AddDbContextFactory<JobCardDbContext>(options => options.UseSqlServer(connectionString2), ServiceLifetime.Scoped);
    }
}

public class JobCardDbContext : DbContext
{
    public DbSet<JobCard> JobCards { get; set; }
    public DbSet<Dealer> Dealers { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<JobCard>(entity => { entity.ToTable("MDMS_JOBCARD", "dbo"); });
    }
}

public class DealerEntityTypeConfiguration : IEntityTypeConfiguration<Dealer>
{
    public void Configure(EntityTypeBuilder<Dealer> builder)
    {
        builder.ToTable("MDMS_DEALER");
    }
}

public class JobCard { public long Id { get; set; } }
public class Dealer { public int DealerId { get; set; } }

public class LabourRepository
{
    private readonly IConfiguration _configuration;
    public LabourRepository(IConfiguration configuration) { _configuration = configuration; }

    public async Task<int> Issue(int id)
    {
        using var conn = new SqlConnection(_configuration.GetConnectionString("JobcardDb"));
        return await conn.ExecuteAsync("usp_issue_labour", new { id }, commandType: CommandType.StoredProcedure);
    }
}
