#!/usr/bin/env python3
"""
Neural DB Initialization Script

Initializes all Neural-CONI database files:
- db/weights.json
- db/execution_history.md
- db/learning_metrics.md
- runs/{run_id}/db/neural_tasks.json
"""

import os
import sys
import json
import argparse
from pathlib import Path


def init_weights_db(db_path: str = "db/weights.json"):
    """Initialize weights database"""
    if os.path.exists(db_path):
        print(f"[INFO] weights.json already exists: {db_path}")
        return

    weights_data = {
        "weights": {},
        "gradients": {},
        "update_counts": {},
        "learning_rate": 0.01
    }

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(weights_data, f, indent=2)

    print(f"[SUCCESS] Created weights.json: {db_path}")


def init_execution_history(db_path: str = "db/execution_history.md"):
    """Initialize execution history database"""
    if os.path.exists(db_path):
        print(f"[INFO] execution_history.md already exists: {db_path}")
        return

    header = """# Execution History

Track all Task executions with neural attributes.

| run_id | task_id | executed | activation | quality | execution_time | tokens | skip_reason |
|--------|---------|----------|------------|---------|----------------|--------|-------------|
"""

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, 'w', encoding='utf-8') as f:
        f.write(header)

    print(f"[SUCCESS] Created execution_history.md: {db_path}")


def init_learning_metrics(db_path: str = "db/learning_metrics.md"):
    """Initialize learning metrics database"""
    if os.path.exists(db_path):
        print(f"[INFO] learning_metrics.md already exists: {db_path}")
        return

    header = """# Learning Metrics

Track quality improvement over runs.

| run_id | total_tasks | activated | skipped | avg_quality | error | weights_updated | improvement |
|--------|-------------|-----------|---------|-------------|-------|-----------------|-------------|
"""

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, 'w', encoding='utf-8') as f:
        f.write(header)

    print(f"[SUCCESS] Created learning_metrics.md: {db_path}")


def init_neural_tasks(run_id: str):
    """Initialize neural_tasks.json for a specific run"""
    db_path = f"runs/{run_id}/db/neural_tasks.json"

    if os.path.exists(db_path):
        print(f"[INFO] neural_tasks.json already exists: {db_path}")
        return

    neural_tasks_data = {}

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(neural_tasks_data, f, indent=2)

    print(f"[SUCCESS] Created neural_tasks.json: {db_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Neural-CONI database files"
    )
    parser.add_argument(
        "--run_id",
        type=str,
        help="Run ID for neural_tasks.json (optional)"
    )
    parser.add_argument(
        "--global-only",
        action="store_true",
        help="Only initialize global DB files"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Neural DB Initialization")
    print("=" * 60)

    # Initialize global DB files
    init_weights_db()
    init_execution_history()
    init_learning_metrics()

    # Initialize run-specific files
    if not args.global_only and args.run_id:
        init_neural_tasks(args.run_id)

    print("=" * 60)
    print("✅ Neural DB initialization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
