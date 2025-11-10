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

-- ==================== Vector DB (pgvector) ====================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- File Embeddings: 파일 임베딩 캐싱 및 검색
CREATE TABLE IF NOT EXISTS file_embeddings (
  id SERIAL PRIMARY KEY,
  file_path TEXT UNIQUE NOT NULL,
  content_hash VARCHAR(64) NOT NULL,
  embedding VECTOR(768),
  file_type VARCHAR(20),
  file_size INT,
  line_count INT,
  last_modified TIMESTAMPTZ,

  -- 사용 통계
  usage_count INT DEFAULT 0,
  last_used_at TIMESTAMPTZ,
  avg_attention_weight FLOAT DEFAULT 0.0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE file_embeddings IS 'File embeddings cache with usage statistics';
COMMENT ON COLUMN file_embeddings.content_hash IS 'SHA-256 hash for change detection';
COMMENT ON COLUMN file_embeddings.embedding IS '768-dim vector from nomic-embed-text';
COMMENT ON COLUMN file_embeddings.usage_count IS 'How many times this file was selected';
COMMENT ON COLUMN file_embeddings.avg_attention_weight IS 'Average attention weight across all uses';

-- HNSW index for fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_file_embeddings_vector
  ON file_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_file_embeddings_path ON file_embeddings(file_path);
CREATE INDEX IF NOT EXISTS idx_file_embeddings_usage ON file_embeddings(usage_count DESC);

-- Execution Contexts: Run 실행 컨텍스트 (학습의 핵심!)
CREATE TABLE IF NOT EXISTS execution_contexts (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(10) NOT NULL,
  task_id VARCHAR(10) NOT NULL,

  -- 사용자 요청
  user_request TEXT NOT NULL,
  request_embedding VECTOR(768),
  task_category VARCHAR(50),

  -- 실행 결과
  quality_score FLOAT,
  execution_time FLOAT,
  tokens_used INT,

  -- 상태
  executed BOOLEAN DEFAULT TRUE,
  success BOOLEAN DEFAULT FALSE,
  error_message TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  FOREIGN KEY (run_id) REFERENCES process_runs(run_id) ON DELETE CASCADE
);

COMMENT ON TABLE execution_contexts IS 'Execution contexts for learning from past runs';
COMMENT ON COLUMN execution_contexts.request_embedding IS 'User request embedding for similarity search';
COMMENT ON COLUMN execution_contexts.task_category IS 'Auto-classified task type (bug_fix, feature, refactor, etc)';
COMMENT ON COLUMN execution_contexts.success IS 'Was this execution successful?';

-- HNSW index for similar request search
CREATE INDEX IF NOT EXISTS idx_execution_contexts_vector
  ON execution_contexts USING hnsw (request_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_execution_contexts_run ON execution_contexts(run_id);
CREATE INDEX IF NOT EXISTS idx_execution_contexts_success ON execution_contexts(success);
CREATE INDEX IF NOT EXISTS idx_execution_contexts_quality ON execution_contexts(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_execution_contexts_category ON execution_contexts(task_category);

-- Selected Files: 선택된 파일과 Attention weights
CREATE TABLE IF NOT EXISTS selected_files (
  id SERIAL PRIMARY KEY,
  context_id INT NOT NULL,
  file_path TEXT NOT NULL,

  -- Attention 정보
  attention_weight FLOAT NOT NULL,
  attention_rank INT,

  -- 유용성 판단
  was_useful BOOLEAN,
  usefulness_score FLOAT,

  created_at TIMESTAMPTZ DEFAULT NOW(),

  FOREIGN KEY (context_id) REFERENCES execution_contexts(id) ON DELETE CASCADE,
  FOREIGN KEY (file_path) REFERENCES file_embeddings(file_path) ON DELETE CASCADE
);

COMMENT ON TABLE selected_files IS 'Files selected by Attention mechanism with their weights';
COMMENT ON COLUMN selected_files.attention_weight IS 'Attention weight (0~1)';
COMMENT ON COLUMN selected_files.attention_rank IS 'Rank in Top-K selection';
COMMENT ON COLUMN selected_files.was_useful IS 'Was this file actually useful? (quality-based)';
COMMENT ON COLUMN selected_files.usefulness_score IS 'How useful was this file? (0~1)';

CREATE INDEX IF NOT EXISTS idx_selected_files_context ON selected_files(context_id);
CREATE INDEX IF NOT EXISTS idx_selected_files_path ON selected_files(file_path);
CREATE INDEX IF NOT EXISTS idx_selected_files_useful ON selected_files(was_useful);
CREATE INDEX IF NOT EXISTS idx_selected_files_weight ON selected_files(attention_weight DESC);

-- File-Task Affinity: 파일과 작업 타입 간 학습된 연관성
CREATE TABLE IF NOT EXISTS file_task_affinity (
  file_path TEXT NOT NULL,
  task_category VARCHAR(50) NOT NULL,

  -- 학습된 통계
  success_count INT DEFAULT 0,
  failure_count INT DEFAULT 0,
  total_uses INT DEFAULT 0,

  avg_quality FLOAT DEFAULT 0.0,
  avg_attention_weight FLOAT DEFAULT 0.0,
  avg_usefulness FLOAT DEFAULT 0.0,

  -- 학습된 가중치 (유사 Weights 테이블)
  learned_importance FLOAT DEFAULT 0.5,
  confidence FLOAT DEFAULT 0.0,

  last_updated TIMESTAMPTZ DEFAULT NOW(),

  PRIMARY KEY (file_path, task_category),
  FOREIGN KEY (file_path) REFERENCES file_embeddings(file_path) ON DELETE CASCADE
);

COMMENT ON TABLE file_task_affinity IS 'Learned affinity between files and task categories';
COMMENT ON COLUMN file_task_affinity.learned_importance IS 'Learned importance weight (0~1)';
COMMENT ON COLUMN file_task_affinity.confidence IS 'Confidence based on sample size (0~1)';

CREATE INDEX IF NOT EXISTS idx_affinity_file ON file_task_affinity(file_path);
CREATE INDEX IF NOT EXISTS idx_affinity_category ON file_task_affinity(task_category);
CREATE INDEX IF NOT EXISTS idx_affinity_importance ON file_task_affinity(learned_importance DESC);

-- File Co-occurrence: 함께 사용되는 파일 패턴
CREATE TABLE IF NOT EXISTS file_co_occurrence (
  file_a TEXT NOT NULL,
  file_b TEXT NOT NULL,

  co_occurrence_count INT DEFAULT 0,
  avg_quality_when_together FLOAT DEFAULT 0.0,
  correlation_strength FLOAT DEFAULT 0.0,

  last_occurred TIMESTAMPTZ DEFAULT NOW(),

  PRIMARY KEY (file_a, file_b),
  FOREIGN KEY (file_a) REFERENCES file_embeddings(file_path) ON DELETE CASCADE,
  FOREIGN KEY (file_b) REFERENCES file_embeddings(file_path) ON DELETE CASCADE,

  CHECK (file_a < file_b)  -- Ensure ordering to avoid duplicates
);

COMMENT ON TABLE file_co_occurrence IS 'Files that are frequently used together';
COMMENT ON COLUMN file_co_occurrence.correlation_strength IS 'How strongly correlated (0~1)';

CREATE INDEX IF NOT EXISTS idx_co_occurrence_a ON file_co_occurrence(file_a);
CREATE INDEX IF NOT EXISTS idx_co_occurrence_b ON file_co_occurrence(file_b);
CREATE INDEX IF NOT EXISTS idx_co_occurrence_strength ON file_co_occurrence(correlation_strength DESC);

-- ==================== Vector Search Functions ====================

-- 1. Find similar files by embedding
CREATE OR REPLACE FUNCTION match_files(
  query_embedding VECTOR(768),
  match_threshold FLOAT DEFAULT 0.5,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  file_path TEXT,
  similarity FLOAT,
  usage_count INT,
  avg_attention_weight FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    file_path,
    1 - (embedding <=> query_embedding) AS similarity,
    usage_count,
    avg_attention_weight
  FROM file_embeddings
  WHERE 1 - (embedding <=> query_embedding) >= match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_files IS 'Find similar files by embedding vector';

-- 2. Find similar execution contexts (past experiences)
CREATE OR REPLACE FUNCTION match_contexts(
  query_embedding VECTOR(768),
  success_only BOOLEAN DEFAULT TRUE,
  min_quality FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 20
)
RETURNS TABLE (
  context_id INT,
  run_id VARCHAR(10),
  task_id VARCHAR(10),
  user_request TEXT,
  similarity FLOAT,
  quality_score FLOAT,
  task_category VARCHAR(50)
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    id AS context_id,
    run_id,
    task_id,
    user_request,
    1 - (request_embedding <=> query_embedding) AS similarity,
    quality_score,
    task_category
  FROM execution_contexts
  WHERE
    (NOT success_only OR success = TRUE)
    AND quality_score >= min_quality
  ORDER BY request_embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_contexts IS 'Find similar past execution contexts';

-- 3. Get recommended files for a task category
CREATE OR REPLACE FUNCTION recommend_files_for_category(
  category VARCHAR(50),
  min_confidence FLOAT DEFAULT 0.3,
  limit_count INT DEFAULT 10
)
RETURNS TABLE (
  file_path TEXT,
  learned_importance FLOAT,
  avg_quality FLOAT,
  total_uses INT,
  confidence FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    file_path,
    learned_importance,
    avg_quality,
    total_uses,
    confidence
  FROM file_task_affinity
  WHERE
    task_category = category
    AND confidence >= min_confidence
  ORDER BY learned_importance DESC, avg_quality DESC
  LIMIT limit_count;
$$;

COMMENT ON FUNCTION recommend_files_for_category IS 'Get recommended files for a task category based on learned affinity';

-- 4. Get co-occurring files (files that work well together)
CREATE OR REPLACE FUNCTION get_co_occurring_files(
  target_file TEXT,
  min_correlation FLOAT DEFAULT 0.3,
  limit_count INT DEFAULT 5
)
RETURNS TABLE (
  related_file TEXT,
  co_occurrence_count INT,
  avg_quality_when_together FLOAT,
  correlation_strength FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    CASE
      WHEN file_a = target_file THEN file_b
      ELSE file_a
    END AS related_file,
    co_occurrence_count,
    avg_quality_when_together,
    correlation_strength
  FROM file_co_occurrence
  WHERE
    (file_a = target_file OR file_b = target_file)
    AND correlation_strength >= min_correlation
  ORDER BY correlation_strength DESC, co_occurrence_count DESC
  LIMIT limit_count;
$$;

COMMENT ON FUNCTION get_co_occurring_files IS 'Find files that frequently co-occur with target file';

-- 5. Get useful files from similar contexts (핵심 함수!)
CREATE OR REPLACE FUNCTION get_learned_file_recommendations(
  query_embedding VECTOR(768),
  success_only BOOLEAN DEFAULT TRUE,
  min_quality FLOAT DEFAULT 0.7,
  min_usefulness FLOAT DEFAULT 0.5,
  limit_count INT DEFAULT 10
)
RETURNS TABLE (
  file_path TEXT,
  recommendation_score FLOAT,
  avg_attention_weight FLOAT,
  avg_usefulness_score FLOAT,
  times_selected INT,
  avg_context_similarity FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    sf.file_path,
    -- Recommendation score: combines attention, usefulness, and context similarity
    AVG((1 - (ec.request_embedding <=> query_embedding)) * sf.attention_weight * sf.usefulness_score) AS recommendation_score,
    AVG(sf.attention_weight) AS avg_attention_weight,
    AVG(sf.usefulness_score) AS avg_usefulness_score,
    COUNT(*) AS times_selected,
    AVG(1 - (ec.request_embedding <=> query_embedding)) AS avg_context_similarity
  FROM execution_contexts ec
  JOIN selected_files sf ON ec.id = sf.context_id
  WHERE
    (NOT success_only OR ec.success = TRUE)
    AND ec.quality_score >= min_quality
    AND sf.was_useful = TRUE
    AND sf.usefulness_score >= min_usefulness
  GROUP BY sf.file_path
  HAVING AVG(1 - (ec.request_embedding <=> query_embedding)) >= 0.5
  ORDER BY recommendation_score DESC
  LIMIT limit_count;
$$;

COMMENT ON FUNCTION get_learned_file_recommendations IS 'Get file recommendations based on learned patterns from similar contexts';

-- ==================== Task Execution Memory (NEW) ====================

-- Task Executions: Task 실행을 Git Commit처럼 저장
CREATE TABLE IF NOT EXISTS task_executions (
  id SERIAL PRIMARY KEY,

  -- Task 식별
  run_id VARCHAR(10) NOT NULL,
  task_id VARCHAR(10) NOT NULL,
  task_name VARCHAR(200),
  task_category VARCHAR(50),

  -- Before (Input): Task의 목적
  task_purpose TEXT NOT NULL,
  purpose_embedding VECTOR(768),

  -- After (Output): Task의 결과
  output_content TEXT,
  output_embedding VECTOR(768),
  output_summary TEXT,

  -- 실행 정보
  selected_files JSONB,
  attention_weights JSONB,

  -- 품질 및 성공 여부
  quality_score FLOAT,
  success BOOLEAN DEFAULT FALSE,
  error_message TEXT,

  -- 리소스 사용
  execution_time FLOAT,
  tokens_used INT,

  -- 시간
  created_at TIMESTAMPTZ DEFAULT NOW(),

  FOREIGN KEY (run_id) REFERENCES process_runs(run_id) ON DELETE CASCADE
);

COMMENT ON TABLE task_executions IS 'Task executions stored like git commits (Before + After)';
COMMENT ON COLUMN task_executions.task_purpose IS 'What the task was meant to do (Before)';
COMMENT ON COLUMN task_executions.purpose_embedding IS 'Task purpose embedding for similarity search';
COMMENT ON COLUMN task_executions.output_content IS 'What the task actually produced (After)';
COMMENT ON COLUMN task_executions.output_embedding IS 'Output embedding for result similarity search';
COMMENT ON COLUMN task_executions.task_category IS 'Auto-classified task type (analysis, coding, testing, etc)';

-- HNSW indexes for fast vector search
CREATE INDEX IF NOT EXISTS idx_task_exec_purpose_vector
  ON task_executions USING hnsw (purpose_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_task_exec_output_vector
  ON task_executions USING hnsw (output_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_task_exec_run ON task_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_task_exec_category ON task_executions(task_category);
CREATE INDEX IF NOT EXISTS idx_task_exec_success ON task_executions(success);
CREATE INDEX IF NOT EXISTS idx_task_exec_quality ON task_executions(quality_score DESC);

-- Code Changes (Git Diff Memory): 개발자 경험 자산 저장
CREATE TABLE IF NOT EXISTS code_changes (
  id SERIAL PRIMARY KEY,

  -- Git 정보
  commit_hash VARCHAR(40) UNIQUE NOT NULL,
  commit_message TEXT NOT NULL,
  author_name VARCHAR(100),
  author_email VARCHAR(100),
  committed_at TIMESTAMPTZ,

  -- Problem (Before): 무엇을 해결하려 했는가?
  problem_description TEXT NOT NULL,
  problem_embedding VECTOR(768),
  problem_category VARCHAR(50),

  -- Solution (After): 어떻게 해결했는가?
  diff_content TEXT NOT NULL,
  diff_embedding VECTOR(768),
  diff_summary TEXT,

  -- 메타데이터
  files_changed JSONB,
  lines_added INT,
  lines_deleted INT,

  -- 품질 지표
  quality_score FLOAT,
  usefulness_score FLOAT,
  complexity_score FLOAT,

  -- 태그 및 분류
  tags TEXT[],
  languages TEXT[],
  frameworks TEXT[],

  -- 재사용 통계
  reference_count INT DEFAULT 0,
  last_referenced_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE code_changes IS 'Git commit diffs stored as vectors for experience-based problem solving';
COMMENT ON COLUMN code_changes.problem_description IS 'What problem was being solved (extracted from commit message)';
COMMENT ON COLUMN code_changes.problem_embedding IS 'Problem description embedding for similarity search';
COMMENT ON COLUMN code_changes.diff_content IS 'The actual code changes (git diff)';
COMMENT ON COLUMN code_changes.diff_embedding IS 'Diff embedding for solution similarity search';
COMMENT ON COLUMN code_changes.quality_score IS 'Estimated quality of the solution (0~1)';

-- HNSW indexes for fast vector search
CREATE INDEX IF NOT EXISTS idx_code_changes_problem_vector
  ON code_changes USING hnsw (problem_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_code_changes_diff_vector
  ON code_changes USING hnsw (diff_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_code_changes_commit ON code_changes(commit_hash);
CREATE INDEX IF NOT EXISTS idx_code_changes_category ON code_changes(problem_category);
CREATE INDEX IF NOT EXISTS idx_code_changes_quality ON code_changes(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_code_changes_tags ON code_changes USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_code_changes_reference ON code_changes(reference_count DESC);

-- ==================== Task & Code Change Search Functions ====================

-- 6. Find similar task executions by purpose
CREATE OR REPLACE FUNCTION match_task_purposes(
  query_embedding VECTOR(768),
  success_only BOOLEAN DEFAULT TRUE,
  min_quality FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  task_exec_id INT,
  task_purpose TEXT,
  output_summary TEXT,
  similarity FLOAT,
  quality_score FLOAT,
  task_category VARCHAR(50),
  selected_files JSONB
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    id AS task_exec_id,
    task_purpose,
    output_summary,
    1 - (purpose_embedding <=> query_embedding) AS similarity,
    quality_score,
    task_category,
    selected_files
  FROM task_executions
  WHERE
    (NOT success_only OR success = TRUE)
    AND quality_score >= min_quality
    AND purpose_embedding IS NOT NULL
  ORDER BY purpose_embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_task_purposes IS 'Find similar past task executions by task purpose';

-- 7. Find similar code solutions by problem
CREATE OR REPLACE FUNCTION match_code_problems(
  query_embedding VECTOR(768),
  min_quality FLOAT DEFAULT 0.6,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  code_change_id INT,
  commit_hash VARCHAR(40),
  problem_description TEXT,
  diff_summary TEXT,
  similarity FLOAT,
  quality_score FLOAT,
  problem_category VARCHAR(50)
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    id AS code_change_id,
    commit_hash,
    problem_description,
    diff_summary,
    1 - (problem_embedding <=> query_embedding) AS similarity,
    quality_score,
    problem_category
  FROM code_changes
  WHERE
    quality_score >= min_quality
    AND problem_embedding IS NOT NULL
  ORDER BY problem_embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_code_problems IS 'Find similar code solutions by problem description';

-- 8. Find similar code solutions by diff content
CREATE OR REPLACE FUNCTION match_code_diffs(
  query_embedding VECTOR(768),
  min_quality FLOAT DEFAULT 0.6,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  code_change_id INT,
  commit_hash VARCHAR(40),
  problem_description TEXT,
  diff_content TEXT,
  similarity FLOAT,
  quality_score FLOAT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    id AS code_change_id,
    commit_hash,
    problem_description,
    diff_content,
    1 - (diff_embedding <=> query_embedding) AS similarity,
    quality_score
  FROM code_changes
  WHERE
    quality_score >= min_quality
    AND diff_embedding IS NOT NULL
  ORDER BY diff_embedding <=> query_embedding
  LIMIT match_count;
$$;

COMMENT ON FUNCTION match_code_diffs IS 'Find similar code solutions by diff content';

-- ==================== Utility Functions ====================

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

-- Trigger for file_embeddings
CREATE TRIGGER update_file_embeddings_updated_at
    BEFORE UPDATE ON file_embeddings
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
