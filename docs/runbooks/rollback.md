# Runbook — Rollback

Last Updated: 2026-02-03

## When to Rollback
**Immediate rollback triggers:**
- Spike in 5xx errors (>5% for 5 minutes)
- Broken critical flow (AOI creation, map display, login)
- Data corruption risk (incorrect calculations, wrong tenant data)
- Security vulnerability discovered in deployed code

**Consider rollback:**
- Performance degradation (p95 latency >1000ms)
- Increased error rate (>2% for 15 minutes)
- Customer complaints about specific feature

**Do NOT rollback:**
- Minor UI bugs (can be fixed forward)
- Non-critical feature issues (can be disabled via feature flag)
- Single isolated error (investigate first)

---

## Rollback Strategy

### App Rollback (ECS)
**Strategy:** Redeploy previous ECS task definition (immutable deployments).

**Steps:**
1. Identify previous stable task definition:
   ```bash
   aws ecs list-task-definitions --family-prefix vivacampo-api --sort DESC
   # Example output: vivacampo-api:125 (current), vivacampo-api:124 (previous)
   ```

2. Update service to use previous task definition:
   ```bash
   aws ecs update-service \
     --cluster vivacampo-prod \
     --service api \
     --task-definition vivacampo-api:124
   ```

3. Repeat for Worker and Tiler services.

**Rollback time:** ~5 minutes (ECS task replacement)

---

### Migration Rollback
**Strategy:** Prefer forward-fix. If rollback needed, use down migration or restore snapshot.

**Expand/Contract Pattern (Preferred):**
- **Expand:** Add new columns/tables (safe, no rollback needed)
- **Contract:** Remove old columns/tables (only after code deployed)
- **Rollback:** Just redeploy old code (still works with expanded schema)

**Down Migration (If Necessary):**
1. Check if down migration exists:
   ```bash
   ls infra/migrations/sql/down/
   ```

2. Apply down migration:
   ```bash
   psql -h vivacampo-prod.xxxx.rds.amazonaws.com -U vivacampo -d vivacampo \
     -f infra/migrations/sql/down/002_revert_ai_assistant.sql
   ```

**Snapshot Restore (Last Resort):**
1. Identify latest snapshot:
   ```bash
   aws rds describe-db-snapshots \
     --db-instance-identifier vivacampo-prod \
     --query 'DBSnapshots[0].DBSnapshotIdentifier'
   ```

2. Restore snapshot (creates new RDS instance):
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier vivacampo-prod-restored \
     --db-snapshot-identifier vivacampo-prod-2026-02-03-06-00
   ```

3. Update DNS to point to new instance.

**⚠️ WARNING:** Snapshot restore loses all data since snapshot time. Only use if data corruption is severe.

---

## Rollback Steps (Production)

### 1. Assess Severity
- [ ] Check error rate (Grafana dashboard)
- [ ] Check customer impact (how many users affected?)
- [ ] Check logs for error patterns
- [ ] Decide: rollback or forward-fix?

### 2. Notify Team
```
@channel ROLLBACK IN PROGRESS
Reason: [brief description]
Affected services: [API/Worker/Tiler]
ETA: 5 minutes
```

### 3. Execute Rollback

**API Service:**
```bash
aws ecs update-service \
  --cluster vivacampo-prod \
  --service api \
  --task-definition vivacampo-api:124
```

**Worker Service:**
```bash
aws ecs update-service \
  --cluster vivacampo-prod \
  --service worker \
  --task-definition vivacampo-worker:124
```

**Tiler Service:**
```bash
aws ecs update-service \
  --cluster vivacampo-prod \
  --service tiler \
  --task-definition vivacampo-tiler:124
```

### 4. Verify Stability
```bash
# Health check
curl https://api.vivacampo.com/health

# Check ECS task status
aws ecs describe-services \
  --cluster vivacampo-prod \
  --services api worker tiler

# Monitor error rate (should drop to <1%)
# Monitor latency (should return to <500ms p95)
```

### 5. Verify Functionality
- [ ] Login works
- [ ] AOI creation works
- [ ] Map tiles load
- [ ] No errors in logs

### 6. Monitor for 30 Minutes
- [ ] Error rate stable (<1%)
- [ ] Latency stable (<500ms p95)
- [ ] No customer complaints

---

## After Rollback

### 1. Create Incident Note
Create file: `docs/runbooks/incidents/YYYY-MM-DD-incident-name.md`

**Template:**
```markdown
# Incident: [Brief Description]

Date: YYYY-MM-DD HH:MM
Severity: Critical / High / Medium
Duration: XX minutes
Affected users: XX%

## Timeline
- HH:MM: Deploy started
- HH:MM: Error rate spike detected
- HH:MM: Rollback initiated
- HH:MM: Rollback complete
- HH:MM: Stability confirmed

## Root Cause
[Detailed explanation]

## Impact
[What broke? How many users affected?]

## Resolution
[What fixed it?]

## Prevention
- [ ] Add test for this scenario
- [ ] Add alert for early detection
- [ ] Update deploy checklist
```

### 2. Create Follow-up Tasks
Add to `ai/tasks.md`:
- Fix root cause
- Add tests to prevent recurrence
- Update deploy checklist

### 3. Update Changelog
Add to `docs/CHANGELOG_INTERNAL.md`:
```markdown
## 2026-02-03
- Rollback: [brief description]
- Root cause: [brief explanation]
- Prevention: [what we'll do differently]
```

---

## Common Rollback Scenarios

### Scenario 1: API Breaking Change
**Symptom:** Frontend errors, 400/500 responses
**Rollback:** Redeploy previous API task definition
**Prevention:** API contract tests, backward compatibility checks

### Scenario 2: Database Migration Breaks Queries
**Symptom:** 500 errors, "column does not exist"
**Rollback:** Apply down migration OR redeploy old code (if expand/contract)
**Prevention:** Test migrations on staging, use expand/contract pattern

### Scenario 3: Worker Job Infinite Loop
**Symptom:** SQS queue backing up, high CPU usage
**Rollback:** Redeploy previous Worker task definition, purge SQS queue
**Prevention:** Add timeout to jobs, add circuit breaker

### Scenario 4: TiTiler Performance Degradation
**Symptom:** Slow map tile loading (>2s)
**Rollback:** Redeploy previous Tiler task definition
**Prevention:** Load testing before deploy, add caching layer

---

## Rollback Decision Matrix

| Error Rate | Latency | User Impact | Action |
|------------|---------|-------------|--------|
| >10% | Any | Any | **ROLLBACK IMMEDIATELY** |
| 5-10% | >1000ms | >50% users | **ROLLBACK** |
| 2-5% | 500-1000ms | 10-50% users | **Investigate, prepare rollback** |
| <2% | <500ms | <10% users | **Monitor, forward-fix** |

---

## Last Updated
2026-02-03
