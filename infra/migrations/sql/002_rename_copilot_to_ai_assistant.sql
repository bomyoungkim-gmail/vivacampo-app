-- Migration to rename copilot to ai_assistant
-- This script is designed to be idempotent and can be run multiple times.

BEGIN;

-- Rename tables if they exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copilot_threads') THEN
        ALTER TABLE copilot_threads RENAME TO ai_assistant_threads;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copilot_checkpoints') THEN
        ALTER TABLE copilot_checkpoints RENAME TO ai_assistant_checkpoints;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'copilot_approvals') THEN
        ALTER TABLE copilot_approvals RENAME TO ai_assistant_approvals;
    END IF;
END $$;

-- Add provider and model columns to ai_assistant_threads if they don't exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_assistant_threads') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='ai_assistant_threads' AND column_name='provider') THEN
            ALTER TABLE ai_assistant_threads ADD COLUMN provider VARCHAR(50) DEFAULT 'openai';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='ai_assistant_threads' AND column_name='model') THEN
            ALTER TABLE ai_assistant_threads ADD COLUMN model VARCHAR(100) DEFAULT 'gpt-4';
        END IF;
    END IF;
END $$;

-- Update indexes
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'copilot_threads_idx' AND n.nspname = 'public') THEN
        DROP INDEX copilot_threads_idx;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'ai_assistant_threads_idx' AND n.nspname = 'public') THEN
        CREATE INDEX ai_assistant_threads_idx ON ai_assistant_threads (tenant_id, created_at DESC);
    END IF;

    IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'copilot_ckpt_thread_idx' AND n.nspname = 'public') THEN
        DROP INDEX copilot_ckpt_thread_idx;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'ai_assistant_ckpt_thread_idx' AND n.nspname = 'public') THEN
        CREATE INDEX ai_assistant_ckpt_thread_idx ON ai_assistant_checkpoints (tenant_id, thread_id, step DESC);
    END IF;

    IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'copilot_approvals_idx' AND n.nspname = 'public') THEN
        DROP INDEX copilot_approvals_idx;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'ai_assistant_approvals_idx' AND n.nspname = 'public') THEN
        CREATE INDEX ai_assistant_approvals_idx ON ai_assistant_approvals (tenant_id, decision, created_at DESC);
    END IF;
END $$;

-- Update foreign key references
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_assistant_checkpoints') THEN
        IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='copilot_checkpoints_thread_id_fkey' AND table_name='ai_assistant_checkpoints') THEN
            ALTER TABLE ai_assistant_checkpoints DROP CONSTRAINT copilot_checkpoints_thread_id_fkey;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='ai_assistant_checkpoints_thread_id_fkey' AND table_name='ai_assistant_checkpoints') THEN
            ALTER TABLE ai_assistant_checkpoints ADD CONSTRAINT ai_assistant_checkpoints_thread_id_fkey 
                FOREIGN KEY (thread_id) REFERENCES ai_assistant_threads(id) ON DELETE CASCADE;
        END IF;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_assistant_approvals') THEN
        IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='copilot_approvals_thread_id_fkey' AND table_name='ai_assistant_approvals') THEN
            ALTER TABLE ai_assistant_approvals DROP CONSTRAINT copilot_approvals_thread_id_fkey;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='ai_assistant_approvals_thread_id_fkey' AND table_name='ai_assistant_approvals') THEN
            ALTER TABLE ai_assistant_approvals ADD CONSTRAINT ai_assistant_approvals_thread_id_fkey 
                FOREIGN KEY (thread_id) REFERENCES ai_assistant_threads(id) ON DELETE CASCADE;
        END IF;
    END IF;
END $$;

COMMIT;