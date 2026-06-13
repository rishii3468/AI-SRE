# High CPU Usage Runbook

## Symptoms

* Application response times increase significantly
* CPU utilization exceeds 90% for sustained periods
* Elevated API latency (p95/p99) across services
* Increased request queue lengths
* Pod or container throttling events
* Timeouts and failed requests under load
* Reduced throughput despite stable traffic
* Autoscaling events triggered frequently

## Root Causes

1. **Traffic Surge**

   * Sudden increase in user traffic
   * Marketing campaigns or product launches
   * Unexpected bot traffic
   * DDoS-like request patterns

2. **Inefficient Application Logic**

   * Infinite loops
   * Excessive recursion
   * Unoptimized algorithms
   * CPU-intensive data processing

3. **Hot Endpoint or Query**

   * Frequently accessed API endpoint
   * Expensive database queries
   * Resource-heavy report generation
   * Poorly cached operations

4. **Background Job Saturation**

   * Scheduled batch jobs
   * Data migration processes
   * Analytics workloads
   * Queue consumer overload

5. **Resource Undersizing**

   * CPU limits too low
   * Insufficient replicas
   * Underprovisioned nodes
   * Incorrect autoscaling thresholds

6. **Dependency-Induced CPU Load**

   * Excessive retries
   * Serialization/deserialization overhead
   * Connection management inefficiencies
   * High-volume error handling

7. **Runtime or Garbage Collection Pressure**

   * Excessive memory allocation
   * Frequent garbage collection cycles
   * Memory leaks increasing CPU activity
   * Runtime configuration issues

## Detection Steps

1. Check CPU utilization:

   Kubernetes:

   ```bash
   kubectl top pods
   kubectl top nodes
   ```

   Linux:

   ```bash
   top
   htop
   mpstat
   ```

2. Identify high-CPU processes:

   ```bash
   ps aux --sort=-%cpu | head
   ```

3. Review application metrics:

   * `cpu_usage_percent`
   * `request_latency_p95`
   * `request_rate`
   * `error_rate`
   * `queue_depth`

4. Analyze application logs:

   Look for:

   * Long-running requests
   * Excessive retries
   * Repeated processing loops
   * Batch job execution spikes

5. Profile application performance:

   * CPU flame graphs
   * Request tracing
   * Function execution times
   * Thread utilization

6. Compare traffic patterns:

   * Current request volume vs baseline
   * Traffic spike timing
   * Top endpoints by request count

## Immediate Mitigation

1. **Scale Application Replicas**

   Kubernetes:

   ```bash
   kubectl scale deployment <deployment-name> --replicas=10
   ```

   Distribute workload across additional instances.

2. **Enable Autoscaling**

   ```bash
   kubectl autoscale deployment <deployment-name>
   ```

   Increase capacity automatically during demand spikes.

3. **Identify and Disable Problematic Workloads**

   * Pause heavy batch jobs
   * Disable expensive background tasks
   * Reduce non-critical processing

4. **Rate Limit Incoming Traffic**

   * Protect backend systems
   * Prevent resource exhaustion
   * Prioritize critical traffic

5. **Restart Stuck Processes**

   * Recover from runaway CPU consumption
   * Clear deadlocked or looping workloads

6. **Reduce Feature Load**

   * Disable resource-intensive features
   * Serve cached responses where possible
   * Temporarily limit expensive API operations

## Long-term Resolution

1. **Optimize Application Logic**

   * Eliminate infinite loops
   * Improve algorithm efficiency
   * Reduce redundant computations
   * Optimize serialization and processing

2. **Performance Profiling**

   * Establish regular profiling practices
   * Identify CPU hotspots
   * Benchmark critical code paths

3. **Caching Strategy**

   * Cache expensive computations
   * Reduce repeated database queries
   * Implement response caching

4. **Autoscaling Improvements**

   * Configure CPU-based scaling policies
   * Tune scaling thresholds
   * Prevent delayed scale-up events

5. **Workload Segmentation**

   * Separate batch jobs from user-facing workloads
   * Isolate CPU-intensive services
   * Use dedicated worker pools

6. **Capacity Planning**

   * Forecast traffic growth
   * Maintain resource headroom
   * Conduct load testing regularly

7. **Monitoring & Alerting**

   * Alert when CPU exceeds 80%
   * Monitor throttling events
   * Track latency and throughput trends
   * Alert on abnormal request volume spikes

## Escalation

* If CPU remains above 90% for more than 10 minutes: page service owner
* If customer-facing latency exceeds SLA: declare incident
* If autoscaling cannot reduce utilization: escalate to platform team
* If node-level CPU saturation occurs: engage infrastructure team
* If suspected code defect causes runaway CPU usage: involve development team immediately

## Success Criteria

* CPU utilization returns below 70%
* Request latency returns to baseline
* Throughput stabilizes
* Error rates normalize
* No CPU throttling events observed
* Autoscaling operates within expected ranges
* Customer-facing performance restored
* No recurring CPU spikes for at least 30 minutes
