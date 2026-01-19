import os
import json
import hashlib
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from worker.config import settings
from worker.shared.aws_clients import SQSClient

# Setup DB
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Setup SQS
sqs = SQSClient()

# Parameters
AOI_ID = "98fd8eb9-3d20-4180-ab4b-0e5272e20076" # Correct ID from DB query
TENANT_ID = "default-tenant" # Assuming default or needs lookup
# Let's find the tenant_id from the AOI
result = db.execute(text("SELECT tenant_id FROM aois WHERE id = :id"), {"id": AOI_ID}).fetchone()
if not result:
    print("AOI not found!")
    exit(1)
TENANT_ID = str(result[0])
print(f"Found Tenant ID: {TENANT_ID}")

JOB_TYPE = "BACKFILL"
# Backfill last 1 year (52 weeks)
FROM_DATE = "2025-01-01"
TO_DATE = "2026-01-18" # Today

pipeline_version = settings.pipeline_version
job_key = hashlib.sha256(
    f"{TENANT_ID}{AOI_ID}{FROM_DATE}{TO_DATE}{JOB_TYPE}{pipeline_version}".encode()
).hexdigest()

payload = {
    "tenant_id": TENANT_ID,
    "aoi_id": AOI_ID,
    "from_date": FROM_DATE,
    "to_date": TO_DATE
}

print(f"Creating job {JOB_TYPE}...")

sql = text("""
    INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
    VALUES (:tenant_id, :aoi_id, :job_type, :job_key, 'PENDING', :payload)
    ON CONFLICT (tenant_id, job_key) DO UPDATE 
    SET status = 'PENDING', updated_at = now()
    RETURNING id
""")

result = db.execute(sql, {
    "tenant_id": TENANT_ID,
    "aoi_id": AOI_ID,
    "job_type": JOB_TYPE,
    "job_key": job_key,
    "payload": json.dumps(payload)
})
db.commit()

row = result.fetchone()
if row:
    job_id = str(row[0])
    print(f"Job created with ID: {job_id}")
    
    # Send to SQS
    print("Sending to SQS...")
    sqs.send_message({
        "job_id": job_id,
        "job_type": JOB_TYPE,
        "payload": payload
    })
    print("Sent!")
else:
    print("Failed to create job (row is None).")

# Verify SQS
import time
print("Waiting 2s then checking SQS...")
time.sleep(2)
msgs = sqs.receive_messages(max_messages=10, wait_time=2)
print(f"Messages in queue: {len(msgs)}")
for m in msgs:
    print(f"Message ID: {m['MessageId']}, Body: {m['Body'][:50]}...")

