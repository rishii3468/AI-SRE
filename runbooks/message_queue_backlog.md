# Message Queue Backlog Runbook

## Symptoms

* Queue depth increases continuously over time
* Message processing lag grows beyond normal thresholds
* Oldest message age steadily increases
* Consumer throughput drops below producer throughput
* Delayed processing of business events
* Increased end-to-end request latency
* Retry queue growth and dead-letter queue (DLQ) accumulation
* Customer-facing operations become delayed or inconsistent

## Root Causes

1. **Slow Consumers**

   * Database latency impacting message processing
   * External API dependencies responding slowly
   * CPU or memory resource contention
   * Inefficient consumer logic

2. **Consumer Crash**

   * Application exception causing consumer termination
   * OOMKilled consumer pods
   * Deployment failure affecting consumers
   * Dependency initialization failure

3. **Traffic Surge**

   * Producer throughput exceeds consumer capacity
   * Sudden increase in event generation
   * Bulk imports or batch processing workloads

4. **Downstream Dependency Bottleneck**

   * Database saturation
   * Cache failures
   * Third-party API degradation
   * Service-to-service communication issues

5. **Message Poisoning**

   * Invalid messages repeatedly retried
   * Consumer stuck processing problematic payloads
   * Large messages causing processing delays

6. **Consumer Configuration Issues**

   * Low concurrency settings
   * Insufficient consumer replicas
   * Misconfigured batch size
   * Rate limiting constraints

7. **Queue Infrastructure Problems**

   * Broker resource exhaustion
   * Storage latency in queue system
   * Partition imbalance
   * Replication issues

## Detection Steps

1. Monitor queue metrics:

   * `queue_depth`
   * `consumer_lag`
   * `oldest_message_age`
   * `messages_processed_per_second`
   * `messages_published_per_second`

2. Check consumer health:

   Kubernetes:

   ```bash
   kubectl get pods
   kubectl top pods
   ```

   Verify:

   * Running status
   * Restart counts
   * Resource utilization

3. Review consumer logs:

   ```bash
   kubectl logs <consumer-pod>
   ```

   Look for:

   * Processing failures
   * Database timeouts
   * External API errors
   * Application crashes

4. Inspect queue infrastructure:

   * Broker CPU and memory
   * Queue partition health
   * Disk utilization
   * Replication status

5. Compare producer and consumer rates:

   * Incoming message volume
   * Processing throughput
   * Backlog growth rate

6. Check dead-letter queues:

   * Failed message count
   * Retry frequency
   * Poison message patterns

## Immediate Mitigation

1. **Scale Consumer Fleet**

   Kubernetes:

   ```bash
   kubectl scale deployment <consumer-deployment> --replicas=10
   ```

   Increase processing capacity immediately.

2. **Restart Failed Consumers**

   * Recover crashed workers
   * Restore processing capacity
   * Verify successful startup

3. **Reprocess Backlogged Messages**

   * Drain retry queues
   * Replay messages from DLQ if appropriate
   * Prioritize critical business events

4. **Reduce Producer Throughput**

   * Temporarily throttle event generation
   * Protect downstream systems
   * Prevent backlog acceleration

5. **Optimize Consumer Concurrency**

   * Increase worker threads
   * Increase batch processing size
   * Improve parallelism

6. **Address Dependency Bottlenecks**

   * Scale databases
   * Restore external services
   * Resolve cache issues

## Long-term Resolution

1. **Consumer Autoscaling**

   * Scale based on queue depth
   * Scale based on consumer lag
   * Scale based on oldest message age

2. **Improve Consumer Reliability**

   * Handle failures gracefully
   * Implement retry policies
   * Prevent consumer crashes

3. **Optimize Processing Logic**

   * Reduce processing latency
   * Batch database operations
   * Improve external API efficiency

4. **Poison Message Handling**

   * Implement dead-letter queues
   * Detect malformed payloads
   * Prevent infinite retry loops

5. **Capacity Planning**

   * Forecast message volume growth
   * Benchmark consumer throughput
   * Maintain operational headroom

6. **Dependency Resilience**

   * Add circuit breakers
   * Cache external responses
   * Reduce dependency bottlenecks

7. **Monitoring & Alerting**

   * Alert on queue depth growth
   * Alert on consumer lag
   * Track consumer crash rates
   * Monitor oldest message age

## Escalation

* If queue depth continues increasing for more than 10 minutes: page service owner
* If consumer lag exceeds SLA thresholds: declare incident
* If consumers repeatedly crash: escalate to application team
* If queue backlog impacts customer-facing workflows: engage incident commander
* If broker infrastructure becomes unhealthy: involve platform engineering team

## Success Criteria

* Queue depth returns to normal levels
* Consumer throughput exceeds producer throughput
* Consumer lag returns to baseline
* Oldest message age decreases steadily
* Dead-letter queue growth stops
* No consumer crashes observed
* Business event processing restored
* No queue-related alerts active for 30 minutes
