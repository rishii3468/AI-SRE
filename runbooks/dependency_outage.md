# Dependency Outage Runbook

## Symptoms

* External API requests failing with HTTP 5xx errors
* Increased request timeouts when calling third-party services
* Elevated application error rates
* API latency spikes affecting downstream user requests
* Circuit breakers opening for external dependencies
* Queue backlogs growing due to failed outbound requests
* Increased retry activity in application logs
* Partial feature degradation while core platform remains operational

## Root Causes

1. **Third-Party Service Downtime**

   * External provider experiencing outage
   * Service unavailable due to maintenance or incident
   * Regional outage affecting provider infrastructure

2. **Third-Party API Degradation**

   * Increased response times
   * Partial service functionality unavailable
   * Intermittent request failures

3. **Network Connectivity Issues**

   * DNS resolution failures
   * Internet routing problems
   * Firewall or proxy issues blocking outbound traffic

4. **Rate Limiting**

   * API quota exceeded
   * Excessive request volume triggering provider limits
   * Misconfigured client causing request spikes

5. **Authentication or Credential Failures**

   * Expired API keys or tokens
   * Invalid credentials
   * Third-party authentication service outage

6. **Retry Storm Amplification**

   * Excessive retries overwhelming dependency
   * Cascading failures across multiple services
   * Poor retry configuration causing resource exhaustion

## Detection Steps

1. Check application logs:

   ```bash
   grep "timeout\|connection refused\|5.." /var/log/application.log
   ```

   Look for:

   * HTTP 500, 502, 503, 504 responses
   * Connection timeouts
   * DNS resolution failures
   * Authentication errors

2. Review dependency metrics:

   * `external_api_success_rate`
   * `external_api_latency_p95`
   * `external_api_timeout_rate`
   * `circuit_breaker_state`

3. Verify external endpoint availability:

   ```bash
   curl https://api.vendor.com/health
   ```

4. Check DNS resolution:

   ```bash
   nslookup api.vendor.com
   dig api.vendor.com
   ```

5. Review provider status page:

   * Active incidents
   * Maintenance windows
   * Regional outages

6. Check retry volume:

   * Increased outbound request count
   * Queue backlog growth
   * Connection pool exhaustion

## Immediate Mitigation

1. **Enable Fallback Mechanisms**

   * Serve cached or stale data
   * Use secondary providers if available
   * Degrade non-critical functionality gracefully

2. **Enable Circuit Breakers**

   * Stop sending requests to failing dependency
   * Prevent resource exhaustion
   * Reduce cascading failures

3. **Implement Exponential Backoff**

   * Retry transient failures only
   * Add jitter to prevent synchronized retries
   * Limit maximum retry attempts

4. **Reduce Dependency Traffic**

   * Disable non-essential API calls
   * Increase cache TTL temporarily
   * Batch requests where possible

5. **Preserve Core Functionality**

   * Prioritize critical user workflows
   * Disable optional integrations
   * Route traffic away from affected features

6. **Communicate Impact**

   * Update incident status page
   * Inform stakeholders of degraded functionality
   * Track provider recovery updates

## Long-term Resolution

1. **Multi-Provider Architecture**

   * Support failover to backup providers
   * Avoid single points of dependency failure
   * Implement provider selection logic

2. **Circuit Breaker Strategy**

   * Automatic failure detection
   * Controlled recovery testing
   * Per-dependency isolation

3. **Resilient Retry Policies**

   * Exponential backoff with jitter
   * Retry only idempotent operations
   * Enforce retry budgets

4. **Caching & Fallback Design**

   * Cache frequently requested data
   * Serve stale responses during outages
   * Implement graceful degradation paths

5. **Dependency Monitoring**

   * Track availability and latency
   * Alert on error rate anomalies
   * Monitor provider status endpoints

6. **Rate Limiting Controls**

   * Protect dependencies from traffic spikes
   * Avoid quota exhaustion
   * Manage retry amplification

7. **Business Continuity Planning**

   * Define acceptable degraded modes
   * Document manual fallback procedures
   * Regularly test outage scenarios

## Escalation

* If dependency outage lasts more than 10 minutes: page service owner
* If critical customer workflows are impacted: declare incident
* If failure rate exceeds 20%: activate degraded mode immediately
* If fallback systems fail: escalate to engineering leadership
* If outage exceeds SLA commitments: engage vendor support and incident management teams

## Success Criteria

* External API success rate returns to baseline
* Request latency normalizes
* Circuit breakers close successfully
* Retry rates return to normal levels
* Queue backlogs are cleared
* Customer-facing functionality restored
* No dependency-related alerts observed for 30 minutes
