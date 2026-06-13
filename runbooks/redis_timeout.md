# Redis Timeout Runbook

## Symptoms
- Redis command timeouts (GET/SET operations failing)
- Connection pool utilization at 90%+ 
- Session lookup latency spikes
- Login failures and authentication timeouts
- API latency degradation (p95/p99 increasing)

## Root Causes
1. **Connection Pool Exhaustion** - All available connections in use, new requests queued
2. **Redis Memory Pressure** - Eviction policies triggering, slow performance
3. **Redis Primary Node Down** - Failover incomplete or replica lag
4. **Network Partition** - Connectivity issues between app and Redis cluster
5. **Slow Commands** - Blocking operations (KEYS, FLUSHALL) on large datasets

## Detection Steps
1. Check Redis INFO command: `redis-cli INFO stats`
   - Look for `total_connections_received` and `rejected_connections`
2. Verify connection pool status in application logs
3. Monitor `redis_connection_pool_utilization` metric
4. Check Redis memory usage: `redis-cli INFO memory | grep used_memory_human`

## Immediate Mitigation
1. **Scale connection pool** (5-10 min):
   - Increase `REDIS_POOL_SIZE` environment variable by 25%
   - Restart affected service instances
2. **Increase timeout threshold** (quick, temporary):
   - Raise `REDIS_TIMEOUT_MS` from default to 10000ms
   - Monitor error rate before permanent change
3. **Circuit breaker activation** (if available):
   - Enable Redis circuit breaker to fail fast
   - Fall back to cache or return stale data

## Long-term Resolution
1. **Capacity Planning**:
   - Baseline: 100 connections per 1000 RPS
   - Scale Redis cluster horizontally if peak RPS increasing
   - Consider read replicas for session lookups
2. **Connection Management**:
   - Implement connection pooling best practices
   - Add jitter to retry logic to avoid thundering herd
3. **Monitoring Setup**:
   - Alert on connection pool utilization > 80%
   - Track rejected_connections metric
   - Monitor command latency percentiles

## Rollback/Escalation
- If mitigation doesn't resolve in 5 min: engage Redis platform team
- Consider traffic shedding or rate limiting to reduce load
- Prepare for Redis restart if memory issue suspected