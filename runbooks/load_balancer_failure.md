# Load Balancer Failure Runbook

## Symptoms
- HTTP 502 "Bad Gateway" errors from client perspective
- HTTP 503 "Service Unavailable" responses
- Client connection timeouts (connection refused)
- Traffic asymmetry (some backends getting all traffic)
- API availability drops below 99%
- Error rate spikes to 5-20%

## Root Causes
1. **Unhealthy Backend Instances** - Health checks failing, LB removes nodes
2. **Backend Crash Loop** - Service crashing and restarting repeatedly
3. **Backend Resource Exhaustion** - OOM, disk full, or open file limits
4. **Load Balancer Overload** - LB at capacity, rejecting new connections
5. **Network Connectivity** - Firewall block or routing issue between LB and backends

## Detection Steps
1. Check load balancer pool status:
   - AWS: `aws elbv2 describe-target-health --target-group-arn arn:...`
   - K8s: `kubectl get svc api-gateway` (check endpoints count)
2. Verify backend health:
   - `curl -s http://backend:8080/health` from LB host
   - Check response code and latency
3. Monitor backend logs:
   - Look for crash errors, panic, OOM signals
   - Check for restart loops in Kubernetes: `kubectl get pods -w`
4. Check backend resource usage:
   - CPU: `kubectl top pod pod_name`
   - Memory: `kubectl describe pod pod_name | grep -A 5 Memory`
   - Disk: `df -h` on backend host

## Immediate Mitigation (0-5 minutes)
1. **Scale backend replicas**:
   - `kubectl scale deployment api-gateway --replicas=5`
   - Adds healthy nodes; LB routes to them automatically
2. **Force health check re-evaluation**:
   - Restart one backend pod: `kubectl delete pod pod_name`
   - Others should absorb traffic during restart
3. **Manually drain failed nodes** (if platform allows):
   - Mark unhealthy nodes as drain so no new connections
   - Existing connections have 30s to gracefully close

## Long-term Resolution
1. **Fix Backend Crashes**:
   - Identify root cause in logs (OOM, panic, resource limit)
   - Apply fixes and redeploy
   - Add liveness/readiness probes that reflect actual health
2. **Resource Scaling**:
   - Set appropriate resource requests/limits
   - Auto-scale based on CPU (70%) or custom metrics
   - Plan capacity for peak load (usually 2x average)
3. **Health Check Optimization**:
   - Use realistic endpoints (not expensive operations)
   - Increase timeout if backends naturally slow on startup
   - Reduce frequency if creating unnecessary load
4. **Monitoring & Alerting**:
   - Alert on healthy backend count < threshold
   - Track 502/503 error rate continuously
   - Monitor backend startup time and recovery

## Escalation
- If >50% backends down and scaling doesn't help: page SRE
- If unresolved after 10 min: activate incident protocol
- If outage >5 min: prepare customer communication
- Consider traffic failover to standby region if available