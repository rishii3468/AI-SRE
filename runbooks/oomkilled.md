# OOMKilled Runbook

## Symptoms

* Kubernetes pod terminated with `OOMKilled` status
* Container restart count increases unexpectedly
* Sudden application crashes under load
* Memory utilization spikes before pod termination
* Service instability or intermittent outages
* Increased latency prior to crashes
* Kubernetes events indicate memory limit violations
* Node memory pressure warnings observed

## Root Causes

1. **Memory Leak**

   * Objects retained indefinitely
   * Unreleased resources
   * Growing in-memory caches
   * Application code defects causing memory growth

2. **Memory Limits Too Low**

   * Container memory limits below workload requirements
   * Incorrect resource requests and limits
   * Recent traffic growth exceeding capacity planning

3. **Traffic Surge**

   * Increased request volume
   * Larger payload sizes
   * Unexpected workload spikes
   * Batch processing overload

4. **Unbounded Cache Growth**

   * Missing cache eviction policies
   * Unlimited session storage
   * Excessive object retention

5. **Large Batch Operations**

   * Processing large datasets in memory
   * Bulk imports or exports
   * Analytics or reporting jobs

6. **Dependency or Runtime Issues**

   * Memory-intensive library updates
   * Runtime configuration problems
   * Garbage collection inefficiencies

7. **Node Resource Pressure**

   * Multiple workloads competing for memory
   * Oversubscribed Kubernetes nodes
   * Insufficient cluster capacity

## Detection Steps

1. Check pod status:

   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

   Look for:

   * `OOMKilled`
   * Restart counts
   * Memory-related events

2. Review pod events:

   ```bash
   kubectl describe pod <pod-name>
   ```

   Search for:

   * Memory limit exceeded
   * OOM kill notifications
   * Node memory pressure

3. Monitor memory utilization:

   ```bash
   kubectl top pods
   kubectl top nodes
   ```

   Review:

   * Current memory consumption
   * Historical memory growth trends

4. Analyze application logs:

   ```bash
   kubectl logs <pod-name> --previous
   ```

   Look for:

   * OutOfMemory errors
   * Heap allocation failures
   * Cache growth messages

5. Inspect resource configuration:

   ```bash
   kubectl get deployment <deployment-name> -o yaml
   ```

   Verify:

   * Memory requests
   * Memory limits
   * Recent configuration changes

6. Capture diagnostic information:

   * Heap dumps
   * Memory profiles
   * Garbage collection metrics
   * Cache utilization statistics

## Immediate Mitigation

1. **Increase Memory Limits**

   Update deployment configuration:

   ```yaml
   resources:
     limits:
       memory: "4Gi"
   ```

   Provide sufficient headroom to stabilize the service.

2. **Restart Affected Pods**

   ```bash
   kubectl rollout restart deployment/<deployment-name>
   ```

   Clear accumulated memory usage.

3. **Scale Additional Replicas**

   * Distribute workload across more instances
   * Reduce memory pressure per pod

4. **Reduce Memory Consumption**

   * Clear non-critical caches
   * Disable memory-intensive features
   * Reduce batch sizes

5. **Capture Diagnostics Before Restart**

   * Heap dump
   * Memory profile
   * Runtime metrics
   * Application logs

6. **Reduce Incoming Load**

   * Apply rate limiting
   * Throttle heavy operations
   * Prioritize critical traffic

## Long-term Resolution

1. **Fix Memory Leaks**

   * Identify retained objects
   * Remove stale references
   * Correct resource cleanup logic

2. **Right-Size Resource Limits**

   * Align memory limits with workload requirements
   * Use historical utilization data
   * Avoid overly aggressive limits

3. **Implement Cache Controls**

   * Configure cache size limits
   * Add eviction policies
   * Monitor cache growth

4. **Optimize Memory Usage**

   * Stream large datasets
   * Reduce object allocation rates
   * Improve data structures

5. **Improve Capacity Planning**

   * Load testing
   * Traffic forecasting
   * Resource utilization analysis

6. **Autoscaling Improvements**

   * Scale based on memory utilization
   * Prevent resource exhaustion during traffic spikes

7. **Monitoring & Alerting**

   * Alert on memory utilization >80%
   * Alert on OOMKilled events
   * Track memory growth trends
   * Monitor restart frequency

## Escalation

* If OOMKilled events occur repeatedly within 15 minutes: page service owner
* If multiple pods are OOMKilled simultaneously: declare incident
* If node memory pressure impacts other workloads: engage platform team
* If memory growth indicates application defect: involve development team
* If service availability is impacted: escalate to incident commander

## Success Criteria

* No new OOMKilled events observed
* Memory utilization remains within expected limits
* Pod restart count stabilizes
* Application performance returns to baseline
* Memory growth trend eliminated or controlled
* Cache utilization remains bounded
* Customer-facing functionality restored
* No memory-related alerts active for 30 minutes
