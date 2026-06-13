# SSL Certificate Expired Runbook

## Symptoms

* TLS/SSL handshake failures
* Increased connection failures between services
* HTTPS requests failing with certificate validation errors
* Browser security warnings for customer-facing applications
* API clients rejecting secure connections
* Service-to-service communication failures over TLS
* Sudden increase in authentication or gateway errors
* Monitoring alerts indicating certificate expiration

## Root Causes

1. **Expired SSL/TLS Certificate**

   * Certificate validity period exceeded
   * Renewal process failed
   * Certificate management automation malfunctioned

2. **Failed Certificate Renewal**

   * ACME/Let's Encrypt renewal errors
   * DNS validation failures
   * Expired automation credentials
   * Renewal jobs not executed

3. **Certificate Deployment Failure**

   * New certificate generated but not deployed
   * Incorrect certificate installed
   * Certificate chain missing intermediate certificates

4. **Configuration Errors**

   * Wrong certificate referenced in configuration
   * Incorrect keystore or truststore settings
   * Expired certificate still being served

5. **Certificate Authority Issues**

   * Revoked certificate
   * Invalid certificate chain
   * Untrusted certificate authority

6. **Service Reload Failure**

   * Certificate updated but service not restarted
   * Load balancer still serving old certificate
   * Reverse proxy configuration not refreshed

7. **Time Synchronization Issues**

   * Incorrect system clock
   * NTP failures causing certificate validation errors
   * Future-dated certificate validation failures

## Detection Steps

1. Review application and proxy logs:

   Search for:

   * `certificate expired`
   * `TLS handshake failed`
   * `x509 certificate has expired`
   * `SSL validation error`

2. Inspect certificate validity:

   ```bash
   openssl x509 -in certificate.crt -text -noout
   ```

   Check:

   * Expiration date
   * Issuer
   * Subject Alternative Names (SANs)

3. Verify endpoint certificate:

   ```bash
   openssl s_client -connect example.com:443
   ```

   Confirm:

   * Active certificate
   * Certificate chain
   * Expiration status

4. Check monitoring systems:

   * Certificate expiration alerts
   * TLS error rates
   * Connection failure metrics

5. Verify system time:

   ```bash
   date
   timedatectl status
   ```

6. Inspect certificate automation:

   * Renewal job status
   * ACME logs
   * Certificate management platform events

## Immediate Mitigation

1. **Renew Certificate**

   * Generate a new certificate
   * Complete CA validation process
   * Verify certificate integrity

2. **Deploy Updated Certificate**

   * Replace expired certificate files
   * Update secrets or keystores
   * Validate certificate chain

3. **Reload Services**

   Examples:

   ```bash
   systemctl reload nginx
   ```

   ```bash
   kubectl rollout restart deployment/<deployment-name>
   ```

   Ensure applications begin serving the new certificate.

4. **Verify TLS Functionality**

   * Test HTTPS endpoints
   * Confirm certificate validity
   * Validate client connectivity

5. **Update Load Balancers and Proxies**

   * Reload ingress controllers
   * Refresh reverse proxy configurations
   * Verify edge certificates

6. **Restore Customer Access**

   * Confirm browser trust
   * Validate API client connections
   * Monitor error rates during recovery

## Long-term Resolution

1. **Automated Certificate Renewal**

   * ACME-based renewal automation
   * Managed certificate services
   * Automated deployment workflows

2. **Certificate Monitoring**

   * Alert at 60, 30, 14, and 7 days before expiration
   * Track certificate inventory
   * Monitor renewal success rates

3. **Certificate Lifecycle Management**

   * Centralized certificate management
   * Ownership tracking
   * Renewal documentation

4. **Deployment Validation**

   * Verify certificate installation automatically
   * Validate certificate chains after deployment
   * Test endpoint trust continuously

5. **Redundancy and Failover**

   * Backup certificates
   * Secondary certificate authorities
   * Disaster recovery procedures

6. **Configuration Management**

   * Infrastructure-as-code for TLS configuration
   * Version-controlled certificate deployment
   * Automated compliance checks

7. **Operational Readiness**

   * Regular certificate audits
   * Expiration drills
   * Renewal process testing

## Escalation

* If customer-facing HTTPS services are unavailable: declare incident immediately
* If critical internal service communication fails due to TLS errors: page service owner
* If certificate renewal automation fails: engage platform engineering
* If multiple services are affected by certificate expiration: escalate to incident commander
* If certificate authority issues prevent renewal: contact CA support immediately

## Success Criteria

* Valid certificate deployed successfully
* TLS handshake success rate returns to baseline
* HTTPS endpoints accessible without warnings
* Service-to-service TLS communication restored
* Connection failure rates normalize
* Certificate monitoring confirms healthy validity period
* No certificate-related alerts active
* All affected services operating normally for 30 minutes
