# Rate Limit Exceeded Runbook

## Symptoms

* Increased HTTP 429 ("Too Many Requests") responses
* API requests rejected despite healthy infrastructure
* Customer complaints about intermittent request failures
* Elevated retry activity from clients
* Sudden drop in successful request rate
* API latency spikes caused by retry amplification
* Third-party API quota exhaustion alerts
* Business workflows failing due to request throttling

## Root Causes

1. **Traffic Spike**

   * Sudden increase in legitimate user traffic
   * Product launch or marketing campaign
   * Automated client behavior generating excessive requests
   * Unexpected workload surge

2. **Misconfigured Rate Limits**

   * Limits set too low for normal traffic patterns
   * Incorrect per-user or per-IP thresholds
   * Aggressive global rate limiting policies
   * Configuration drift between environments

3. **Retry Storm**

   * Clients retrying failed requests aggressively
   * Missing exponential backoff
   * Cascading retries across services
   * Retry amplification during incidents

4. **Abusive or Bot Traffic**

   * Scrapers or automated systems
   * Credential stuffing attacks
   * API abuse
   * Malicious traffic spikes

5. **Third-Party API Quota Exhaustion**

   * Vendor API usage exceeds allocated quota
   * Shared credentials consumed by multiple services
   * Unexpected integration traffic growth

6. **Application Defects**

   * Infinite request loops
   * Polling frequency misconfiguration
   * Duplicate request generation
   * Background jobs exceeding expected request volume

7. **Uneven Traffic Distribution**

   * Hot users generating disproportionate traffic
   * Single IP consuming excessive quota
   * Load balancer routing imbalance

## Detection Steps

1. Review application logs:

   Search for:

   * HTTP 429 responses
   * Rate limit exceeded messages
   * Quota exhaustion errors
   * Retry-related warnings

2. Monitor API metrics:

   * `http_429_rate`
   * Request rate (RPS)
   * Success rate
   * Retry volume
   * API latency

3. Analyze traffic patterns:

   * Top users by request volume
   * Top IP addresses
   * Endpoint request distribution
   * Request spikes by time window

4. Verify rate-limit configuration:

   * Per-user limits
   * Per-IP limits
   * Global quotas
   * Third-party API quotas

5. Inspect retry behavior:

   * Client retry frequency
   * Retry backoff implementation
   * Request amplification factors

6. Review external provider dashboards:

   * API quota consumption
   * Vendor rate-limit metrics
   * Usage thresholds

## Immediate Mitigation

1. **Increase Quotas**

   * Raise API rate limits where safe
   * Expand third-party API quotas if available
   * Adjust temporary burst allowances

2. **Apply Throttling Controls**

   * Limit excessive clients
   * Protect backend services
   * Prioritize critical traffic

3. **Enable Exponential Backoff**

   * Reduce retry amplification
   * Add randomized jitter
   * Limit maximum retry attempts

4. **Block Abusive Traffic**

   * Restrict offending IPs
   * Apply WAF rules
   * Enforce client authentication requirements

5. **Scale Supporting Infrastructure**

   * Increase application capacity
   * Scale API gateways
   * Expand backend resources if limits are legitimate

6. **Prioritize Critical Workloads**

   * Reserve quota for essential business functions
   * Defer non-critical operations
   * Reduce background processing traffic

## Long-term Resolution

1. **Rate Limit Strategy Review**

   * Align limits with actual usage patterns
   * Separate user, application, and system quotas
   * Define burst handling policies

2. **Traffic Management**

   * Implement adaptive rate limiting
   * Use token bucket or leaky bucket algorithms
   * Dynamically adjust thresholds

3. **Retry Policy Improvements**

   * Mandatory exponential backoff
   * Retry budgets
   * Circuit breakers for failing services

4. **Capacity Planning**

   * Forecast traffic growth
   * Review quota requirements regularly
   * Maintain sufficient headroom

5. **Bot & Abuse Protection**

   * WAF integration
   * Behavioral analysis
   * Automated traffic filtering

6. **Monitoring & Alerting**

   * Alert on elevated 429 rates
   * Monitor quota consumption
   * Track retry amplification
   * Alert before quota exhaustion

7. **Client Education**

   * Publish rate-limit guidance
   * Encourage efficient API usage
   * Document retry best practices

## Escalation

* If 429 errors impact customer-facing workflows: page service owner
* If third-party quota exhaustion occurs: contact vendor support
* If traffic surge exceeds planned capacity: engage platform team
* If abusive traffic is suspected: involve security team
* If critical business operations are affected: declare incident

## Success Criteria

* HTTP 429 rates return to baseline
* Successful request rate normalizes
* Retry volume decreases
* API latency returns to expected levels
* Quota utilization remains within safe thresholds
* No active rate-limit-related alerts
* Customer-facing functionality restored
* Traffic patterns stabilized without excessive throttling
