-- Neural-CONI Supabase Database Schema
--
-- Execute this SQL in your Supabase SQL Editor to create all tables
--
-- Supabase Project Setup:
-- 1. Go to https://supabase.com
-- 2. Create new project
-- 3. Go to SQL Editor
-- 4. Paste and execute this script

-- ==================== Process Runs ====================

CREATE TABLE IF NOT EXISTS process_runs (
  run_id VARCHAR(10) PRIMARY KEY,
  creation_timestamp TIMESTAMPTZ DEFAULT NOW(),
  user_request TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'PENDING',
  current_phase_id VARCHAR(10),
  current_stage_id VARCHAR(10),
  current_sub_stage_id VARCHAR(10),
  current_task_id VARCHAR(10),
  run_mode VARCHAR(20)
);

COMMENT ON TABLE process_runs IS 'Master list of all runs and their current state';
COMMENT ON COLUMN process_runs.run_id IS 'Unique run identifier (e.g., run-001)';
COMMENT ON COLUMN process_runs.status IS 'PENDING, COMPLETED, FAILED';
COMMENT ON COLUMN process_runs.run_mode IS 'INITIAL_RUN or CONTINUOUS_RUN';

-- Index for status filtering
CREATE INDEX IF NOT EXISTS idx_process_runs_status ON process_runs(status);
CREATE INDEX IF NOT EXISTS idx_process_runs_timestamp ON process_runs(creation_timestamp DESC);

-- ==================== Phases ====================

CREATE TABLE IF NOT EXISTS phases (
  phase_id VARCHAR(10) NOT NULL,
  run_id VARCHAR(10) NOT NULL REFERENCES process_runs(run_id) ON DELETE CASCADE,
  phase_name VARCHAR(100),
  phase_reason TEXT,
  phase_purpose TEXT,
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (run_id, phase_id)
);

COMMENT ON TABLE phases IS 'Phases for each run';
CREATE INDEX IF NOT EXISTS idx_phases_run ON phases(run_id);
CREATE INDEX IF NOT EXISTS idx_phases_status ON phases(run_id, status);

-- ==================== Stages ====================

CREATE TABLE IF NOT EXISTS stages (
  stage_id VARCHAR(10) NOT NULL,
  run_id VARCHAR(10) NOT NULL,
  phase_id VARCHAR(10) NOT NULL,
  stage_name VARCHAR(100),
  stage_reason TEXT,
  stage_purpose TEXT,
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (run_id, phase_id, stage_id),
  FOREIGN KEY (run_id, phase_id) REFERENCES phases(run_id, phase_id) ON DELETE CASCADE
);

COMMENT ON TABLE stages IS 'Stages within phases';
CREATE INDEX IF NOT EXISTS idx_stages_run_phase ON stages(run_id, phase_id);

-- ==================== Sub-Stages ====================

CREATE TABLE IF NOT EXISTS sub_stages (
  sub_stage_id VARCHAR(10) NOT NULL,
  run_id VARCHAR(10) NOT NULL,
  phase_id VARCHAR(10) NOT NULL,
  stage_id VARCHAR(10) NOT NULL,
  sub_stage_name VARCHAR(200),
  sub_stage_reason TEXT,
  sub_stage_purpose TEXT,
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (run_id, phase_id, stage_id, sub_stage_id),
  FOREIGN KEY (run_id, phase_id, stage_id) REFERENCES stages(run_id, phase_id, stage_id) ON DELETE CASCADE
);

COMMENT ON TABLE sub_stages IS 'Sub-stages within stages';
CREATE INDEX IF NOT EXISTS idx_sub_stages_run_phase_stage ON sub_stages(run_id, phase_id, stage_id);

-- ==================== Tasks ====================

CREATE TABLE IF NOT EXISTS tasks (
  task_id VARCHAR(10) NOT NULL,
  run_id VARCHAR(10) NOT NULL,
  phase_id VARCHAR(10) NOT NULL,
  stage_id VARCHAR(10) NOT NULL,
  sub_stage_id VARCHAR(10) NOT NULL,
  task_name VARCHAR(200),
  task_reason TEXT,
  task_purpose TEXT,
  dependencies JSONB DEFAULT '[]',
  threshold FLOAT DEFAULT 0.6,
  mcp_id VARCHAR(50),
  related_references JSONB,
  related_guidelines JSONB,
  output_folder TEXT,
  output_path TEXT,
  pre_tool_reason TEXT,
  pre_tool_purpose TEXT,
  status VARCHAR(20) DEFAULT 'PENDING',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (run_id, phase_id, stage_id, sub_stage_id, task_id),
  FOREIGN KEY (run_id, phase_id, stage_id, sub_stage_id)
    REFERENCES sub_stages(run_id, phase_id, stage_id, sub_stage_id) ON DELETE CASCADE
);

COMMENT ON TABLE tasks IS 'Individual tasks to execute';
COMMENT ON COLUMN tasks.dependencies IS 'JSON array of task_ids this task depends on';
COMMENT ON COLUMN tasks.threshold IS 'Neural activation threshold (0~1)';
COMMENT ON COLUMN tasks.related_references IS 'JSON array of file paths';

CREATE INDEX IF NOT EXISTS idx_tasks_run ON tasks(run_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(run_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_sub_stage ON tasks(run_id, phase_id, stage_id, sub_stage_id);

-- ==================== Weights (Neural Network) ====================

CREATE TABLE IF NOT EXISTS weights (
  from_task VARCHAR(50) NOT NULL,
  to_task VARCHAR(50) NOT NULL,
  weight FLOAT NOT NULL,
  gradient FLOAT DEFAULT 0.0,
  update_count INT DEFAULT 0,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (from_task, to_task)
);

COMMENT ON TABLE weights IS 'Learnable weights between tasks (Neural Network connections)';
COMMENT ON COLUMN weights.weight IS 'Current weight value (0~1)';
COMMENT ON COLUMN weights.gradient IS 'Gradient from last backpropagation';
COMMENT ON COLUMN weights.update_count IS 'Number of times this weight was updated';

CREATE INDEX IF NOT EXISTS idx_weights_from ON weights(from_task);
CREATE INDEX IF NOT EXISTS idx_weights_to ON weights(to_task);
CREATE INDEX IF NOT EXISTS idx_weights_updated ON weights(last_updated DESC);

-- ==================== Execution History ====================

CREATE TABLE IF NOT EXISTS execution_history (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(10) NOT NULL,
  task_id VARCHAR(10) NOT NULL,
  task_name VARCHAR(200),
  executed BOOLEAN NOT NULL,
  activation FLOAT,
  quality FLOAT,
  execution_time FLOAT,
  tokens_used INT,
  skip_reason TEXT,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE execution_history IS 'Log of all task executions';
COMMENT ON COLUMN execution_history.executed IS 'TRUE if task was executed, FALSE if skipped';
COMMENT ON COLUMN execution_history.activation IS 'Neural activation level (0~1)';
COMMENT ON COLUMN execution_history.quality IS 'Output quality score (0~1)';
COMMENT ON COLUMN execution_history.tokens_used IS 'LLM tokens consumed';

CREATE INDEX IF NOT EXISTS idx_execution_run ON execution_history(run_id);
CREATE INDEX IF NOT EXISTS idx_execution_task_name ON execution_history(task_name);
CREATE INDEX IF NOT EXISTS idx_execution_executed ON execution_history(executed);
CREATE INDEX IF NOT EXISTS idx_execution_time ON execution_history(executed_at DESC);

-- ==================== Neural Tasks ====================

CREATE TABLE IF NOT EXISTS neural_tasks (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(10) NOT NULL,
  task_id VARCHAR(10) NOT NULL,
  activation_level FLOAT,
  threshold FLOAT DEFAULT 0.6,
  quality_score FLOAT,
  selected_files JSONB,
  attention_weights JSONB,
  execution_time FLOAT,
  tokens_used INT,
  retry_count INT DEFAULT 0,
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (run_id, task_id)
);

COMMENT ON TABLE neural_tasks IS 'Neural network attributes for each task';
COMMENT ON COLUMN neural_tasks.activation_level IS 'Computed activation value (0~1)';
COMMENT ON COLUMN neural_tasks.selected_files IS 'JSON array of files selected by Attention';
COMMENT ON COLUMN neural_tasks.attention_weights IS 'JSON object of file -> attention weight';

CREATE INDEX IF NOT EXISTS idx_neural_tasks_run ON neural_tasks(run_id);
CREATE INDEX IF NOT EXISTS idx_neural_tasks_run_task ON neural_tasks(run_id, task_id);

-- ==================== Learning Metrics ====================

CREATE TABLE IF NOT EXISTS learning_metrics (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(10) UNIQUE NOT NULL,
  total_tasks INT NOT NULL,
  activated_tasks INT NOT NULL,
  skipped_tasks INT NOT NULL,
  avg_quality FLOAT NOT NULL,
  error FLOAT NOT NULL,
  weights_updated INT NOT NULL,
  improvement FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE learning_metrics IS 'Learning performance metrics per run';
COMMENT ON COLUMN learning_metrics.error IS 'target_quality - avg_quality';
COMMENT ON COLUMN learning_metrics.improvement IS 'Quality improvement vs previous run (%)';

CREATE INDEX IF NOT EXISTS idx_learning_metrics_run ON learning_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_learning_metrics_created ON learning_metrics(created_at DESC);

-- ==================== Functions ====================

-- Auto-update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for neural_tasks
CREATE TRIGGER update_neural_tasks_updated_at
    BEFORE UPDATE ON neural_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== Row Level Security (RLS) ====================

-- Enable RLS (optional - for multi-tenant scenarios)
-- ALTER TABLE process_runs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE weights ENABLE ROW LEVEL SECURITY;
-- ... etc

-- ==================== Initial Data ====================

-- Insert default learning rate
INSERT INTO weights (from_task, to_task, weight, gradient, update_count)
VALUES ('__config__', '__learning_rate__', 0.01, 0.0, 0)
ON CONFLICT (from_task, to_task) DO NOTHING;

-- ==================== Complete! ====================

-- Verify tables
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name IN (
    'process_runs', 'phases', 'stages', 'sub_stages', 'tasks',
    'weights', 'execution_history', 'neural_tasks', 'learning_metrics'
  )
ORDER BY table_name;
