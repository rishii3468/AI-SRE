# Memory Leak Runbook

## Symptoms

* Memory usage increases steadily over time without returning to baseline
* Pod or process memory consumption continuously grows
* Frequent `OOMKilled` events in Kubernetes
* Application performance degrades gradually
* Increased garbage collection activity
* Service restarts become more frequent
* Response latency increases as memory pressure grows
* Node memory utilization rises despite stable traffic

## Root Causes

1. **Unreleased Objects**

   * Objects retained longer than necessary
   * References preventing garbage collection
   * Memory allocation without proper cleanup
   * Event listeners or callbacks not removed

2. **Unbounded Cache Growth**

   * Missing cache eviction policies
   * Unlimited in-memory data structures
   * Stale cache entries accumulating
   * Excessive session or object retention

3. **Resource Leaks**

   * Open file handles not closed
   * Database connections not released
   * Network sockets remaining active
   * Thread pools growing uncontrollably

4. **Application Defects**

   * Memory leak introduced in a recent release
   * Third-party library leak
   * Serialization or deserialization issues
   * Recursive object references

5. **Background Job Accumulation**

   * Queued tasks retained in memory
   * Failed jobs not cleaned up
   * Message processing buffers growing indefinitely

6. **Large Data Retention**

   * Excessive in-memory datasets
   * Oversized request payloads
   * Long-lived application state
   * Batch processing buffers

7. **Garbage Collection Inefficiency**

   * Excessive object creation
   * Fragmented heap
   * Runtime configuration issues
   * Insufficient memory tuning

## Detection Steps

1. Check memory utilization:

   Kubernetes:

   ```bash
   kubectl top pods
   kubectl top nodes
   ```

   Linux:

   ```bash
   free -m
   top
   htop
   ```

2. Review historical memory trends:

   * `memory_usage_bytes`
   * `heap_usage_percent`
   * `container_memory_working_set_bytes`
   * OOM event count

3. Check for OOMKilled events:

   ```bash
   kubectl describe pod <pod-name>
   ```

   Look for:

   * OOMKilled
   * Restart counts
   * Memory limit violations

4. Analyze application logs:

   Search for:

   * OutOfMemory exceptions
   * Heap allocation warnings
   * Cache growth messages
   * Garbage collection events

5. Capture memory profiles:

   * Heap dumps
   * Memory snapshots
   * Allocation tracking
   * Object retention analysis

6. Verify cache behavior:

   * Cache size growth
   * Eviction rates
   * Hit/miss ratios
   * Session counts

## Immediate Mitigation

1. **Restart Affected Service**

   Kubernetes:

   ```bash
   kubectl rollout restart deployment/<deployment-name>
   ```

   Frees accumulated memory and restores service stability.

2. **Scale Additional Replicas**

   * Reduce memory pressure per instance
   * Maintain service availability during investigation

3. **Clear Non-Critical Caches**

   * Remove stale entries
   * Reduce memory footprint
   * Monitor application impact

4. **Increase Memory Limits (Temporary)**

   * Prevent immediate OOM failures
   * Allow time for root-cause analysis

5. **Disable Problematic Features**

   * Pause memory-intensive workloads
   * Reduce data retention in memory
   * Limit batch processing size

6. **Capture Diagnostic Data Before Restart**

   * Heap dumps
   * Memory profiles
   * Runtime metrics
   * Application logs

## Long-term Resolution

1. **Patch Application Defects**

   * Fix object retention issues
   * Remove stale references
   * Address memory leaks in code

2. **Implement Cache Controls**

   * Configure cache eviction policies
   * Add maximum cache size limits
   * Expire stale entries automatically

3. **Resource Lifecycle Management**

   * Ensure connections are closed
   * Release file handles
   * Clean up background tasks

4. **Memory Profiling Program**

   * Regular heap analysis
   * Automated leak detection
   * Pre-release memory testing

5. **Optimize Application Architecture**

   * Reduce in-memory state
   * Stream large datasets
   * Limit object lifetimes

6. **Runtime Tuning**

   * Optimize garbage collection settings
   * Configure memory thresholds
   * Improve heap management

7. **Monitoring & Alerting**

   * Alert on continuous memory growth
   * Track heap utilization trends
   * Monitor cache growth rates
   * Alert before OOM conditions occur

## Escalation

* If memory usage exceeds 90% for more than 10 minutes: page service owner
* If OOMKilled events occur repeatedly: escalate immediately
* If multiple instances exhibit identical growth patterns: involve development team
* If node memory pressure impacts other workloads: engage platform team
* If customer-facing services degrade significantly: declare incident

## Success Criteria

* Memory utilization stabilizes
* No continuous upward memory trend observed
* OOMKilled events cease
* Restart frequency returns to baseline
* Cache growth remains within expected limits
* Application latency normalizes
* Root cause identified and patched
* No memory-related alerts observed for 30 days after deployment of the fix
