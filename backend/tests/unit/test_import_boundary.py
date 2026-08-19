"""Contracts stay pure: schemas/ and domain/ import only stdlib, pydantic, and each other."""

from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parents[2] / "app"
PURE_PACKAGES = ("domain", "schemas")
ALLOWED_THIRD_PARTY = {"pydantic"}
ALLOWED_APP_PREFIXES = ("app.domain", "app.schemas")


def _top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _is_allowed(module_name: str) -> bool:
    root = module_name.split(".")[0]
    if root in sys.stdlib_module_names or root in ALLOWED_THIRD_PARTY:
        return True
    return module_name.startswith(ALLOWED_APP_PREFIXES)


@pytest.mark.parametrize("package", PURE_PACKAGES)
def test_pure_packages_import_only_stdlib_and_pydantic(package: str) -> None:
    for path in (APP_DIR / package).rglob("*.py"):
        offending = {name for name in _top_level_imports(path) if not _is_allowed(name)}
        assert not offending, f"{path.relative_to(APP_DIR)} imports {sorted(offending)}"


def _schema_models() -> list[type[BaseModel]]:
    models: list[type[BaseModel]] = []
    for path in (APP_DIR / "schemas").glob("*.py"):
        if path.name == "__init__.py":
            continue
        module = importlib.import_module(f"app.schemas.{path.stem}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == module.__name__
            ):
                models.append(obj)
    return models


def test_every_schema_model_forbids_extra_fields() -> None:
    models = _schema_models()
    assert models, "no schema models found"
    lax = [model.__name__ for model in models if model.model_config.get("extra") != "forbid"]
    assert not lax, f"models without extra='forbid': {lax}"


def test_outline_modules_import_cleanly() -> None:
    importlib.import_module("app.orchestration.workflow")
    importlib.import_module("app.agents.factory")
