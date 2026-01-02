"""
Compatibility shim for simulations importing `shared.physics_engine`.

The canonical `Physics` class lives at repo-root in `physics_engine.py`.
"""

from __future__ import annotations

from physics_engine import Physics

__all__ = ["Physics"]

