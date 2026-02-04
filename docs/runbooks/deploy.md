# Runbook — Deploy

Last Updated: 2026-02-03

## Environments
- **Development:** Docker Compose + LocalStack (S3, SQS)
  - URL: http://localhost:8000 (API), http://localhost:3002 (App UI)
  - Database: PostgreSQL 16 + PostGIS 3.4 (local Docker)
  - S3/SQS: LocalStack (http://localhost:4566)

- **Staging:** (Planned) AWS ECS + RDS + S3 + SQS
  - URL: https://staging-api.vivacampo.com
  - Database: RDS PostgreSQL 16 + PostGIS
  - S3: vivacampo-staging-rasters
  - SQS: vivacampo-staging-jobs

- **Production:** (Future) AWS ECS + RDS + S3 + SQS + CloudFront
  - URL: https://api.vivacampo.com
  - Database: RDS PostgreSQL 16 + PostGIS (Multi-AZ)
  - S3: vivacampo-prod-rasters (with versioning)
  - SQS: vivacampo-prod-jobs

---

## Preconditions
- [ ] CI green (all tests passing)
- [ ] Migrations reviewed and tested on staging
- [ ] Secrets available in AWS Secrets Manager
- [ ] Rollback plan ready (see `rollback.md`)
- [ ] Team notified (Slack/Discord)

---

## Deploy Steps (Development)

### 1. Start Infrastructure
```bash
cd c:\projects\vivacampo-app
docker compose up -d db redis localstack
```

### 2. Wait for Services
```bash
# Wait 30 seconds for services to be ready
timeout /t 30
```

### 3. Apply Migrations
```bash
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/001_initial_schema.sql
docker compose exec -T db psql -U vivacampo -d vivacampo < infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql
```

### 4. Start Services
```bash
# Option A: All services
docker compose up -d

# Option B: Individual services (for development)
cd services/api
uvicorn app.main:app --reload --port 8000

cd services/worker
python -m worker.main

cd services/app-ui
npm run dev
```

### 5. Verify Health
```bash
# API health check
curl http://localhost:8000/health

# Database check
docker compose exec db psql -U vivacampo -d vivacampo -c "SELECT COUNT(*) FROM aois;"

# Redis check
docker compose exec redis redis-cli ping
```

---

## Deploy Steps (Staging)

### 1. Build Docker Images
```bash
# Build all services
docker compose build

# Tag for ECR
docker tag vivacampo-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-api:staging
docker tag vivacampo-worker:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-worker:staging
docker tag vivacampo-tiler:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-tiler:staging
```

### 2. Push to ECR
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# Push images
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-api:staging
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-worker:staging
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/vivacampo-tiler:staging
```

### 3. Apply Migrations
```bash
# Connect to RDS
psql -h vivacampo-staging.xxxx.us-east-1.rds.amazonaws.com -U vivacampo -d vivacampo

# Run migrations
\i infra/migrations/sql/001_initial_schema.sql
\i infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql
```

### 4. Update ECS Services
```bash
# Update API service
aws ecs update-service --cluster vivacampo-staging --service api --force-new-deployment

# Update Worker service
aws ecs update-service --cluster vivacampo-staging --service worker --force-new-deployment

# Update Tiler service
aws ecs update-service --cluster vivacampo-staging --service tiler --force-new-deployment
```

### 5. Verify Deployment
```bash
# Health check
curl https://staging-api.vivacampo.com/health

# Check ECS task status
aws ecs describe-services --cluster vivacampo-staging --services api worker tiler

# Check logs
aws logs tail /ecs/vivacampo-staging/api --follow
```

### 6. Smoke Tests
```bash
# Run smoke tests
pytest tests/smoke/ --env=staging

# Manual checks:
# - Login to staging UI
# - Create test AOI
# - Verify map tiles load
# - Check logs for errors
```

---

## Deploy Steps (Production)

**⚠️ CRITICAL: Production deploys require approval from 2 team members.**

### 1. Pre-deploy Checklist
- [ ] Staging deploy successful
- [ ] Smoke tests passed
- [ ] Performance tests passed (p95 <500ms)
- [ ] Security scan passed (no critical vulnerabilities)
- [ ] Database backup created (within last 24h)
- [ ] Rollback plan reviewed

### 2. Deploy (same as staging, but with `prod` tags)
```bash
# Build and push to ECR (prod tags)
# Apply migrations (on prod RDS)
# Update ECS services (prod cluster)
```

### 3. Verify Deployment
```bash
# Health check
curl https://api.vivacampo.com/health

# Monitor metrics (Grafana)
# - Error rate <1%
# - Latency p95 <500ms
# - CPU/Memory usage normal
```

### 4. Post-deploy
- [ ] Update `docs/CHANGELOG_INTERNAL.md`
- [ ] Update `ai/handoff.md` with next step
- [ ] Notify team (Slack/Discord)
- [ ] Monitor for 1 hour (watch for errors, performance degradation)

---

## Rollback Procedure
See `rollback.md` for detailed rollback steps.

**Quick rollback:**
```bash
# Revert to previous ECS task definition
aws ecs update-service --cluster vivacampo-prod --service api --task-definition vivacampo-api:123

# Verify health
curl https://api.vivacampo.com/health
```

---

## Common Issues

### Issue: Migration fails
**Symptom:** `psql` returns error during migration
**Solution:**
1. Check if migration already applied: `SELECT * FROM schema_migrations;`
2. If partial migration, manually rollback changes
3. Fix migration SQL, re-run

### Issue: ECS task fails to start
**Symptom:** Task status = STOPPED, exit code 1
**Solution:**
1. Check logs: `aws logs tail /ecs/vivacampo-prod/api`
2. Common causes: missing env vars, DB connection failure, port conflict
3. Fix issue, redeploy

### Issue: High error rate after deploy
**Symptom:** Error rate >5% in Grafana
**Solution:**
1. Check logs for error patterns
2. If widespread, rollback immediately
3. If isolated, investigate specific endpoint

---

## Last Updated
2026-02-03
