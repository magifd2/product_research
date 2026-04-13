"""GCP configuration management for product-research."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any


def _load_toml(tool_name: str) -> dict[str, Any]:
    """Load TOML config from ~/.config/<tool_name>/config.toml if it exists."""
    path = Path.home() / ".config" / tool_name / "config.toml"
    if not path.is_file():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    flat: dict[str, Any] = {}
    if "gcp" in data and isinstance(data["gcp"], dict):
        if "project" in data["gcp"]:
            flat["project"] = data["gcp"]["project"]
        if "location" in data["gcp"]:
            flat["location"] = data["gcp"]["location"]
    return flat


def get_config() -> dict[str, str]:
    """Load GCP configuration with priority: env vars > config.toml > defaults.

    Returns:
        dict with keys: project, location
    """
    toml = _load_toml("product-research")

    project = (
        os.environ.get("PRODUCT_RESEARCH_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or toml.get("project", "")
    )
    location = (
        os.environ.get("PRODUCT_RESEARCH_LOCATION")
        or os.environ.get("GOOGLE_CLOUD_LOCATION")
        or toml.get("location", "us-central1")
    )

    if not project:
        raise ValueError(
            "GCP project is required. Set PRODUCT_RESEARCH_PROJECT, "
            "GOOGLE_CLOUD_PROJECT, or gcp.project in ~/.config/product-research/config.toml"
        )

    return {"project": project, "location": location}
