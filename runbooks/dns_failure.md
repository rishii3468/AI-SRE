# DNS Failure Runbook

## Symptoms

* Application logs contain "host not found" or "name resolution failed" errors
* Services unable to connect to dependencies using hostnames
* Increased request failures despite healthy target services
* HTTP 502/503/504 errors caused by upstream resolution failures
* Kubernetes services unable to discover other services
* External API calls failing with DNS lookup errors
* Sudden increase in connection timeout errors
* Multiple services experiencing connectivity issues simultaneously

## Root Causes

1. **DNS Provider Outage**

   * Upstream DNS provider unavailable
   * Managed DNS service experiencing incident
   * Regional DNS infrastructure failure

2. **Incorrect DNS Records**

   * Missing A, AAAA, CNAME, or SRV records
   * Incorrect IP address mappings
   * Misconfigured DNS zones
   * Failed DNS updates

3. **Resolver Failure**

   * Local DNS resolver unavailable
   * CoreDNS outage in Kubernetes
   * DNS forwarding configuration errors
   * Resolver resource exhaustion

4. **DNS Propagation Issues**

   * Recent DNS changes not fully propagated
   * Inconsistent responses across regions
   * Stale DNS caches

5. **Expired or Invalid Records**

   * Incorrect TTL settings
   * Zone configuration corruption
   * Record deletion or accidental modification

6. **Network Connectivity Problems**

   * Firewall blocking DNS traffic
   * UDP/TCP port 53 connectivity issues
   * Routing failures to DNS servers

7. **Service Discovery Failure**

   * Kubernetes CoreDNS malfunction
   * Service registry unavailable
   * Internal DNS synchronization issues

## Detection Steps

1. Check application logs:

   ```bash
   grep -i "dns\|host not found\|name resolution\|lookup failed" /var/log/application.log
   ```

   Look for:

   * NXDOMAIN responses
   * Temporary failure in name resolution
   * DNS timeout errors
   * Unknown host exceptions

2. Test DNS resolution:

   ```bash
   nslookup api.example.com
   dig api.example.com
   host api.example.com
   ```

3. Verify resolver configuration:

   ```bash
   cat /etc/resolv.conf
   ```

   Check:

   * Configured nameservers
   * Search domains
   * Resolver options

4. Validate DNS records:

   ```bash
   dig A api.example.com
   dig CNAME api.example.com
   ```

5. Check DNS server health:

   * Query response times
   * Resolver error rates
   * DNS infrastructure status

6. For Kubernetes environments:

   ```bash
   kubectl get pods -n kube-system
   kubectl logs -n kube-system deployment/coredns
   ```

   Look for:

   * CoreDNS crashes
   * Resolution failures
   * Plugin errors

## Immediate Mitigation

1. **Verify DNS Records**

   * Confirm required records exist
   * Validate IP addresses and aliases
   * Check recent DNS changes

2. **Switch DNS Resolver**

   * Temporarily use alternate resolvers
   * Redirect to secondary DNS infrastructure
   * Verify resolver availability

3. **Flush DNS Cache**

   Linux:

   ```bash
   systemd-resolve --flush-caches
   ```

   Kubernetes:

   * Restart affected application pods
   * Refresh cached DNS entries

4. **Use Direct IP Addresses (Temporary)**

   * Bypass DNS where operationally safe
   * Apply only as a short-term workaround

5. **Restart DNS Components**

   * Restart CoreDNS
   * Restart local DNS resolver services
   * Recover failed DNS pods

6. **Rollback Recent DNS Changes**

   * Restore previous known-good records
   * Revert zone modifications
   * Reapply validated configurations

## Long-term Resolution

1. **DNS High Availability**

   * Deploy redundant DNS infrastructure
   * Use multiple authoritative DNS providers
   * Configure resolver failover

2. **DNS Change Management**

   * Review and approve DNS modifications
   * Automate record validation
   * Maintain change audit trails

3. **Monitoring & Alerting**

   * Alert on DNS resolution failures
   * Track query latency and error rates
   * Monitor CoreDNS health

4. **Automated DNS Testing**

   * Continuous hostname resolution checks
   * Regional DNS validation
   * Service discovery verification

5. **Service Discovery Resilience**

   * Multi-instance CoreDNS deployment
   * DNS caching optimization
   * Backup service discovery mechanisms

6. **Configuration Management**

   * Version control DNS zones
   * Automated record deployment
   * Prevent manual configuration drift

7. **Capacity Planning**

   * Monitor DNS query volume
   * Scale DNS infrastructure proactively
   * Prevent resolver saturation

## Escalation

* If DNS failures impact multiple services: declare incident immediately
* If authoritative DNS provider is unavailable: contact provider support
* If CoreDNS remains unhealthy for more than 10 minutes: page platform team
* If customer-facing applications are affected: escalate to incident commander
* If service discovery failures impact production workloads: engage infrastructure engineering

## Success Criteria

* DNS queries resolve successfully
* Resolver error rates return to baseline
* Application connectivity restored
* Service discovery functioning normally
* No DNS-related alerts active
* CoreDNS and resolver services healthy
* Customer-facing error rates normalized
* Resolution success rate remains above 99.9%
