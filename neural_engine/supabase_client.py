"""
Supabase Database Client for Neural-CONI

PostgreSQL 기반 관계형 DB로 마크다운 DB의 한계 극복:
- 동시성 문제 해결 (ACID 트랜잭션)
- 빠른 쿼리 (SQL)
- 관계형 데이터 표현 (Task 간 가중치, 의존성)
- 확장성 (무제한 Run 이력)
- Real-time subscriptions
"""

from supabase import create_client, Client
from typing import Dict, List, Optional, Any
import os
import json
from datetime import datetime


class SupabaseDB:
    """Neural-CONI Supabase Database Client"""

    def __init__(
        self,
        url: str = None,
        key: str = None,
        use_env: bool = True
    ):
        """
        Args:
            url: Supabase project URL
            key: Supabase anon/service key
            use_env: Load from environment variables
        """
        if use_env:
            url = os.getenv("SUPABASE_URL", url)
            key = os.getenv("SUPABASE_KEY", key)

        if not url or not key:
            raise ValueError(
                "Supabase URL and KEY required. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )

        self.client: Client = create_client(url, key)
        self.url = url
        print(f"[SupabaseDB] Connected to {url}")

    # ==================== Process Runs ====================

    def create_run(
        self,
        run_id: str,
        user_request: str,
        run_mode: str = "INITIAL_RUN"
    ) -> Dict:
        """
        Create a new Run

        Args:
            run_id: Unique run identifier (e.g., "run-001")
            user_request: User's original request
            run_mode: "INITIAL_RUN" or "CONTINUOUS_RUN"

        Returns:
            Created run record
        """
        data = {
            "run_id": run_id,
            "user_request": user_request,
            "run_mode": run_mode,
            "status": "PENDING"
        }

        response = self.client.table("process_runs").insert(data).execute()
        print(f"[SupabaseDB] Created run: {run_id}")
        return response.data[0] if response.data else {}

    def get_pending_run(self) -> Optional[Dict]:
        """Get the oldest PENDING run"""
        response = self.client.table("process_runs") \
            .select("*") \
            .eq("status", "PENDING") \
            .order("creation_timestamp") \
            .limit(1) \
            .execute()

        return response.data[0] if response.data else None

    def get_run(self, run_id: str) -> Optional[Dict]:
        """Get run by ID"""
        response = self.client.table("process_runs") \
            .select("*") \
            .eq("run_id", run_id) \
            .execute()

        return response.data[0] if response.data else None

    def update_run(self, run_id: str, **updates) -> Dict:
        """
        Update run fields

        Example:
            db.update_run("run-001", status="COMPLETED", current_phase_id="ph-2")
        """
        response = self.client.table("process_runs") \
            .update(updates) \
            .eq("run_id", run_id) \
            .execute()

        return response.data[0] if response.data else {}

    def list_runs(
        self,
        status: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """List runs with optional status filter"""
        query = self.client.table("process_runs").select("*")

        if status:
            query = query.eq("status", status)

        return query.order("creation_timestamp", desc=True).limit(limit).execute().data

    # ==================== Phases ====================

    def create_phase(
        self,
        run_id: str,
        phase_id: str,
        phase_name: str,
        phase_reason: str,
        phase_purpose: str
    ) -> Dict:
        """Create a new Phase"""
        data = {
            "run_id": run_id,
            "phase_id": phase_id,
            "phase_name": phase_name,
            "phase_reason": phase_reason,
            "phase_purpose": phase_purpose,
            "status": "PENDING"
        }

        return self.client.table("phases").insert(data).execute().data[0]

    def get_phases(self, run_id: str, status: str = None) -> List[Dict]:
        """Get phases for a run"""
        query = self.client.table("phases") \
            .select("*") \
            .eq("run_id", run_id)

        if status:
            query = query.eq("status", status)

        return query.order("phase_id").execute().data

    def update_phase(
        self,
        run_id: str,
        phase_id: str,
        **updates
    ) -> Dict:
        """Update phase"""
        response = self.client.table("phases") \
            .update(updates) \
            .eq("run_id", run_id) \
            .eq("phase_id", phase_id) \
            .execute()

        return response.data[0] if response.data else {}

    # ==================== Tasks ====================

    def create_task(
        self,
        run_id: str,
        phase_id: str,
        stage_id: str,
        sub_stage_id: str,
        task_id: str,
        task_name: str,
        task_reason: str,
        task_purpose: str,
        dependencies: List[str] = None,
        threshold: float = 0.6,
        related_references: List[str] = None,
        **extra
    ) -> Dict:
        """Create a single task"""
        data = {
            "run_id": run_id,
            "phase_id": phase_id,
            "stage_id": stage_id,
            "sub_stage_id": sub_stage_id,
            "task_id": task_id,
            "task_name": task_name,
            "task_reason": task_reason,
            "task_purpose": task_purpose,
            "dependencies": json.dumps(dependencies or []),
            "threshold": threshold,
            "related_references": json.dumps(related_references or []),
            "status": "PENDING",
            **extra
        }

        return self.client.table("tasks").insert(data).execute().data[0]

    def create_tasks_batch(self, tasks: List[Dict]) -> List[Dict]:
        """Create multiple tasks at once"""
        # Ensure all tasks have proper JSON fields
        for task in tasks:
            if "dependencies" in task and isinstance(task["dependencies"], list):
                task["dependencies"] = json.dumps(task["dependencies"])
            if "related_references" in task and isinstance(task["related_references"], list):
                task["related_references"] = json.dumps(task["related_references"])

        return self.client.table("tasks").insert(tasks).execute().data

    def get_tasks(
        self,
        run_id: str,
        sub_stage_id: str = None,
        status: str = None
    ) -> List[Dict]:
        """Get tasks for a run/sub-stage"""
        query = self.client.table("tasks") \
            .select("*") \
            .eq("run_id", run_id)

        if sub_stage_id:
            query = query.eq("sub_stage_id", sub_stage_id)

        if status:
            query = query.eq("status", status)

        tasks = query.execute().data

        # Parse JSON fields
        for task in tasks:
            if task.get("dependencies"):
                task["dependencies"] = json.loads(task["dependencies"]) if isinstance(task["dependencies"], str) else task["dependencies"]
            if task.get("related_references"):
                task["related_references"] = json.loads(task["related_references"]) if isinstance(task["related_references"], str) else task["related_references"]

        return tasks

    def get_task(
        self,
        run_id: str,
        task_id: str
    ) -> Optional[Dict]:
        """Get a specific task"""
        response = self.client.table("tasks") \
            .select("*") \
            .eq("run_id", run_id) \
            .eq("task_id", task_id) \
            .execute()

        if response.data:
            task = response.data[0]
            # Parse JSON
            if task.get("dependencies"):
                task["dependencies"] = json.loads(task["dependencies"]) if isinstance(task["dependencies"], str) else task["dependencies"]
            if task.get("related_references"):
                task["related_references"] = json.loads(task["related_references"]) if isinstance(task["related_references"], str) else task["related_references"]
            return task

        return None

    def update_task(
        self,
        run_id: str,
        task_id: str,
        **updates
    ) -> Dict:
        """Update task"""
        # Convert lists to JSON strings if needed
        if "dependencies" in updates and isinstance(updates["dependencies"], list):
            updates["dependencies"] = json.dumps(updates["dependencies"])
        if "related_references" in updates and isinstance(updates["related_references"], list):
            updates["related_references"] = json.dumps(updates["related_references"])

        response = self.client.table("tasks") \
            .update(updates) \
            .eq("run_id", run_id) \
            .eq("task_id", task_id) \
            .execute()

        return response.data[0] if response.data else {}

    # ==================== Weights ====================

    def get_weight(self, from_task: str, to_task: str) -> Optional[float]:
        """Get weight between two tasks"""
        response = self.client.table("weights") \
            .select("weight") \
            .eq("from_task", from_task) \
            .eq("to_task", to_task) \
            .execute()

        return response.data[0]["weight"] if response.data else None

    def set_weight(
        self,
        from_task: str,
        to_task: str,
        weight: float,
        gradient: float = 0.0
    ) -> Dict:
        """Set/update weight (upsert)"""
        response = self.client.table("weights") \
            .select("update_count") \
            .eq("from_task", from_task) \
            .eq("to_task", to_task) \
            .execute()

        current_count = response.data[0]["update_count"] if response.data else 0

        data = {
            "from_task": from_task,
            "to_task": to_task,
            "weight": weight,
            "gradient": gradient,
            "update_count": current_count + 1
        }

        return self.client.table("weights").upsert(data).execute().data[0]

    def get_all_weights(self) -> Dict[str, float]:
        """Get all weights as dict"""
        response = self.client.table("weights").select("*").execute()

        weights = {}
        for row in response.data:
            key = f"{row['from_task']}→{row['to_task']}"
            weights[key] = row["weight"]

        return weights

    def batch_update_weights(self, weights: Dict[str, float]) -> List[Dict]:
        """Batch update weights (for backpropagation)"""
        data = []

        for key, weight in weights.items():
            from_task, to_task = key.split("→")

            # Get current update_count
            existing = self.client.table("weights") \
                .select("update_count") \
                .eq("from_task", from_task) \
                .eq("to_task", to_task) \
                .execute()

            count = existing.data[0]["update_count"] + 1 if existing.data else 1

            data.append({
                "from_task": from_task,
                "to_task": to_task,
                "weight": weight,
                "update_count": count
            })

        return self.client.table("weights").upsert(data).execute().data

    # ==================== Execution History ====================

    def log_execution(
        self,
        run_id: str,
        task_id: str,
        task_name: str,
        executed: bool,
        activation: float = None,
        quality: float = None,
        execution_time: float = None,
        tokens_used: int = None,
        skip_reason: str = None
    ) -> Dict:
        """Log task execution"""
        data = {
            "run_id": run_id,
            "task_id": task_id,
            "task_name": task_name,
            "executed": executed,
            "activation": activation,
            "quality": quality,
            "execution_time": execution_time,
            "tokens_used": tokens_used,
            "skip_reason": skip_reason
        }

        return self.client.table("execution_history").insert(data).execute().data[0]

    def get_execution_history(
        self,
        run_id: str = None,
        task_name: str = None,
        executed: bool = None,
        limit: int = 100
    ) -> List[Dict]:
        """Query execution history"""
        query = self.client.table("execution_history").select("*")

        if run_id:
            query = query.eq("run_id", run_id)
        if task_name:
            query = query.eq("task_name", task_name)
        if executed is not None:
            query = query.eq("executed", executed)

        return query.order("executed_at", desc=True).limit(limit).execute().data

    # ==================== Neural Tasks ====================

    def create_neural_task(
        self,
        run_id: str,
        task_id: str,
        activation_level: float = None,
        threshold: float = 0.6,
        quality_score: float = None,
        selected_files: List[str] = None,
        attention_weights: Dict[str, float] = None,
        **extra
    ) -> Dict:
        """Create/update neural task attributes"""
        data = {
            "run_id": run_id,
            "task_id": task_id,
            "activation_level": activation_level,
            "threshold": threshold,
            "quality_score": quality_score,
            "selected_files": json.dumps(selected_files) if selected_files else None,
            "attention_weights": json.dumps(attention_weights) if attention_weights else None,
            **extra
        }

        return self.client.table("neural_tasks").upsert(data).execute().data[0]

    def get_neural_task(self, run_id: str, task_id: str) -> Optional[Dict]:
        """Get neural task attributes"""
        response = self.client.table("neural_tasks") \
            .select("*") \
            .eq("run_id", run_id) \
            .eq("task_id", task_id) \
            .execute()

        if response.data:
            task = response.data[0]
            # Parse JSON
            if task.get("selected_files"):
                task["selected_files"] = json.loads(task["selected_files"]) if isinstance(task["selected_files"], str) else task["selected_files"]
            if task.get("attention_weights"):
                task["attention_weights"] = json.loads(task["attention_weights"]) if isinstance(task["attention_weights"], str) else task["attention_weights"]
            return task

        return None

    def get_neural_tasks(self, run_id: str) -> List[Dict]:
        """Get all neural tasks for a run"""
        tasks = self.client.table("neural_tasks") \
            .select("*") \
            .eq("run_id", run_id) \
            .execute().data

        # Parse JSON fields
        for task in tasks:
            if task.get("selected_files"):
                task["selected_files"] = json.loads(task["selected_files"]) if isinstance(task["selected_files"], str) else task["selected_files"]
            if task.get("attention_weights"):
                task["attention_weights"] = json.loads(task["attention_weights"]) if isinstance(task["attention_weights"], str) else task["attention_weights"]

        return tasks

    # ==================== Learning Metrics ====================

    def save_learning_metrics(
        self,
        run_id: str,
        total_tasks: int,
        activated_tasks: int,
        skipped_tasks: int,
        avg_quality: float,
        error: float,
        weights_updated: int,
        improvement: float = None
    ) -> Dict:
        """Save learning metrics for a run"""
        data = {
            "run_id": run_id,
            "total_tasks": total_tasks,
            "activated_tasks": activated_tasks,
            "skipped_tasks": skipped_tasks,
            "avg_quality": avg_quality,
            "error": error,
            "weights_updated": weights_updated,
            "improvement": improvement
        }

        return self.client.table("learning_metrics").insert(data).execute().data[0]

    def get_learning_metrics(self, limit: int = 10) -> List[Dict]:
        """Get recent learning metrics"""
        return self.client.table("learning_metrics") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute().data

    def get_run_metrics(self, run_id: str) -> Optional[Dict]:
        """Get metrics for a specific run"""
        response = self.client.table("learning_metrics") \
            .select("*") \
            .eq("run_id", run_id) \
            .execute()

        return response.data[0] if response.data else None

    # ==================== Utility Methods ====================

    def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            # Simple query to check connection
            self.client.table("process_runs").select("run_id").limit(1).execute()
            return True
        except Exception as e:
            print(f"[SupabaseDB] Health check failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}

        try:
            stats["total_runs"] = len(self.client.table("process_runs").select("run_id").execute().data)
            stats["total_weights"] = len(self.client.table("weights").select("from_task").execute().data)
            stats["total_executions"] = len(self.client.table("execution_history").select("id").execute().data)
            stats["pending_runs"] = len(self.client.table("process_runs").select("run_id").eq("status", "PENDING").execute().data)
        except Exception as e:
            stats["error"] = str(e)

        return stats


# Global singleton instance
_global_db = None

def get_supabase_db(url: str = None, key: str = None) -> SupabaseDB:
    """Get global Supabase DB instance (singleton)"""
    global _global_db

    if _global_db is None:
        _global_db = SupabaseDB(url=url, key=key, use_env=True)

    return _global_db
