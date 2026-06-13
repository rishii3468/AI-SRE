# Authentication Failure Runbook

## Symptoms
- User login failures with "session validation timeout" errors
- Authentication service latency spikes (>2s)
- Failed login rate > 5% (baseline ~0.1%)
- Session lookup failures
- Token validation timeouts
- API 401/403 errors increasing

## Root Causes
1. **Session Store Latency** - Redis or session database slow/unavailable
2. **Authentication Service Degradation** - Auth service instance down or overloaded
3. **Downstream Dependency** - User database or identity provider unreachable
4. **Token Cache Eviction** - Session cache full, frequent misses
5. **Retry Amplification** - Cascading retries causing thundering herd

## Detection Steps
1. Check auth service error logs:
   - `grep "session lookup timeout" /var/log/auth-service.log`
   - Look for database connection errors
2. Monitor key metrics:
   - `auth_service_latency_p95` (should be <500ms, alert if >2s)
   - `auth_failure_rate` (should be <1%, alert if >5%)
3. Verify session store connectivity:
   - Redis: `redis-cli PING`
   - Database: `psql -c "SELECT 1"`
4. Check identity provider status:
   - Test OAuth/SAML endpoint reachability
   - Review rate limit headers on responses

## Immediate Mitigation
1. **Clear stale session cache** (if safe):
   - `redis-cli --scan --pattern "session:*" | redis-cli -x DEL` (async clear)
   - Sessions rebuild on next login attempt
   - Monitor error rate during clearing
2. **Reduce session validation checks**:
   - Temporarily trust JWT signature without DB lookup
   - Reduces session store queries by 80%
3. **Increase token TTL** (temporary):
   - Change from 1h to 2h token expiry
   - Reduces session validation frequency

## Long-term Resolution
1. **Session Store Reliability**:
   - Implement Redis Sentinel for automatic failover
   - Add multi-region session replication
   - Implement fallback auth path
2. **Circuit Breaker Pattern**:
   - Fail open on timeouts (allow with degraded trust)
   - Log all degraded-mode authentications
3. **Rate Limiting**:
   - Per-user login rate limits (5 attempts/5min)
   - Per-IP rate limits to stop brute force
4. **Monitoring & Alerting**:
   - Alert on failure rate > 2%
   - Track p99 session store latency
   - Monitor retry storm patterns

## Escalation
- If unresolved after 10 min: page auth service owner
- If failure rate >20%: consider blocking new logins, preserve sessions
- If identity provider down >30min: activate manual backup auth method