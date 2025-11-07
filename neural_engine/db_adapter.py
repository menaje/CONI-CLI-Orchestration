"""
Hybrid Database Adapter for Neural-CONI

Automatically chooses between Supabase and Markdown based on availability:
1. Supabase (preferred): If SUPABASE_URL and SUPABASE_KEY are set
2. Markdown (fallback): If Supabase is not available

Usage:
    from neural_engine.db_adapter import get_db

    db = get_db()
    db.create_run("run-001", "User request", "INITIAL_RUN")
"""

import os
from typing import Dict, List, Optional, Any


class HybridDB:
    """
    Hybrid Database Adapter

    Automatically selects Supabase or Markdown based on environment
    """

    def __init__(
        self,
        mode: str = "auto",  # auto | supabase | markdown
        supabase_url: str = None,
        supabase_key: str = None
    ):
        """
        Args:
            mode: "auto" (detect), "supabase" (force), "markdown" (force)
            supabase_url: Supabase URL (optional)
            supabase_key: Supabase key (optional)
        """
        self.mode = mode
        self.backend = None
        self.backend_type = None

        # Auto-detect or force mode
        if mode == "auto":
            self.backend_type = self._detect_backend()
        elif mode == "supabase":
            self.backend_type = "supabase"
        elif mode == "markdown":
            self.backend_type = "markdown"
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'auto', 'supabase', or 'markdown'")

        # Initialize backend
        self._init_backend(supabase_url, supabase_key)

    def _detect_backend(self) -> str:
        """Auto-detect which backend to use"""
        # Check if Supabase credentials are available
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if supabase_url and supabase_key:
            print("[HybridDB] Auto-detected: Supabase")
            return "supabase"
        else:
            print("[HybridDB] Auto-detected: Markdown (Supabase credentials not found)")
            return "markdown"

    def _init_backend(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the selected backend"""
        if self.backend_type == "supabase":
            try:
                from neural_engine.supabase_client import SupabaseDB
                self.backend = SupabaseDB(url=supabase_url, key=supabase_key, use_env=True)
                print(f"[HybridDB] Using Supabase backend")
            except Exception as e:
                print(f"[HybridDB] Failed to initialize Supabase: {e}")
                print(f"[HybridDB] Falling back to Markdown")
                self.backend_type = "markdown"
                self._init_markdown_backend()
        else:
            self._init_markdown_backend()

    def _init_markdown_backend(self):
        """Initialize Markdown backend"""
        from neural_engine.markdown_db import MarkdownDB
        self.backend = MarkdownDB()
        print(f"[HybridDB] Using Markdown backend")

    # ==================== Delegate all methods to backend ====================

    def __getattr__(self, name):
        """Delegate all method calls to the backend"""
        if self.backend is None:
            raise RuntimeError("Backend not initialized")

        return getattr(self.backend, name)

    # ==================== Additional hybrid-specific methods ====================

    def get_backend_type(self) -> str:
        """Get current backend type"""
        return self.backend_type

    def is_supabase(self) -> bool:
        """Check if using Supabase backend"""
        return self.backend_type == "supabase"

    def is_markdown(self) -> bool:
        """Check if using Markdown backend"""
        return self.backend_type == "markdown"


# Global singleton instance
_global_db = None

def get_db(
    mode: str = "auto",
    supabase_url: str = None,
    supabase_key: str = None,
    force_new: bool = False
) -> HybridDB:
    """
    Get global database instance (singleton)

    Args:
        mode: "auto" (default), "supabase", or "markdown"
        supabase_url: Supabase URL (optional)
        supabase_key: Supabase key (optional)
        force_new: Force create new instance

    Returns:
        HybridDB instance

    Example:
        # Auto-detect (Supabase if available, else Markdown)
        db = get_db()

        # Force Supabase
        db = get_db(mode="supabase")

        # Force Markdown
        db = get_db(mode="markdown")
    """
    global _global_db

    if _global_db is None or force_new:
        _global_db = HybridDB(
            mode=mode,
            supabase_url=supabase_url,
            supabase_key=supabase_key
        )

    return _global_db


def reset_db():
    """Reset global database instance (useful for testing)"""
    global _global_db
    _global_db = None
