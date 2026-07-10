"""Deterministic boundary-surface to solid-face mapping for BLUECAD pressure loads.

Spec 024-B owns this module. The implementation must map Gmsh boundary elements to
exactly one BODY solid-element face using connectivity, emit inspectable evidence,
and fail closed for ambiguous or unsupported topology.
"""

from __future__ import annotations

__all__: list[str] = []
