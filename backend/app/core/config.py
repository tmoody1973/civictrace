"""Vertex AI environment for the real agent runner. Read once, fail fast, never a key file."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_LOCATION = "global"  # Gemini 3.x Flash is served only from Vertex location "global"
DEFAULT_MODEL = "gemini-3.7-flash"


@dataclass(frozen=True)
class VertexConfig:
    project: str
    location: str
    model: str


def require_vertex_config(env: dict[str, str] | None = None) -> VertexConfig:
    """Build the Vertex config or explain exactly what is missing.

    Auth itself is Application Default Credentials (`gcloud auth application-default login`),
    resolved by the google-genai SDK; see docs/runbooks/local-vertex-setup.md.
    """
    values = env if env is not None else dict(os.environ)
    project = values.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not project:
        raise RuntimeError(
            "GOOGLE_CLOUD_PROJECT is not set. The --runner adk path needs your Google Cloud "
            "dev project and local sign-in. Follow docs/runbooks/local-vertex-setup.md, "
            "then export GOOGLE_CLOUD_PROJECT (or put it in .env)."
        )
    return VertexConfig(
        project=project,
        location=values.get("GOOGLE_CLOUD_LOCATION", "").strip() or DEFAULT_LOCATION,
        model=values.get("CIVICTRACE_MODEL", "").strip() or DEFAULT_MODEL,
    )


def apply_vertex_env(config: VertexConfig) -> None:
    """Point the google-genai SDK (used by ADK) at Vertex with ADC."""
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = config.project
    os.environ["GOOGLE_CLOUD_LOCATION"] = config.location
