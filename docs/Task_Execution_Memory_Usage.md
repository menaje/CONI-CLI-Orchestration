# Task Execution Memory - Usage Guide

## Overview

Task Execution Memory stores every task execution as a vector (like git commits), enabling the system to learn from past experiences and provide intelligent recommendations for future similar tasks.

## Key Concepts

### Before + After Pattern
- **Before (Purpose)**: What the task was intended to do
- **After (Output)**: What the task actually produced

Both are embedded as vectors for semantic similarity search.

### Automatic Learning
Every task execution is automatically saved to the vector database with:
- Task purpose embedding
- Output content embedding
- Selected files and attention weights
- Quality score and success status
- Execution time and resource usage

## Quick Start

### 1. Basic Task Execution with Auto-Save

```python
from neural_engine import NeuralTask
from neural_engine.validator import NeuralValidator

# Create a task
task = NeuralTask(
    task_id="tsk-001",
    run_id="run-001",
    sub_stage_id="sub-01",
    task_name="Analyze Requirements",
    task_reason="User requested analysis",
    task_purpose="Analyze user requirements and identify key features"
)

# Execute task (your logic here)
output = "Requirements analysis:\n1. Feature A\n2. Feature B\n3. Feature C"

# Evaluate quality
validator = NeuralValidator()
quality_result = validator.evaluate(output, task.task_purpose)

# Record results - automatically saves to Task Execution Memory
task.record_execution_result(
    quality_score=quality_result['quality'],
    execution_time=5.2,
    token_used=1500,
    output_path="/output/analysis.md",
    output_content=output,
    output_summary="Identified 3 key features from user requirements"
    # auto_save_to_memory=True (default)
)
```

### 2. Get Recommendations from Past Executions

```python
# Before executing a new task, get recommendations
task = NeuralTask(
    task_id="tsk-002",
    run_id="run-002",
    sub_stage_id="sub-01",
    task_name="Analyze Requirements",
    task_reason="New user request",
    task_purpose="Analyze user requirements for mobile app features"
)

# Get recommendations from similar past tasks
recommendations = task.get_past_execution_recommendations()

if recommendations:
    print(f"Success Rate: {recommendations['success_rate']:.1%}")
    print(f"Avg Quality: {recommendations['avg_quality']:.2f}")

    # Recommended files based on similar tasks
    print("\nRecommended Files:")
    for file_rec in recommendations['recommended_files'][:5]:
        print(f"  - {file_rec['file_path']} (score: {file_rec['recommendation_score']:.3f})")

    # Suggested approaches from past successful tasks
    print("\nSuggested Approaches:")
    for approach in recommendations['suggested_approaches'][:3]:
        print(f"  - {approach['approach']} (similarity: {approach['similarity']:.2f})")
```

### 3. Direct TaskExecutionMemory Usage

```python
from neural_engine import get_task_execution_memory

task_memory = get_task_execution_memory()

# Search for similar past executions
similar_tasks = task_memory.get_similar_task_executions(
    task_purpose="Analyze user requirements",
    success_only=True,
    min_quality=0.7,
    match_count=10
)

for task_exec in similar_tasks:
    print(f"Task: {task_exec['task_purpose']}")
    print(f"Similarity: {task_exec['similarity']:.2f}")
    print(f"Quality: {task_exec['quality_score']:.2f}")
    print(f"Category: {task_exec['task_category']}")
    print()

# Get comprehensive recommendations
recommendations = task_memory.get_task_recommendations(
    task_purpose="Write API documentation"
)

# Get statistics
stats = task_memory.get_statistics()
print(f"Total Executions: {stats['total_executions']}")
print(f"Success Rate: {stats['success_rate']:.1%}")
print(f"Avg Quality: {stats['avg_quality']:.2f}")
print(f"Categories: {list(stats['categories'].keys())}")
```

### 4. Query by Category

```python
# Get all successful testing tasks
testing_tasks = task_memory.get_executions_by_category(
    task_category="testing",
    success_only=True,
    min_quality=0.8,
    limit=20
)

# Get all coding tasks
coding_tasks = task_memory.get_executions_by_category(
    task_category="coding",
    success_only=False,  # Include failures to learn from
    min_quality=0.0,
    limit=50
)
```

## Task Categories

Tasks are automatically categorized into:

- `analysis` - Analysis, understanding, review tasks
- `coding` - Code implementation, development
- `testing` - Testing, validation tasks
- `documentation` - Documentation writing
- `refactoring` - Code refactoring, cleanup
- `bug_fix` - Bug fixes, error corrections
- `design` - Design, planning, architecture
- `integration` - Integration, connection tasks
- `general` - General purpose tasks

## Database Schema

### task_executions Table

```sql
CREATE TABLE task_executions (
  id SERIAL PRIMARY KEY,
  run_id VARCHAR(10),
  task_id VARCHAR(10),
  task_name VARCHAR(200),
  task_category VARCHAR(50),

  -- Before (Input)
  task_purpose TEXT NOT NULL,
  purpose_embedding VECTOR(768),

  -- After (Output)
  output_content TEXT,
  output_embedding VECTOR(768),
  output_summary TEXT,

  -- Metadata
  selected_files JSONB,
  attention_weights JSONB,
  quality_score FLOAT,
  success BOOLEAN,
  execution_time FLOAT,
  tokens_used INT,

  created_at TIMESTAMPTZ
);

-- HNSW indexes for fast vector search
CREATE INDEX idx_task_exec_purpose_vector
  ON task_executions USING hnsw (purpose_embedding vector_cosine_ops);
CREATE INDEX idx_task_exec_output_vector
  ON task_executions USING hnsw (output_embedding vector_cosine_ops);
```

## Vector Search Functions

### 1. match_task_purposes()

Find similar past task executions by purpose:

```sql
SELECT * FROM match_task_purposes(
  query_embedding := '[0.1, 0.2, ...]'::vector(768),
  success_only := true,
  min_quality := 0.7,
  match_count := 10
);
```

Returns:
- `task_exec_id` - Execution ID
- `task_purpose` - Task purpose text
- `output_summary` - Output summary
- `similarity` - Cosine similarity (0~1)
- `quality_score` - Quality score
- `task_category` - Category
- `selected_files` - Files used

## Benefits

### 1. Faster Task Execution
System learns which files are relevant for each task type, reducing search time.

### 2. Higher Quality Results
Recommendations from past successful executions guide new tasks toward proven approaches.

### 3. Consistency
Similar tasks produce consistent results based on learned patterns.

### 4. Knowledge Accumulation
Every execution adds to the system's knowledge base, creating a growing asset.

### 5. Cross-Run Learning
Knowledge from past runs is available in future runs, enabling continuous improvement.

## Best Practices

### 1. Always Provide Output Content
```python
task.record_execution_result(
    quality_score=0.85,
    execution_time=10.0,
    token_used=2000,
    output_path="/output/result.md",
    output_content=result_text,  # ✓ Always include
    output_summary="Brief summary of results"  # ✓ For long outputs
)
```

### 2. Use Output Summaries for Long Content
For outputs > 2000 characters, provide a summary:

```python
output_summary = "Implemented 5 new features: feature A, B, C, D, E. " \
                "Updated 3 configuration files. All tests passing."
```

### 3. Check Recommendations Before Execution
```python
recommendations = task.get_past_execution_recommendations()
if recommendations and recommendations['success_rate'] > 0.8:
    # High success rate - use recommended approach
    for file_rec in recommendations['recommended_files'][:3]:
        task.related_references.append(file_rec['file_path'])
```

### 4. Learn from Failures
Don't filter out failures completely - they provide valuable learning:

```python
# Include some failures to learn what NOT to do
similar_tasks = task_memory.get_similar_task_executions(
    task_purpose="Deploy application",
    success_only=False,  # Include failures
    min_quality=0.0,
    match_count=20
)

# Analyze what went wrong in past failures
failures = [t for t in similar_tasks if t['quality_score'] < 0.5]
```

### 5. Monitor Memory Statistics
```python
stats = task_memory.get_statistics()

# Alert if quality is dropping
if stats['avg_quality'] < 0.6:
    print("WARNING: Average quality is below threshold!")

# Track category performance
for category, cat_stats in stats['categories'].items():
    print(f"{category}: {cat_stats['count']} tasks, "
          f"quality: {cat_stats['avg_quality']:.2f}")
```

## Integration with Attention Mechanism

Task Execution Memory works seamlessly with the Attention mechanism:

```python
from neural_engine import AttentionMechanism, get_embedding_engine

engine = get_embedding_engine()
attention = AttentionMechanism(engine)

# Get recommendations from past executions
recommendations = task.get_past_execution_recommendations()

# Combine with Attention for optimal file selection
if recommendations['recommended_files']:
    # Boost attention weights for recommended files
    for file_rec in recommendations['recommended_files']:
        file_path = file_rec['file_path']
        if file_path in candidate_files:
            # Increase probability of selection
            pass
```

## Troubleshooting

### Memory Not Saving

If tasks aren't being saved to memory:

1. Check Supabase connection:
```python
from neural_engine import get_task_execution_memory
task_memory = get_task_execution_memory()
# Should not raise errors
```

2. Verify database schema:
```sql
SELECT COUNT(*) FROM task_executions;
```

3. Check for errors in logs:
```python
# Look for "[WARNING] Task Execution Memory save failed"
```

### No Recommendations Found

If `get_past_execution_recommendations()` returns empty results:

1. Not enough historical data yet (need at least 1 past execution)
2. Purpose embeddings too different (similarity threshold too high)
3. Quality threshold too high (lower `min_quality`)

```python
# Try with lower thresholds
similar_tasks = task_memory.get_similar_task_executions(
    task_purpose=task.task_purpose,
    success_only=False,  # Include all
    min_quality=0.0,     # No quality filter
    match_count=20       # More results
)
```

### Slow Vector Search

If vector similarity search is slow:

1. Verify HNSW indexes exist:
```sql
SELECT indexname FROM pg_indexes
WHERE tablename = 'task_executions';
-- Should see idx_task_exec_purpose_vector and idx_task_exec_output_vector
```

2. Check index usage:
```sql
EXPLAIN ANALYZE
SELECT * FROM match_task_purposes('[...]'::vector(768), true, 0.7, 10);
-- Should use "Index Scan using idx_task_exec_purpose_vector"
```

## Future Enhancements

The planning document (Neural-CONI_Task_Memory_통합_기획서.md) describes additional features:

1. **Task Auto-Generation** - Automatically generate tasks based on patterns
2. **Failure Prediction** - Predict failures before execution
3. **Task Order Optimization** - Learn optimal task sequences
4. **Cross-Project Learning** - Abstract knowledge for reuse across projects

These will be implemented in future phases.

## See Also

- [Neural-CONI_Task_Memory_통합_기획서.md](./Neural-CONI_Task_Memory_통합_기획서.md) - Full planning document
- [Git_Diff_Vector_Memory_기획서.md](./Git_Diff_Vector_Memory_기획서.md) - Git diff memory planning
- [Supabase Schema](../db_templates/supabase_schema.sql) - Complete database schema
