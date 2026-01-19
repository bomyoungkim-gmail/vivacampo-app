# Frontend Loading Issue - Root Cause Analysis and Resolution

## 1. The Problem

Users reported that both the `app-ui` and `admin-ui` were getting stuck on an infinite loading screen after login.

## 2. Investigation Summary

My investigation followed these steps:

1.  **Initial Hypothesis:** The issue was likely caused by a hanging API request from the frontend.
2.  **Frontend Code Analysis:**
    *   I reviewed the login and dashboard pages for both `admin-ui` and `app-ui`.
    *   I confirmed that after login, the frontends make API calls to fetch initial data. For the `admin-ui`, this was a call to `/v1/admin/ops/health`.
    *   The loading indicators were designed to stop once these API calls completed (either successfully or with an error). The fact that they didn't stop pointed to the API calls never returning a response (timing out).
3.  **Backend API Analysis:**
    *   I traced the API endpoints and found they were protected by authentication dependencies (`get_current_system_admin` and `get_current_membership`).
    *   Crucially, both of these dependencies perform a database query to validate the user's token and permissions.
    *   This led me to suspect a problem with the database connection. A hanging database query in the authentication dependency would cause the entire API request to hang, which perfectly matched the symptoms observed in the frontend.
4.  **Database and Migration Analysis:**
    *   I reviewed the database configuration (`database.py`, `config.py`, `.env.local`) and found it to be correct for a Docker environment. The API service was correctly configured to connect to the `db` service.
    *   I then examined the database migration scripts in `infra/migrations/sql`.
    *   I discovered a highly problematic migration script: `002_rename_copilot_to_ai_assistant.sql`. This script was not *idempotent*, meaning it would fail if run more than once. It performed major schema changes like renaming tables and altering foreign keys.

## 3. Root Cause

The root cause of the infinite loading issue was an inconsistent and broken database state caused by a faulty, non-idempotent database migration script (`002_rename_copilot_to_ai_assistant.sql`).

When the Docker containers were started, the database initialization process would attempt to run all migration scripts. The faulty script could fail midway, leaving the database schema in a corrupted state (e.g., tables renamed but foreign keys not updated).

When the API service started and tried to execute queries against this broken schema (for example, during authentication), the queries would hang, waiting for locks or referencing non-existent objects. This caused the API endpoints to time out, which in turn caused the frontends to be stuck in a loading state forever.

## 4. Resolution

I have implemented the following solutions:

1.  **Idempotent Migration Script:** I have rewritten `infra/migrations/sql/002_rename_copilot_to_ai_assistant.sql` to be fully idempotent. It now uses `IF EXISTS` and `IF NOT EXISTS` checks to ensure it can be run multiple times without causing errors. This will prevent the database from getting into a broken state in the future.

2.  **Database Reset Script:** The existing database may still be in a broken state. To provide a clean slate, I have created a `reset_db.sh` script.

## 5. How to Fix Your Environment

To apply the fix and get your application working again, please follow these steps:

1.  **Ensure you are in the project's root directory.**
2.  **Run the database reset script:**
    *   If you are on Linux or macOS (or using WSL on Windows), run:
        ```bash
        bash reset_db.sh
        ```
    *   If you are on Windows PowerShell, you might need to adjust the script's content or execute the commands manually:
        ```powershell
        docker-compose down
        docker volume rm vivacampo_dbdata
        docker-compose up -d --build
        ```

This will delete the old, broken database, and then start the application again. The services will create a new, clean database and run the corrected migration scripts. After a few moments, the application should be accessible and the infinite loading issue will be resolved.