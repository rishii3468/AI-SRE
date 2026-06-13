# Cache Stampede Runbook

## Symptoms

* Sudden database CPU spike immediately after cache expiry
* Sharp increase in database queries per second (QPS)
* Cache hit ratio drops significantly (<80%)
* API latency spikes affecting read-heavy endpoints
* Increased response times despite healthy application instances
* Database connection pool exhaustion
* Elevated cache miss rate across multiple application nodes
* Increased HTTP 5xx errors caused by backend timeouts

## Root Causes

1. **Simultaneous Cache Expiry**

   * Large numbers of cache keys share identical TTL values
   * Popular keys expire at the same time, causing request bursts to the database

2. **Hot Key Expiration**

   * Frequently accessed cache entry expires
   * Thousands of concurrent requests regenerate the same data

3. **Cache Cluster Restart**

   * Redis or cache cluster restart clears cached entries
   * Entire application falls back to the database

4. **Cache Eviction Pressure**

   * Memory limits force eviction of frequently used keys
   * Cache effectiveness degrades rapidly

5. **Missing Request Coalescing**

   * Multiple application instances independently rebuild identical cache entries
   * Duplicate database work amplifies load

## Detection Steps

1. Check cache metrics:

   * `cache_hit_ratio` (should be >95%, alert if <80%)
   * `cache_miss_rate`
   * `cache_evictions_total`

2. Monitor database metrics:

   * Database CPU utilization
   * Query rate (QPS)
   * Connection pool usage
   * Slow query count

3. Review application logs:

   * Search for cache miss spikes
   * Look for repeated cache rebuild operations
   * Identify hot keys generating excessive traffic

4. Verify cache health:

   * Redis: `redis-cli INFO stats`
   * Check memory utilization and eviction counts
   * Confirm cache cluster availability

5. Compare timeline:

   * Determine whether latency spike aligns with cache expiration events
   * Verify if database load increased immediately after cache miss surge

## Immediate Mitigation

1. **Warm Critical Cache Entries**

   * Preload frequently accessed data
   * Prioritize hot keys and high-traffic endpoints

2. **Stagger Cache Expiration**

   * Add TTL jitter/randomization
   * Example: TTL = 3600 ± 300 seconds

3. **Enable Request Coalescing**

   * Allow only one request to regenerate a cache entry
   * Other requests wait for cache population

4. **Serve Stale Data Temporarily**

   * Return slightly stale cache entries while regeneration occurs
   * Prevents database overload

5. **Scale Database Resources**

   * Add read replicas if available
   * Increase connection pool capacity temporarily

6. **Rate Limit Expensive Endpoints**

   * Protect backend systems from surge traffic
   * Prioritize critical business operations

## Long-term Resolution

1. **Probabilistic Early Expiration**

   * Refresh cache entries before actual expiration
   * Prevent synchronized expiration events

2. **Cache Warming Framework**

   * Automatically refresh critical keys
   * Schedule warming during low-traffic periods

3. **Request Deduplication**

   * Implement distributed locking
   * Use single-flight request patterns

4. **TTL Randomization**

   * Ensure cache keys expire gradually
   * Avoid synchronized invalidation events

5. **Multi-Layer Caching**

   * Application cache + Redis cache
   * Reduce database dependency during cache misses

6. **Capacity Planning**

   * Identify hot keys and high-read workloads
   * Scale cache memory before eviction becomes a problem

7. **Monitoring & Alerting**

   * Alert on cache hit ratio <90%
   * Alert on cache miss rate anomalies
   * Monitor database load following cache expirations
   * Track top cache keys by request volume

## Escalation

* If database CPU remains >80% for 10 minutes: page database owner
* If cache hit ratio remains <70% for 5 minutes: page platform team
* If API latency exceeds SLA for 15 minutes: declare incident
* If database connection pool exhaustion occurs: initiate emergency traffic reduction measures
* If cache cluster failure impacts multiple services: escalate to infrastructure on-call

## Success Criteria

* Cache hit ratio restored above 95%
* Database CPU returns to baseline
* Query rate normalized
* API latency within SLA
* No sustained cache miss spikes observed
* Hot keys successfully warmed and protected
