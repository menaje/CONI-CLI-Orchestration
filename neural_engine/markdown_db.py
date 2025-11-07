"""
Markdown Database Wrapper for Neural-CONI

Provides Supabase-compatible interface for Markdown-based storage
(backward compatibility with existing file-based DB)
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class MarkdownDB:
    """
    Markdown-based database with Supabase-compatible interface

    Uses file system for storage:
    - db/process_runs.md
    - db/weights.json
    - db/execution_history.md
    - db/learning_metrics.md
    - runs/{run_id}/db/neural_tasks.json
    """

    def __init__(self, base_path: str = "."):
        """
        Args:
            base_path: Base directory path (default: current directory)
        """
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "db"
        self.db_path.mkdir(exist_ok=True)

        print(f"[MarkdownDB] Initialized at {self.base_path}")

    # ==================== Process Runs ====================

    def create_run(
        self,
        run_id: str,
        user_request: str,
        run_mode: str = "INITIAL_RUN"
    ) -> Dict:
        """Create a new run"""
        runs_file = self.db_path / "process_runs.md"

        # Create file if not exists
        if not runs_file.exists():
            with open(runs_file, 'w', encoding='utf-8') as f:
                f.write("# Process Runs\n\n")
                f.write("| run_id | creation_timestamp | user_request | status | current_phase_id | current_stage_id | current_sub_stage_id | current_task_id |\n")
                f.write("|--------|-------------------|--------------|--------|-----------------|-----------------|---------------------|----------------|\n")

        # Append new run
        timestamp = datetime.now().isoformat()
        with open(runs_file, 'a', encoding='utf-8') as f:
            f.write(f"| {run_id} | {timestamp} | {user_request} | PENDING | | | | |\n")

        print(f"[MarkdownDB] Created run: {run_id}")

        return {
            "run_id": run_id,
            "creation_timestamp": timestamp,
            "user_request": user_request,
            "status": "PENDING",
            "run_mode": run_mode
        }

    def get_pending_run(self) -> Optional[Dict]:
        """Get oldest pending run"""
        runs = self._read_runs_table()

        for run in runs:
            if run.get("status") == "PENDING":
                return run

        return None

    def get_run(self, run_id: str) -> Optional[Dict]:
        """Get run by ID"""
        runs = self._read_runs_table()

        for run in runs:
            if run.get("run_id") == run_id:
                return run

        return None

    def update_run(self, run_id: str, **updates) -> Dict:
        """Update run (rewrites entire file)"""
        runs = self._read_runs_table()

        for run in runs:
            if run["run_id"] == run_id:
                run.update(updates)

        self._write_runs_table(runs)

        return self.get_run(run_id)

    def list_runs(self, status: str = None, limit: int = 50) -> List[Dict]:
        """List runs"""
        runs = self._read_runs_table()

        if status:
            runs = [r for r in runs if r.get("status") == status]

        return runs[:limit]

    def _read_runs_table(self) -> List[Dict]:
        """Parse process_runs.md into list of dicts"""
        runs_file = self.db_path / "process_runs.md"

        if not runs_file.exists():
            return []

        with open(runs_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        runs = []
        for line in lines:
            if line.startswith("|") and "run_id" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 4:
                    runs.append({
                        "run_id": parts[0],
                        "creation_timestamp": parts[1],
                        "user_request": parts[2],
                        "status": parts[3],
                        "current_phase_id": parts[4] if len(parts) > 4 else "",
                        "current_stage_id": parts[5] if len(parts) > 5 else "",
                        "current_sub_stage_id": parts[6] if len(parts) > 6 else "",
                        "current_task_id": parts[7] if len(parts) > 7 else ""
                    })

        return runs

    def _write_runs_table(self, runs: List[Dict]):
        """Write runs back to process_runs.md"""
        runs_file = self.db_path / "process_runs.md"

        with open(runs_file, 'w', encoding='utf-8') as f:
            f.write("# Process Runs\n\n")
            f.write("| run_id | creation_timestamp | user_request | status | current_phase_id | current_stage_id | current_sub_stage_id | current_task_id |\n")
            f.write("|--------|-------------------|--------------|--------|-----------------|-----------------|---------------------|----------------|\n")

            for run in runs:
                f.write(f"| {run['run_id']} | {run.get('creation_timestamp', '')} | "
                       f"{run.get('user_request', '')} | {run.get('status', '')} | "
                       f"{run.get('current_phase_id', '')} | {run.get('current_stage_id', '')} | "
                       f"{run.get('current_sub_stage_id', '')} | {run.get('current_task_id', '')} |\n")

    # ==================== Phases (Simplified) ====================

    def create_phase(self, run_id: str, phase_id: str, **kwargs) -> Dict:
        """Create phase (stores in runs/{run_id}/db/phases.md)"""
        phase_file = self.base_path / "runs" / run_id / "db" / "phases.md"
        phase_file.parent.mkdir(parents=True, exist_ok=True)

        # Create table if not exists
        if not phase_file.exists():
            with open(phase_file, 'w', encoding='utf-8') as f:
                f.write("# Phases\n\n")
                f.write("| phase_id | phase_name | phase_reason | phase_purpose | status |\n")
                f.write("|----------|------------|--------------|---------------|--------|\n")

        # Append phase
        with open(phase_file, 'a', encoding='utf-8') as f:
            f.write(f"| {phase_id} | {kwargs.get('phase_name', '')} | "
                   f"{kwargs.get('phase_reason', '')} | {kwargs.get('phase_purpose', '')} | PENDING |\n")

        return {"run_id": run_id, "phase_id": phase_id, **kwargs}

    def get_phases(self, run_id: str, status: str = None) -> List[Dict]:
        """Get phases (simplified - returns empty for now)"""
        return []

    def update_phase(self, run_id: str, phase_id: str, **updates) -> Dict:
        """Update phase (simplified)"""
        return {"run_id": run_id, "phase_id": phase_id, **updates}

    # ==================== Tasks (Simplified) ====================

    def create_task(self, run_id: str, **kwargs) -> Dict:
        """Create task (simplified)"""
        return {"run_id": run_id, **kwargs}

    def create_tasks_batch(self, tasks: List[Dict]) -> List[Dict]:
        """Create tasks batch (simplified)"""
        return tasks

    def get_tasks(self, run_id: str, **filters) -> List[Dict]:
        """Get tasks (simplified)"""
        return []

    def get_task(self, run_id: str, task_id: str) -> Optional[Dict]:
        """Get task (simplified)"""
        return None

    def update_task(self, run_id: str, task_id: str, **updates) -> Dict:
        """Update task (simplified)"""
        return {"run_id": run_id, "task_id": task_id, **updates}

    # ==================== Weights ====================

    def get_weight(self, from_task: str, to_task: str) -> Optional[float]:
        """Get weight"""
        weights = self._read_weights()
        key = f"{from_task}→{to_task}"
        return weights.get("weights", {}).get(key)

    def set_weight(
        self,
        from_task: str,
        to_task: str,
        weight: float,
        gradient: float = 0.0
    ) -> Dict:
        """Set weight"""
        data = self._read_weights()

        key = f"{from_task}→{to_task}"
        data["weights"][key] = weight
        data["gradients"][key] = gradient
        data["update_counts"][key] = data["update_counts"].get(key, 0) + 1

        self._write_weights(data)

        return {
            "from_task": from_task,
            "to_task": to_task,
            "weight": weight,
            "gradient": gradient
        }

    def get_all_weights(self) -> Dict[str, float]:
        """Get all weights"""
        data = self._read_weights()
        return data.get("weights", {})

    def batch_update_weights(self, weights: Dict[str, float]) -> List[Dict]:
        """Batch update weights"""
        data = self._read_weights()

        for key, weight in weights.items():
            data["weights"][key] = weight
            data["update_counts"][key] = data["update_counts"].get(key, 0) + 1

        self._write_weights(data)

        return [{"key": k, "weight": w} for k, w in weights.items()]

    def _read_weights(self) -> Dict:
        """Read weights.json"""
        weights_file = self.db_path / "weights.json"

        if not weights_file.exists():
            return {
                "weights": {},
                "gradients": {},
                "update_counts": {},
                "learning_rate": 0.01
            }

        with open(weights_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_weights(self, data: Dict):
        """Write weights.json"""
        weights_file = self.db_path / "weights.json"

        with open(weights_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    # ==================== Execution History ====================

    def log_execution(
        self,
        run_id: str,
        task_id: str,
        task_name: str,
        executed: bool,
        **kwargs
    ) -> Dict:
        """Log execution"""
        history_file = self.db_path / "execution_history.md"

        if not history_file.exists():
            with open(history_file, 'w', encoding='utf-8') as f:
                f.write("# Execution History\n\n")
                f.write("| run_id | task_id | executed | activation | quality | execution_time | tokens | skip_reason |\n")
                f.write("|--------|---------|----------|------------|---------|----------------|--------|-------------|\n")

        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(f"| {run_id} | {task_id} | {executed} | "
                   f"{kwargs.get('activation', '')} | {kwargs.get('quality', '')} | "
                   f"{kwargs.get('execution_time', '')} | {kwargs.get('tokens_used', '')} | "
                   f"{kwargs.get('skip_reason', '')} |\n")

        return {"run_id": run_id, "task_id": task_id, "executed": executed, **kwargs}

    def get_execution_history(self, **filters) -> List[Dict]:
        """Get execution history (simplified)"""
        return []

    # ==================== Neural Tasks ====================

    def create_neural_task(self, run_id: str, task_id: str, **attributes) -> Dict:
        """Create/update neural task"""
        neural_file = self.base_path / "runs" / run_id / "db" / "neural_tasks.json"
        neural_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing
        if neural_file.exists():
            with open(neural_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}

        # Update
        data[task_id] = attributes

        # Write
        with open(neural_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return {"run_id": run_id, "task_id": task_id, **attributes}

    def get_neural_task(self, run_id: str, task_id: str) -> Optional[Dict]:
        """Get neural task"""
        neural_file = self.base_path / "runs" / run_id / "db" / "neural_tasks.json"

        if not neural_file.exists():
            return None

        with open(neural_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data.get(task_id)

    def get_neural_tasks(self, run_id: str) -> List[Dict]:
        """Get all neural tasks"""
        neural_file = self.base_path / "runs" / run_id / "db" / "neural_tasks.json"

        if not neural_file.exists():
            return []

        with open(neural_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [{"task_id": k, **v} for k, v in data.items()]

    # ==================== Learning Metrics ====================

    def save_learning_metrics(self, run_id: str, **metrics) -> Dict:
        """Save learning metrics"""
        metrics_file = self.db_path / "learning_metrics.md"

        if not metrics_file.exists():
            with open(metrics_file, 'w', encoding='utf-8') as f:
                f.write("# Learning Metrics\n\n")
                f.write("| run_id | total_tasks | activated | skipped | avg_quality | error | weights_updated | improvement |\n")
                f.write("|--------|-------------|-----------|---------|-------------|-------|-----------------|-------------|\n")

        with open(metrics_file, 'a', encoding='utf-8') as f:
            f.write(f"| {run_id} | {metrics.get('total_tasks', '')} | "
                   f"{metrics.get('activated_tasks', '')} | {metrics.get('skipped_tasks', '')} | "
                   f"{metrics.get('avg_quality', '')} | {metrics.get('error', '')} | "
                   f"{metrics.get('weights_updated', '')} | {metrics.get('improvement', '')} |\n")

        return {"run_id": run_id, **metrics}

    def get_learning_metrics(self, limit: int = 10) -> List[Dict]:
        """Get learning metrics (simplified)"""
        return []

    def get_run_metrics(self, run_id: str) -> Optional[Dict]:
        """Get metrics for run (simplified)"""
        return None

    # ==================== Utility ====================

    def health_check(self) -> bool:
        """Health check"""
        return self.db_path.exists()

    def get_stats(self) -> Dict:
        """Get stats"""
        runs = self._read_runs_table()
        weights = self._read_weights()

        return {
            "backend": "markdown",
            "total_runs": len(runs),
            "total_weights": len(weights.get("weights", {})),
            "db_path": str(self.db_path)
        }
