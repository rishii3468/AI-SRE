# PostgreSQL Timeout Runbook

## Symptoms

* Database timeout errors in application logs
* Slow query execution times
* Increased API latency and request failures
* HTTP 500/502/503 errors caused by database operations
* Database connection pool exhaustion
* Transaction timeouts
* Elevated query queue lengths
* Customer-facing functionality degraded or unavailable

## Root Causes

1. **Connection Pool Exhaustion**

   * Application opens more connections than available
   * Connection leaks preventing reuse
   * Traffic surge consuming all pool slots
   * Misconfigured pool limits

2. **Long-Running Queries**

   * Expensive joins or aggregations
   * Missing indexes
   * Full table scans
   * Reporting or batch workloads

3. **Database Overload**

   * CPU saturation
   * Memory pressure
   * High transaction volume
   * Excessive concurrent queries

4. **Lock Contention**

   * Blocked transactions
   * Row-level locking conflicts
   * Deadlocks
   * Long-running write transactions

5. **Resource Constraints**

   * Insufficient database instance size
   * Storage I/O bottlenecks
   * Memory shortages
   * Network latency

6. **Query Plan Regression**

   * Poor optimizer decisions
   * Outdated statistics
   * Recent schema changes
   * Unexpected execution plans

7. **Infrastructure Issues**

   * Storage subsystem degradation
   * Replica lag causing failover issues
   * Cloud provider performance problems
   * Network interruptions

## Detection Steps

1. Check application logs:

   Search for:

   * `connection timeout`
   * `query timeout`
   * `could not obtain connection`
   * `statement timeout exceeded`

2. Review PostgreSQL activity:

   ```sql
   SELECT pid,
          usename,
          state,
          query_start,
          now() - query_start AS duration,
          query
   FROM pg_stat_activity
   WHERE state != 'idle';
   ```

   Look for:

   * Long-running queries
   * Blocked sessions
   * Excessive active connections

3. Check database metrics:

   * CPU utilization
   * Memory utilization
   * Active connections
   * Query latency
   * Transaction rate

4. Identify blocking queries:

   ```sql
   SELECT blocking_pid,
          blocked_pid
   FROM pg_blocking_pids(pid);
   ```

5. Review slow query logs:

   * Frequently executed slow queries
   * High-cost execution plans
   * Full table scans

6. Verify connection pool health:

   * Pool utilization percentage
   * Waiting connection count
   * Connection acquisition latency

## Immediate Mitigation

1. **Identify and Kill Blocking Queries**

   Review active sessions:

   ```sql
   SELECT pid, query, now() - query_start
   FROM pg_stat_activity;
   ```

   Terminate problematic queries:

   ```sql
   SELECT pg_terminate_backend(<pid>);
   ```

2. **Increase Connection Pool Size**

   * Temporarily expand pool capacity
   * Reduce connection acquisition failures
   * Monitor database resource utilization

3. **Scale Database Resources**

   * Increase CPU and memory
   * Add read replicas
   * Upgrade database instance class

4. **Reduce Application Load**

   * Enable rate limiting
   * Pause non-critical background jobs
   * Disable expensive reports or analytics

5. **Route Reads to Replicas**

   * Reduce primary database load
   * Separate read and write workloads

6. **Optimize Critical Queries**

   * Add emergency indexes
   * Reduce query scope
   * Limit result set sizes

## Long-term Resolution

1. **Query Optimization**

   * Review slow queries regularly
   * Optimize joins and aggregations
   * Eliminate unnecessary database calls

2. **Index Management**

   * Add missing indexes
   * Remove unused indexes
   * Monitor index effectiveness

3. **Connection Pool Improvements**

   * Tune pool size appropriately
   * Detect connection leaks
   * Implement connection recycling

4. **Database Scaling Strategy**

   * Read replicas
   * Partitioning
   * Sharding where appropriate
   * Capacity planning

5. **Lock Contention Reduction**

   * Shorten transaction duration
   * Optimize update patterns
   * Standardize lock acquisition order

6. **Monitoring & Alerting**

   * Alert on connection pool utilization >80%
   * Alert on query latency spikes
   * Monitor active connection counts
   * Track blocking query frequency

7. **Performance Testing**

   * Load testing before releases
   * Query benchmark validation
   * Capacity forecasting

## Escalation

* If API error rates exceed SLA thresholds: page service owner
* If database CPU remains above 90% for more than 10 minutes: page database owner
* If connection pool exhaustion persists after mitigation: escalate to database team
* If critical business workflows are impacted: declare incident
* If database scaling or failover is required: engage platform engineering

## Success Criteria

* Database timeout errors return to baseline
* Query latency normalizes
* Connection pool utilization stabilizes
* No blocked or runaway queries remain
* API response times recover
* Error rates return to normal levels
* Database resource utilization remains healthy
* No timeout-related alerts observed for 30 minutes
