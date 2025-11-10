#!/usr/bin/env python3
"""
Supabase Database Test Script

Test all Supabase database operations

Usage:
    python scripts/test_supabase.py [mode]

    mode: auto (default) | supabase | markdown
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural_engine.db_adapter import get_db


def test_database(mode: str = "auto"):
    """Test database operations"""
    print("=" * 70)
    print(f"  Neural-CONI Database Test - Mode: {mode}")
    print("=" * 70)

    # Initialize database
    print("\n[1] Initializing database...")
    try:
        db = get_db(mode=mode)
        print(f"    ✅ Backend: {db.get_backend_type()}")
    except Exception as e:
        print(f"    ❌ Failed to initialize: {e}")
        print("\n💡 For Supabase:")
        print("  export SUPABASE_URL=https://xxxxx.supabase.co")
        print("  export SUPABASE_KEY=eyJhbGc...")
        return False

    # Test 1: Create Run
    print("\n[2] Testing Run creation...")
    try:
        run = db.create_run(
            run_id="test-001",
            user_request="Test user request",
            run_mode="INITIAL_RUN"
        )
        print(f"    ✅ Created run: {run.get('run_id')}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False

    # Test 2: Get Run
    print("\n[3] Testing Run retrieval...")
    try:
        run = db.get_run("test-001")
        if run:
            print(f"    ✅ Retrieved run: {run.get('run_id')}")
            print(f"       Status: {run.get('status')}")
        else:
            print(f"    ❌ Run not found")
            return False
    except Exception as e:
        print(f"    ❌ Failed: {e}")
        return False

    # Test 3: Update Run
    print("\n[4] Testing Run update...")
    try:
        db.update_run("test-001", status="COMPLETED", current_phase_id="ph-1")
        run = db.get_run("test-001")
        if run.get("status") == "COMPLETED":
            print(f"    ✅ Updated run status: {run.get('status')}")
        else:
            print(f"    ❌ Status not updated")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Test 4: Weights
    print("\n[5] Testing Weights...")
    try:
        # Set weight
        db.set_weight("tsk-01", "tsk-02", 0.85, gradient=0.12)
        print(f"    ✅ Set weight: tsk-01 → tsk-02 = 0.85")

        # Get weight
        weight = db.get_weight("tsk-01", "tsk-02")
        print(f"    ✅ Retrieved weight: {weight}")

        # Batch update
        db.batch_update_weights({
            "tsk-01→tsk-03": 0.45,
            "tsk-02→tsk-04": 0.92
        })
        print(f"    ✅ Batch updated 2 weights")

        # Get all weights
        all_weights = db.get_all_weights()
        print(f"    ✅ Total weights in DB: {len(all_weights)}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Test 5: Execution History
    print("\n[6] Testing Execution History...")
    try:
        db.log_execution(
            run_id="test-001",
            task_id="tsk-01",
            task_name="Test Task",
            executed=True,
            activation=0.95,
            quality=0.88,
            execution_time=45.2,
            tokens_used=8500
        )
        print(f"    ✅ Logged execution: test-001/tsk-01")

        # Log skipped task
        db.log_execution(
            run_id="test-001",
            task_id="tsk-02",
            task_name="Skipped Task",
            executed=False,
            activation=0.42,
            skip_reason="activation < 0.6"
        )
        print(f"    ✅ Logged skip: test-001/tsk-02")

        # Query history
        history = db.get_execution_history(run_id="test-001")
        print(f"    ✅ Retrieved {len(history)} execution records")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Test 6: Neural Tasks
    print("\n[7] Testing Neural Tasks...")
    try:
        db.create_neural_task(
            run_id="test-001",
            task_id="tsk-01",
            activation_level=0.95,
            threshold=0.7,
            quality_score=0.88,
            selected_files=["file1.md", "file2.md"],
            attention_weights={"file1.md": 0.92, "file2.md": 0.78},
            execution_time=45.2,
            tokens_used=8500,
            status="COMPLETED"
        )
        print(f"    ✅ Created neural task: test-001/tsk-01")

        # Retrieve
        neural_task = db.get_neural_task("test-001", "tsk-01")
        if neural_task:
            print(f"    ✅ Retrieved neural task")
            print(f"       Activation: {neural_task.get('activation_level')}")
            print(f"       Quality: {neural_task.get('quality_score')}")
            print(f"       Selected files: {len(neural_task.get('selected_files', []))}")
        else:
            print(f"    ❌ Neural task not found")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Test 7: Learning Metrics
    print("\n[8] Testing Learning Metrics...")
    try:
        db.save_learning_metrics(
            run_id="test-001",
            total_tasks=18,
            activated_tasks=15,
            skipped_tasks=3,
            avg_quality=0.85,
            error=0.05,
            weights_updated=24,
            improvement=8.0
        )
        print(f"    ✅ Saved learning metrics for test-001")

        # Retrieve
        metrics = db.get_run_metrics("test-001")
        if metrics:
            print(f"    ✅ Retrieved metrics")
            print(f"       Avg Quality: {metrics.get('avg_quality')}")
            print(f"       Improvement: {metrics.get('improvement')}%")
        else:
            print(f"    ⚠️  Metrics not found (may not be implemented in {db.get_backend_type()})")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Test 8: Database Stats
    print("\n[9] Database Statistics...")
    try:
        stats = db.get_stats()
        print(f"    Backend: {db.get_backend_type()}")
        for key, value in stats.items():
            print(f"    {key}: {value}")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    # Health Check
    print("\n[10] Health Check...")
    try:
        healthy = db.health_check()
        if healthy:
            print(f"    ✅ Database is healthy")
        else:
            print(f"    ❌ Database health check failed")
    except Exception as e:
        print(f"    ❌ Failed: {e}")

    print("\n" + "=" * 70)
    print("  ✅ All tests completed!")
    print("=" * 70)

    # Cleanup info
    if db.get_backend_type() == "supabase":
        print("\n💡 To clean up test data:")
        print("  DELETE FROM process_runs WHERE run_id = 'test-001';")
        print("  (This will cascade delete all related records)")
    else:
        print("\n💡 Test data saved to markdown files:")
        print("  db/process_runs.md")
        print("  db/weights.json")
        print("  etc.")

    return True


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"

    if mode not in ["auto", "supabase", "markdown"]:
        print(f"❌ Unknown mode: {mode}")
        print("Usage: python scripts/test_supabase.py [auto|supabase|markdown]")
        sys.exit(1)

    success = test_database(mode)

    if not success:
        print("\n❌ Tests failed")
        print("\n💡 Troubleshooting:")
        print("  Supabase:")
        print("    1. Set environment variables:")
        print("       export SUPABASE_URL=https://xxxxx.supabase.co")
        print("       export SUPABASE_KEY=eyJhbGc...")
        print("    2. Run SQL schema: db_templates/supabase_schema.sql")
        print("")
        print("  Markdown:")
        print("    - No setup needed, uses local files")
        sys.exit(1)

    sys.exit(0)
