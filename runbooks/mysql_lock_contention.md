# MySQL Lock Contention Runbook

## Symptoms

* Database queries hang or take significantly longer than normal
* Transaction timeouts increase
* Application requests waiting on database operations
* Elevated API latency tied to database interactions
* Increased database connection pool utilization
* Slow query count rises unexpectedly
* Deadlock errors appearing in database logs
* Throughput decreases despite stable traffic levels

## Root Causes

1. **Row Lock Contention**

   * Multiple transactions competing for the same rows
   * Long-running transactions holding locks
   * High-frequency updates to hot records
   * Excessive write concurrency

2. **Deadlocks**

   * Transactions acquiring locks in different orders
   * Circular lock dependencies
   * Simultaneous updates across multiple tables
   * Poor transaction design

3. **Long-Running Transactions**

   * Transactions left open unnecessarily
   * User interactions occurring within transactions
   * Large batch updates or deletes
   * Inefficient application workflows

4. **Missing or Inefficient Indexes**

   * Full table scans causing broader lock scope
   * Range scans locking excessive rows
   * Poor query execution plans

5. **Hotspot Records**

   * Frequently updated counters
   * Shared configuration tables
   * Popular inventory or account records
   * Centralized metadata updates

6. **Bulk Data Operations**

   * Large imports or migrations
   * Mass update statements
   * Schema changes affecting active tables
   * Maintenance jobs running during peak traffic

7. **Application Design Issues**

   * Excessive transaction isolation levels
   * Unnecessary locking queries
   * Lack of retry handling for deadlocks

## Detection Steps

1. Check active transactions:

   ```sql
   SHOW PROCESSLIST;
   ```

   Look for:

   * Long-running queries
   * Queries in "Waiting for lock" state
   * Blocked transactions

2. Inspect InnoDB lock status:

   ```sql
   SHOW ENGINE INNODB STATUS\G
   ```

   Review:

   * Latest detected deadlocks
   * Waiting transactions
   * Lock ownership information

3. Identify lock waits:

   ```sql
   SELECT * FROM information_schema.innodb_lock_waits;
   ```

4. Review slow query logs:

   * Long execution times
   * Frequently blocked queries
   * Repeated transaction retries

5. Monitor database metrics:

   * Transaction timeout count
   * Deadlock count
   * Connection pool utilization
   * Query latency

6. Review application logs:

   * Transaction timeout exceptions
   * Deadlock exceptions
   * Database retry activity

## Immediate Mitigation

1. **Identify Blocking Transactions**

   ```sql
   SHOW PROCESSLIST;
   ```

   Find transactions holding locks for extended periods.

2. **Terminate Problematic Sessions**

   ```sql
   KILL <process_id>;
   ```

   Remove blocking transactions when operationally safe.

3. **Reduce Transaction Duration**

   * Commit transactions earlier
   * Avoid user interaction inside transactions
   * Split large operations into smaller batches

4. **Retry Deadlocked Transactions**

   * Implement safe retry logic
   * Apply exponential backoff
   * Prevent immediate retry storms

5. **Pause Bulk Operations**

   * Stop migrations
   * Pause batch jobs
   * Reduce write-heavy workloads

6. **Scale Read Traffic Away**

   * Route reads to replicas
   * Reduce pressure on primary database
   * Isolate write contention

## Long-term Resolution

1. **Optimize Transaction Design**

   * Keep transactions short
   * Minimize lock duration
   * Commit as early as possible

2. **Standardize Lock Acquisition Order**

   * Ensure transactions lock resources consistently
   * Reduce deadlock probability
   * Document locking patterns

3. **Improve Indexing**

   * Add missing indexes
   * Reduce table scans
   * Limit rows affected by locking operations

4. **Reduce Hotspot Contention**

   * Partition high-traffic data
   * Shard frequently updated records
   * Distribute write operations

5. **Batch Processing Improvements**

   * Process smaller transaction batches
   * Avoid massive updates
   * Schedule maintenance during off-peak hours

6. **Application Resilience**

   * Automatic deadlock retry handling
   * Lock timeout monitoring
   * Graceful transaction recovery

7. **Monitoring & Alerting**

   * Alert on deadlock spikes
   * Monitor lock wait times
   * Track long-running transactions
   * Alert on transaction timeout increases

## Escalation

* If transaction timeouts exceed SLA thresholds: page database owner
* If deadlocks increase significantly: involve application team
* If lock contention impacts customer-facing services: declare incident
* If database throughput drops substantially: escalate to platform engineering
* If blocking transactions cannot be safely terminated: engage database administrators immediately

## Success Criteria

* Query execution times return to baseline
* Transaction timeouts cease
* Lock wait times normalize
* Deadlock frequency returns to normal levels
* Application latency recovers
* Connection pool utilization stabilizes
* No blocked transactions remain
* No lock-related alerts observed for 30 minutes
