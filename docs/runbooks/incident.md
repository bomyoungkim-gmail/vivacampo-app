# Runbook — Incident Response

Last Updated: 2026-02-03

## Incident Severity Levels

| Severity | Definition | Response Time | Example |
|----------|------------|---------------|---------|
| **P0 - Critical** | Complete service outage, data loss risk | Immediate (24/7) | Database down, API returning 500 for all requests |
| **P1 - High** | Major feature broken, >50% users affected | <30 minutes | Login broken, map tiles not loading |
| **P2 - Medium** | Minor feature broken, <50% users affected | <2 hours | Chart not displaying, slow performance |
| **P3 - Low** | Cosmetic issue, workaround available | <24 hours | UI alignment issue, typo |

---

## Incident Response Process

### 1. Triage (First 5 Minutes)

**Assess severity:**
- [ ] What is broken?
- [ ] How many users affected?
- [ ] Is data at risk?
- [ ] Is there a workaround?

**Assign severity level:** P0 / P1 / P2 / P3

**Notify team:**
```
@channel INCIDENT P1
Issue: [brief description]
Impact: [% users affected]
Incident lead: @name
Status: Investigating
```

**Start incident log:**
Create file: `docs/runbooks/incidents/YYYY-MM-DD-HH-MM-incident-name.md`

---

### 2. Immediate Actions (First 15 Minutes)

**Stabilize the system:**
- [ ] Identify failing component (API / Worker / Tiler / Database)
- [ ] Check recent deploys (was there a recent change?)
- [ ] Check logs for error patterns
- [ ] Check metrics (error rate, latency, CPU, memory)

**Mitigation options:**
1. **Rollback** (if recent deploy caused issue) - See `rollback.md`
2. **Scale up** (if resource exhaustion) - Increase ECS task count
3. **Disable feature** (if specific feature broken) - Feature flag
4. **Restart service** (if transient issue) - Restart ECS tasks

**Communicate status:**
```
UPDATE: [what we found]
Action: [what we're doing]
ETA: [when we expect resolution]
```

---

### 3. Investigation (Parallel with Mitigation)

**Gather evidence:**
- [ ] Logs (API, Worker, Tiler)
- [ ] Metrics (error rate, latency, CPU, memory)
- [ ] Recent deploys (what changed?)
- [ ] Database queries (slow queries, locks)
- [ ] External dependencies (Sentinel Hub, Open-Meteo)

**Common investigation commands:**

**Check API logs:**
```bash
aws logs tail /ecs/vivacampo-prod/api --follow --filter-pattern "ERROR"
```

**Check Worker logs:**
```bash
aws logs tail /ecs/vivacampo-prod/worker --follow --filter-pattern "ERROR"
```

**Check database connections:**
```sql
SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';
```

**Check slow queries:**
```sql
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Check ECS task status:**
```bash
aws ecs describe-services --cluster vivacampo-prod --services api worker tiler
```

---

### 4. Resolution

**Apply fix:**
- [ ] Deploy hotfix (if code change needed)
- [ ] Apply database fix (if data corruption)
- [ ] Restart services (if transient issue)
- [ ] Scale up (if capacity issue)

**Verify fix:**
- [ ] Error rate back to normal (<1%)
- [ ] Latency back to normal (<500ms p95)
- [ ] Manual testing (login, AOI creation, map display)
- [ ] No new errors in logs

**Communicate resolution:**
```
RESOLVED: [brief description]
Root cause: [what caused it]
Fix: [what we did]
Duration: [XX minutes]
```

---

### 5. Post-Incident Review (Within 24 Hours)

**Complete incident report:**
- Timeline (when did it start, when detected, when resolved)
- Root cause analysis (why did it happen?)
- Impact assessment (how many users, revenue impact?)
- What went well / What went poorly
- Action items (how to prevent recurrence)

**Template:** See `docs/runbooks/incidents/TEMPLATE.md`

**Create follow-up tasks:**
Add to `ai/tasks.md`:
- [ ] Fix root cause
- [ ] Add test to prevent recurrence
- [ ] Add monitoring/alert for early detection
- [ ] Update runbooks

---

## Common Incident Scenarios

### Scenario 1: Database Connection Pool Exhausted
**Symptoms:**
- API returns 500 errors
- Logs: "FATAL: sorry, too many clients already"

**Investigation:**
```sql
SELECT COUNT(*) FROM pg_stat_activity;
-- If count > max_connections (default 100), pool exhausted
```

**Immediate fix:**
```bash
# Restart API service (releases connections)
aws ecs update-service --cluster vivacampo-prod --service api --force-new-deployment
```

**Root cause:** Connection leak (not closing connections).

**Prevention:**
- Use connection pooling (SQLAlchemy pool)
- Add connection timeout
- Monitor connection count

---

### Scenario 2: S3 Bucket Full / Quota Exceeded
**Symptoms:**
- Worker jobs fail with "Access Denied"
- Logs: "S3 upload failed"

**Investigation:**
```bash
# Check S3 bucket size
aws s3 ls s3://vivacampo-prod-rasters --recursive --summarize
```

**Immediate fix:**
- Increase S3 quota (AWS console)
- Delete old/unused files

**Root cause:** No cleanup policy for old rasters.

**Prevention:**
- Add S3 lifecycle policy (delete files >90 days)
- Add monitoring for bucket size

---

### Scenario 3: TiTiler Slow / Unresponsive
**Symptoms:**
- Map tiles load slowly (>5 seconds)
- Logs: "Timeout reading from S3"

**Investigation:**
```bash
# Check TiTiler task CPU/memory
aws ecs describe-tasks --cluster vivacampo-prod --tasks <task-id>
```

**Immediate fix:**
```bash
# Scale up TiTiler tasks
aws ecs update-service --cluster vivacampo-prod --service tiler --desired-count 4
```

**Root cause:** High traffic, insufficient capacity.

**Prevention:**
- Add auto-scaling for TiTiler
- Add Redis caching layer

---

### Scenario 4: Worker Jobs Stuck in Queue
**Symptoms:**
- SQS queue depth increasing
- Jobs not processing

**Investigation:**
```bash
# Check SQS queue depth
aws sqs get-queue-attributes --queue-url <url> --attribute-names ApproximateNumberOfMessages
```

**Immediate fix:**
```bash
# Scale up Worker tasks
aws ecs update-service --cluster vivacampo-prod --service worker --desired-count 4
```

**Root cause:** Worker crash loop or infinite job.

**Prevention:**
- Add job timeout (max 5 minutes)
- Add dead-letter queue for failed jobs
- Add monitoring for queue depth

---

## Incident Communication Template

**Initial notification:**
```
@channel INCIDENT P1
Issue: API returning 500 errors for /v1/aois endpoint
Impact: ~80% of users cannot create AOIs
Incident lead: @alice
Status: Investigating
Started: 14:30 UTC
```

**Update (every 15 minutes):**
```
UPDATE 14:45 UTC
Found: Database connection pool exhausted
Action: Restarting API service
ETA: 5 minutes
```

**Resolution:**
```
RESOLVED 14:52 UTC
Issue: Database connection pool exhausted
Root cause: Connection leak in AOI creation endpoint
Fix: Restarted API service, deployed hotfix
Duration: 22 minutes
Impact: ~200 users affected
Post-mortem: Will be published within 24h
```

---

## Last Updated
2026-02-03
