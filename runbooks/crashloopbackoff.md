# CrashLoopBackOff Runbook

## Symptoms

* Pod enters `CrashLoopBackOff` state
* Container restart count increases continuously
* Application becomes unavailable or partially degraded
* Kubernetes events show repeated container restarts
* Readiness and liveness probes failing
* Service endpoints disappear intermittently
* Increased HTTP 5xx errors from dependent services
* New deployments fail to become healthy

## Root Causes

1. **Configuration Errors**

   * Invalid environment variables
   * Missing required configuration values
   * Incorrect application settings
   * Malformed configuration files

2. **Missing Secrets or ConfigMaps**

   * Kubernetes Secret not found
   * Incorrect secret name reference
   * Missing credentials, API keys, or certificates
   * Secret mounted incorrectly

3. **Application Startup Failure**

   * Unhandled exception during initialization
   * Dependency injection failure
   * Invalid startup arguments
   * Missing application resources

4. **Dependency Unavailability**

   * Database unreachable during startup
   * Redis or cache service unavailable
   * External API dependency timeout
   * Service discovery failure

5. **Resource Constraints**

   * Container exceeds memory limit and is OOMKilled
   * CPU starvation causing startup timeout
   * Insufficient node resources

6. **Probe Misconfiguration**

   * Liveness probe too aggressive
   * Readiness probe timeout too short
   * Startup probe missing or incorrectly configured

7. **Image or Deployment Issues**

   * Corrupted container image
   * Incorrect image tag
   * Failed deployment artifact
   * Runtime incompatibility after release

## Detection Steps

1. Check pod status:

   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

   Look for:

   * CrashLoopBackOff events
   * Restart counts
   * Exit codes
   * Probe failures

2. Review container logs:

   ```bash
   kubectl logs <pod-name>
   kubectl logs <pod-name> --previous
   ```

   Search for:

   * Startup exceptions
   * Missing configuration errors
   * Secret loading failures
   * Connection failures

3. Inspect Kubernetes events:

   ```bash
   kubectl describe pod <pod-name>
   ```

   Look for:

   * FailedMount
   * FailedScheduling
   * Back-off restarting failed container
   * OOMKilled

4. Verify secrets and ConfigMaps:

   ```bash
   kubectl get secrets
   kubectl get configmaps
   ```

5. Check deployment configuration:

   ```bash
   kubectl describe deployment <deployment-name>
   ```

6. Validate resource utilization:

   ```bash
   kubectl top pod
   kubectl top node
   ```

## Immediate Mitigation

1. **Inspect Application Logs**

   * Identify startup failures
   * Capture exception stack traces
   * Determine whether failure occurs before service initialization

2. **Validate Configuration**

   * Confirm required environment variables exist
   * Verify ConfigMaps and Secrets are mounted correctly
   * Check deployment manifests for recent changes

3. **Rollback Recent Deployment**

   * If failures started after a release:

   ```bash
   kubectl rollout undo deployment <deployment-name>
   ```

4. **Restore Missing Secrets**

   * Recreate deleted or corrupted secrets
   * Verify secret references in deployment manifests

5. **Temporarily Disable Faulty Probes**

   * Prevent unnecessary restarts while investigating
   * Increase probe timeout thresholds

6. **Scale Healthy ReplicaSet**

   * Route traffic to stable application versions
   * Reduce customer impact

## Long-term Resolution

1. **Configuration Validation**

   * Validate configuration during CI/CD
   * Fail deployments if required values are missing
   * Enforce schema validation

2. **Secret Management Improvements**

   * Centralized secret management
   * Secret rotation automation
   * Pre-deployment secret validation

3. **Startup Resilience**

   * Graceful handling of unavailable dependencies
   * Retry mechanisms during initialization
   * Circuit breakers for external services

4. **Deployment Safety Controls**

   * Canary deployments
   * Blue-green deployments
   * Automated rollback on health check failures

5. **Resource Optimization**

   * Right-size memory and CPU limits
   * Monitor startup resource consumption
   * Prevent OOM conditions

6. **Probe Optimization**

   * Add startup probes
   * Tune readiness and liveness thresholds
   * Align probe timing with application startup characteristics

7. **Monitoring & Alerting**

   * Alert on restart count increases
   * Alert on CrashLoopBackOff events
   * Track deployment success rates
   * Monitor pod health and startup duration

## Escalation

* If pod remains in CrashLoopBackOff for more than 10 minutes: page service owner
* If restart count exceeds 20 within 15 minutes: escalate to application team
* If multiple services are affected: declare platform incident
* If deployment rollout causes widespread failures: initiate rollback immediately
* If root cause is infrastructure-related: engage Kubernetes platform team

## Success Criteria

* Pod reaches Running state
* Restart count stabilizes
* Readiness and liveness probes pass consistently
* Service endpoints become healthy
* Application error rates return to baseline
* No new CrashLoopBackOff events observed for 30 minutes
