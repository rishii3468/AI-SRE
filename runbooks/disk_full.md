# Disk Full Runbook

## Symptoms
- "No space left on device" errors in logs
- Service write operations failing
- Database unable to accept connections
- Application crashes with OOM or write-error
- Alert: "Disk usage > 90%"

## Root Causes
1. **Log Accumulation** - Application/system logs growing without rotation
2. **Temporary File Buildup** - Cache, tmp, or downloaded files not cleaned
3. **Database Growth** - Transaction logs, WAL (write-ahead logs) not archived
4. **Backup Retention** - Old backups retained longer than policy
5. **Metrics/Monitoring Data** - Time-series databases or trace files growing
6. **Incorrectly Sized Volume** - Underestimated storage needs during planning

## Detection Steps
1. Check disk usage:
   - `df -h` on the affected host
   - `kubectl exec pod_name -- df -h` in Kubernetes
2. Find large files/directories:
   - `du -sh /* | sort -h` (top-level directories)
   - `find / -size +1G -type f 2>/dev/null | head -20`
3. Check specific directories:
   - Logs: `du -sh /var/log/*`
   - Database: `du -sh /var/lib/postgresql`
   - Tmp: `du -sh /tmp`
4. Monitor growth rate:
   - Check how fast disk is filling
   - Estimate time to 100% (urgency indicator)

## Immediate Mitigation (0-10 minutes)
1. **Emergency log cleanup** (lowest risk):
   - Rotate current logs: `logrotate -f /etc/logrotate.conf`
   - Remove old logs: `find /var/log -name "*.log.*.gz" -mtime +7 -delete`
   - Frees 10-50GB typically
2. **Clean temporary files**:
   - Clear temp dir: `rm -rf /tmp/* /var/tmp/*`
   - Clear cache: `rm -rf ~/.cache/*`
3. **Archive old backups** (if safe):
   - Move to external storage: `mv /backup/old_backup.tar.gz /mnt/archive/`
   - Frees space immediately
4. **Restart database** (last resort):
   - Forces checkpoint and WAL cleanup
   - Brief service interruption

## Long-term Resolution
1. **Log Management**:
   - Implement log rotation policy (daily, keep 7 days)
   - Compress old logs (gzip reduces by 90%)
   - Send logs to centralized logging (remove local copies)
   - Example: `logrotate.conf` compress, rotate daily, keep 14 days
2. **Database Maintenance**:
   - Archive WAL files periodically
   - Set `max_wal_size` appropriately (default 1GB, may need 10-50GB)
   - Implement automated WAL archival to S3/GCS
3. **Capacity Planning**:
   - Monitor disk growth trend over time
   - Add 50% headroom to peak projected usage
   - Use auto-expanding volumes when available
4. **Monitoring**:
   - Alert at 70% disk usage
   - Alert at 80% disk usage (page SRE)
   - Track daily growth rate
   - Set up trend monitoring for predictive scaling

## Prevention
- Set up automated cleanup jobs (cron):
  ```bash
  # Daily log cleanup
  0 2 * * * find /var/log -name "*.log.*" -mtime +30 -delete
  
  # Weekly backup cleanup
  0 3 * * 0 find /backup -name "*.tar.gz" -mtime +60 -delete
  ```
- Use disk quotas for users/applications
- Enable filesystem compression where available

## Escalation
- If still >90% after mitigation: page infrastructure team
- If approaching 100%: consider emergency service shutdown
- If repeated issue: escalate to capacity planning meeting