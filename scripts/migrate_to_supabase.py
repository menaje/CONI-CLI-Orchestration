#!/usr/bin/env python3
"""
Migrate Markdown DB to Supabase

Migrates existing data from markdown files to Supabase database:
- db/process_runs.md → process_runs table
- db/weights.json → weights table
- db/execution_history.md → execution_history table
- db/learning_metrics.md → learning_metrics table

Usage:
    python scripts/migrate_to_supabase.py [--dry-run]
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural_engine.supabase_client import get_supabase_db
from neural_engine.markdown_db import MarkdownDB


def migrate_weights(dry_run: bool = False):
    """Migrate db/weights.json → Supabase weights table"""
    print("\n" + "=" * 60)
    print("Migrating Weights")
    print("=" * 60)

    weights_file = Path("db/weights.json")

    if not weights_file.exists():
        print("⚠️  No weights.json found, skipping...")
        return

    with open(weights_file, 'r') as f:
        data = json.load(f)

    weights = data.get("weights", {})
    gradients = data.get("gradients", {})

    print(f"Found {len(weights)} weights to migrate")

    if dry_run:
        print("\n[DRY RUN] Would migrate:")
        for key, weight in list(weights.items())[:5]:
            from_task, to_task = key.split("→")
            print(f"  {from_task} → {to_task}: {weight:.4f}")
        if len(weights) > 5:
            print(f"  ... and {len(weights) - 5} more")
        return

    # Actual migration
    db = get_supabase_db()

    migrated = 0
    for key, weight in weights.items():
        from_task, to_task = key.split("→")
        gradient = gradients.get(key, 0.0)

        try:
            db.set_weight(from_task, to_task, weight, gradient)
            migrated += 1
        except Exception as e:
            print(f"❌ Failed to migrate {key}: {e}")

    print(f"✅ Migrated {migrated}/{len(weights)} weights")


def migrate_execution_history(dry_run: bool = False):
    """Migrate db/execution_history.md → Supabase execution_history table"""
    print("\n" + "=" * 60)
    print("Migrating Execution History")
    print("=" * 60)

    history_file = Path("db/execution_history.md")

    if not history_file.exists():
        print("⚠️  No execution_history.md found, skipping...")
        return

    with open(history_file, 'r') as f:
        lines = f.readlines()

    # Parse markdown table
    records = []
    for line in lines:
        if line.startswith("|") and "run_id" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 7:
                records.append({
                    "run_id": parts[0],
                    "task_id": parts[1],
                    "executed": parts[2].upper() == "TRUE",
                    "activation": float(parts[3]) if parts[3] and parts[3] != "-" else None,
                    "quality": float(parts[4]) if parts[4] and parts[4] != "-" else None,
                    "execution_time": float(parts[5]) if parts[5] and parts[5] != "-" else None,
                    "tokens_used": int(parts[6]) if parts[6] and parts[6] != "-" else None,
                    "skip_reason": parts[7] if len(parts) > 7 and parts[7] != "-" else None
                })

    print(f"Found {len(records)} execution records to migrate")

    if dry_run:
        print("\n[DRY RUN] Would migrate:")
        for record in records[:5]:
            print(f"  {record['run_id']} - {record['task_id']}: "
                  f"executed={record['executed']}, quality={record.get('quality')}")
        if len(records) > 5:
            print(f"  ... and {len(records) - 5} more")
        return

    # Actual migration
    db = get_supabase_db()

    migrated = 0
    for record in records:
        try:
            db.log_execution(
                run_id=record["run_id"],
                task_id=record["task_id"],
                task_name=record.get("task_name", ""),
                executed=record["executed"],
                activation=record.get("activation"),
                quality=record.get("quality"),
                execution_time=record.get("execution_time"),
                tokens_used=record.get("tokens_used"),
                skip_reason=record.get("skip_reason")
            )
            migrated += 1
        except Exception as e:
            print(f"❌ Failed to migrate {record['run_id']}/{record['task_id']}: {e}")

    print(f"✅ Migrated {migrated}/{len(records)} execution records")


def migrate_learning_metrics(dry_run: bool = False):
    """Migrate db/learning_metrics.md → Supabase learning_metrics table"""
    print("\n" + "=" * 60)
    print("Migrating Learning Metrics")
    print("=" * 60)

    metrics_file = Path("db/learning_metrics.md")

    if not metrics_file.exists():
        print("⚠️  No learning_metrics.md found, skipping...")
        return

    with open(metrics_file, 'r') as f:
        lines = f.readlines()

    # Parse markdown table
    records = []
    for line in lines:
        if line.startswith("|") and "run_id" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 7:
                records.append({
                    "run_id": parts[0],
                    "total_tasks": int(parts[1]) if parts[1] else 0,
                    "activated_tasks": int(parts[2]) if parts[2] else 0,
                    "skipped_tasks": int(parts[3]) if parts[3] else 0,
                    "avg_quality": float(parts[4]) if parts[4] else 0.0,
                    "error": float(parts[5]) if parts[5] else 0.0,
                    "weights_updated": int(parts[6]) if parts[6] else 0,
                    "improvement": float(parts[7]) if len(parts) > 7 and parts[7] else None
                })

    print(f"Found {len(records)} learning metric records to migrate")

    if dry_run:
        print("\n[DRY RUN] Would migrate:")
        for record in records[:5]:
            print(f"  {record['run_id']}: quality={record['avg_quality']:.2f}, "
                  f"improvement={record.get('improvement')}")
        if len(records) > 5:
            print(f"  ... and {len(records) - 5} more")
        return

    # Actual migration
    db = get_supabase_db()

    migrated = 0
    for record in records:
        try:
            db.save_learning_metrics(**record)
            migrated += 1
        except Exception as e:
            print(f"❌ Failed to migrate metrics for {record['run_id']}: {e}")

    print(f"✅ Migrated {migrated}/{len(records)} learning metric records")


def main():
    parser = argparse.ArgumentParser(description="Migrate Markdown DB to Supabase")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually migrating"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Neural-CONI: Markdown → Supabase Migration")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No data will be written to Supabase\n")

    # Check Supabase connection
    if not args.dry_run:
        print("\n[1] Checking Supabase connection...")
        try:
            db = get_supabase_db()
            if not db.health_check():
                print("❌ Supabase health check failed!")
                print("\n💡 Make sure:")
                print("  1. SUPABASE_URL is set")
                print("  2. SUPABASE_KEY is set")
                print("  3. Database schema is created (run supabase_schema.sql)")
                sys.exit(1)
            print("✅ Supabase connection OK")
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            sys.exit(1)

    # Run migrations
    print("\n[2] Starting migrations...")

    migrate_weights(dry_run=args.dry_run)
    migrate_execution_history(dry_run=args.dry_run)
    migrate_learning_metrics(dry_run=args.dry_run)

    print("\n" + "=" * 60)
    if args.dry_run:
        print("✅ Dry run complete! Run without --dry-run to actually migrate.")
    else:
        print("✅ Migration complete!")
    print("=" * 60)

    # Show stats
    if not args.dry_run:
        print("\n[3] Supabase database stats:")
        db = get_supabase_db()
        stats = db.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
