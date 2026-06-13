# Service Discovery Failure Runbook

## Symptoms

* Services cannot locate or connect to dependent services
* Increased "service not found" or "endpoint unavailable" errors
* Inter-service communication failures
* HTTP 503/504 responses from downstream dependencies
* New service instances receive no traffic
* Requests fail despite healthy application instances
* Load balancers report no available backends
* Distributed systems report missing cluster members

## Root Causes

1. **Service Registry Outage**

   * Service discovery platform unavailable
   * Registry database failure
   * Registry cluster quorum loss
   * Infrastructure outage affecting registry nodes

2. **Service Registration Failure**

   * Services fail to register on startup
   * Registration credentials invalid
   * Registration API unavailable
   * Startup sequence issues preventing registration

3. **Health Check Failures**

   * Services incorrectly marked unhealthy
   * Misconfigured health checks
   * Temporary dependency failures causing deregistration

4. **Network Connectivity Issues**

   * Services unable to reach registry
   * Firewall rules blocking registration traffic
   * DNS resolution failures
   * Routing problems

5. **Configuration Errors**

   * Incorrect registry endpoint configuration
   * Wrong service names
   * Namespace or environment mismatches
   * Invalid service discovery settings

6. **Service Mesh or Discovery Agent Failure**

   * Consul agent failure
   * Eureka server issues
   * Kubernetes CoreDNS problems
   * Service mesh control plane outage

7. **Registry Data Corruption**

   * Missing service entries
   * Inconsistent registry state
   * Replication failures
   * Stale service metadata

## Detection Steps

1. Review application logs:

   Search for:

   * `service not found`
   * `endpoint unavailable`
   * `registration failed`
   * `unable to discover service`

2. Verify service registry health:

   Examples:

   ```bash
   curl http://registry:8500/v1/status/leader
   ```

   ```bash
   curl http://registry:8761/actuator/health
   ```

   Check:

   * Registry availability
   * Cluster status
   * Leader election health

3. Verify service registration:

   ```bash
   curl http://registry/services
   ```

   Confirm:

   * Expected services are registered
   * Endpoint metadata is correct
   * Service instances appear healthy

4. Check service health status:

   * Health check results
   * Registration timestamps
   * Deregistration events

5. Verify connectivity to registry:

   ```bash
   ping registry-host
   ```

   ```bash
   nc -vz registry-host 8500
   ```

6. Inspect infrastructure metrics:

   * Registry CPU and memory
   * Request error rates
   * Registration success rate
   * Discovery lookup latency

## Immediate Mitigation

1. **Restore Registry Availability**

   * Restart failed registry nodes
   * Recover quorum
   * Restore database connectivity
   * Fail over to standby registry if available

2. **Re-register Services**

   * Restart affected services
   * Trigger manual registration
   * Verify successful registration events

3. **Validate Service Discovery Configuration**

   * Confirm registry endpoints
   * Verify service names and namespaces
   * Check authentication credentials

4. **Use Static Endpoints Temporarily**

   * Configure direct service addresses
   * Bypass service discovery where operationally safe
   * Restore critical communication paths

5. **Restart Discovery Components**

   * Discovery agents
   * Sidecars
   * Service mesh control plane components
   * CoreDNS or registry services

6. **Restore Healthy Registry Data**

   * Recover from backups if required
   * Synchronize registry replicas
   * Rebuild missing service entries

## Long-term Resolution

1. **High Availability Registry**

   * Multi-node registry clusters
   * Automatic failover
   * Geographic redundancy
   * Quorum-based operation

2. **Registration Reliability**

   * Automatic re-registration
   * Registration retries with backoff
   * Startup validation checks

3. **Health Check Optimization**

   * Tune health-check thresholds
   * Prevent false deregistration
   * Separate readiness and liveness checks

4. **Configuration Management**

   * Standardized service discovery configuration
   * Environment validation
   * Automated configuration testing

5. **Monitoring & Alerting**

   * Alert on registry unavailability
   * Monitor registration success rates
   * Track discovery lookup failures
   * Alert on unexpected service deregistration

6. **Service Discovery Resilience**

   * Local service caching
   * Fallback endpoints
   * Discovery request circuit breakers

7. **Disaster Recovery Testing**

   * Simulate registry outages
   * Test service re-registration procedures
   * Validate failover workflows

## Escalation

* If critical services cannot discover dependencies for more than 5 minutes: page platform team
* If registry quorum is lost: escalate immediately to infrastructure engineering
* If customer-facing services are impacted: declare incident
* If multiple environments are affected: engage incident commander
* If service mesh or discovery infrastructure is failing globally: initiate major incident response

## Success Criteria

* Registry service is healthy and reachable
* All critical services successfully registered
* Service discovery lookups succeed
* Inter-service communication restored
* No missing service endpoints
* Registration success rate returns to baseline
* Application error rates normalize
* No service-discovery-related alerts observed for 30 minutes
