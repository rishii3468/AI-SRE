# Deployment Failure Runbook

## Symptoms

* Application errors begin immediately after a deployment
* Increased HTTP 5xx responses following a release
* New pods fail health checks or enter CrashLoopBackOff
* Service latency increases after rollout
* Customer-facing functionality becomes unavailable or degraded
* Deployment rollout stalls or fails to complete
* Elevated error rates in monitoring dashboards
* Successful rollback restores service health

## Root Causes

1. **Bad Build Artifact**

   * Defective application code introduced in the release
   * Missing runtime dependencies
   * Corrupted container image
   * Packaging or build pipeline errors

2. **Configuration Mismatch**

   * Application expects configuration not present in production
   * Missing environment variables
   * Incorrect ConfigMap or Secret values
   * Environment-specific settings not updated

3. **Database Schema Incompatibility**

   * Application deployed before required database migration
   * Breaking schema changes
   * Missing tables, columns, or indexes

4. **Dependency Version Conflict**

   * Incompatible library upgrades
   * API contract changes
   * Runtime version mismatch

5. **Infrastructure Misconfiguration**

   * Incorrect Kubernetes manifests
   * Invalid ingress or load balancer settings
   * Resource limits causing startup failures

6. **Deployment Pipeline Error**

   * Wrong image tag deployed
   * Partial deployment execution
   * Failed artifact promotion

7. **Feature Flag Misconfiguration**

   * Incomplete feature rollout
   * Incorrect feature flag targeting
   * New functionality enabled without required dependencies

## Detection Steps

1. Identify deployment timing:

   ```bash
   kubectl rollout history deployment/<deployment-name>
   ```

   Verify:

   * Recent deployments
   * Deployment timestamps
   * Revision changes

2. Check application logs:

   ```bash
   kubectl logs <pod-name>
   ```

   Look for:

   * Startup failures
   * Configuration validation errors
   * Dependency initialization failures
   * Runtime exceptions

3. Review deployment status:

   ```bash
   kubectl rollout status deployment/<deployment-name>
   kubectl describe deployment <deployment-name>
   ```

4. Compare previous and current releases:

   ```bash
   kubectl diff
   ```

   Check:

   * Environment variables
   * Secrets
   * ConfigMaps
   * Resource limits

5. Verify artifact integrity:

   * Confirm image tag
   * Verify build version
   * Validate deployment package contents

6. Review monitoring dashboards:

   * Error rate spikes
   * Latency increases
   * Pod restart counts
   * Availability metrics

## Immediate Mitigation

1. **Rollback Deployment**

   If customer impact is ongoing:

   ```bash
   kubectl rollout undo deployment/<deployment-name>
   ```

   Restore the last known healthy version.

2. **Pause Further Rollouts**

   Prevent additional impact:

   ```bash
   kubectl rollout pause deployment/<deployment-name>
   ```

3. **Validate Configuration**

   * Confirm environment variables exist
   * Verify ConfigMaps and Secrets
   * Compare production and staging settings

4. **Verify Release Artifacts**

   * Check image version
   * Validate build checksums
   * Confirm deployment references correct artifact

5. **Disable New Features**

   * Turn off recently introduced feature flags
   * Reduce blast radius while investigating

6. **Restore Service Availability**

   * Route traffic to stable instances
   * Scale healthy replicas
   * Use previous release if necessary

## Long-term Resolution

1. **Deployment Validation**

   * Automated deployment verification
   * Pre-release smoke tests
   * Health-check validation gates

2. **Artifact Verification**

   * Signed release artifacts
   * Build integrity validation
   * Automated version consistency checks

3. **Configuration Management**

   * Configuration schema validation
   * Environment parity checks
   * Automated secret verification

4. **Progressive Delivery**

   * Canary deployments
   * Blue-green deployments
   * Gradual traffic shifting

5. **Automated Rollbacks**

   * Roll back automatically on elevated error rates
   * Roll back on failed health checks
   * Roll back on latency regressions

6. **Release Testing**

   * End-to-end integration tests
   * Production-like staging environments
   * Dependency compatibility testing

7. **Monitoring & Alerting**

   * Alert on post-deployment error spikes
   * Track deployment success rates
   * Monitor rollback frequency
   * Correlate incidents with release events

## Escalation

* If customer-facing errors begin immediately after deployment: page service owner
* If rollback does not restore service: escalate to engineering lead
* If multiple services are affected by the release: declare incident
* If deployment impacts critical business workflows: engage incident commander
* If root cause is CI/CD related: involve platform engineering team

## Success Criteria

* Error rates return to baseline
* Deployment stabilizes successfully
* Health checks pass consistently
* Service availability restored
* Customer-facing functionality operational
* Root cause identified and documented
* Release artifacts validated and approved
* No deployment-related alerts observed for 30 minutes
