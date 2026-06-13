# API Latency Runbook

## Symptoms
- API p95 latency > 2000ms (baseline ~200ms)
- API p99 latency > 5000ms (baseline ~500ms)
- Request timeout errors increasing
- Client experiences slow page loads
- Monitoring alerts: "API Latency Threshold Exceeded"

## Root Causes
1. **Database Bottleneck** - Slow queries, missing indexes, high lock contention
2. **Downstream Dependency Slowdown** - External API, microservice, or cache latency
3. **Service CPU Saturation** - CPU-bound workload consuming 100% CPU
4. **Memory Pressure** - Garbage collection pauses, swap usage
5. **Network Latency** - High packet loss, congestion, or DNS resolution delays
6. **Inefficient Code** - N+1 queries, redundant computations, suboptimal algorithms

## Detection Steps
1. Check API service metrics:
   - `GET /metrics` endpoint for histograms
   - Look for `http_request_duration_seconds{quantile="0.95"}` spike
2. Profile a slow request:
   - Enable request tracing: `curl -H "X-Trace-Enable: true" http://api/endpoint`
   - Review span timings in trace output
3. Database analysis:
   - Identify slow queries: `SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;`
   - Check for missing indexes on frequently queried columns
   - Monitor active connections: `SELECT count(*) FROM pg_stat_activity;`
4. Service resource check:
   - CPU: `kubectl top pod api-service-pod`
   - Memory: `kubectl describe pod api-service-pod | grep -A 5 Memory`
   - GC pauses: check application logs for GC time

## Immediate Mitigation (0-5 minutes)
1. **Scale horizontal replicas**:
   - `kubectl scale deployment api-service --replicas=5`
   - Distributes load across more instances
2. **Increase request timeout** (temporary):
   - Raise client timeout from 5s to 10s
   - Gives slow requests time to complete
3. **Enable caching for expensive queries**:
   - Query cache: 5-min TTL for product catalog
   - HTTP cache: add Cache-Control headers for GET endpoints
4. **Circuit breaker for slow dependencies**:
   - If external API latency >2s, fail fast
   - Use cached response or default value

## Long-term Resolution
1. **Database Optimization**:
   - Add indexes on WHERE/JOIN columns
   - Denormalize hot data to reduce joins
   - Implement query result caching (10-60 min)
   - Consider read replicas for reporting queries
2. **Code Efficiency**:
   - Eliminate N+1 query patterns (use batch queries)
   - Profile CPU-bound operations with flame graphs
   - Implement pagination for large result sets
3. **Dependency Management**:
   - Use timeout/retry strategies with jitter
   - Implement bulkheads (isolate slow services)
   - Cache external API responses
4. **Capacity Planning**:
   - Right-size instances for baseline load
   - Add auto-scaling (trigger at 70% CPU)
   - Load test before major features

## Monitoring & Alerting
- Alert on p95 latency > 2x baseline
- Track p99 separately (tail latencies matter)
- Monitor per-endpoint latencies (identify problem areas)
- Set up SLO: API latency p99 < 1000ms

## Escalation
- If mitigation doesn't improve after 5 min: page database team
- If database CPU 100%: consider emergency query optimization
- If unresolved >15 min: activate feature degradation (disable slow features)