#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import dataclasses
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_PATH = ROOT / "compatibility.json"
COMPONENTS: dict[str, dict[str, str]] = {
    "windows-lead": {
        "key": "windows_lead",
        "path": "components/windows-lead",
    },
    "mac-runner": {
        "key": "mac_runner",
        "path": "components/mac-runner",
    },
}


class UpdateError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class UpdatePlan:
    label: str
    key: str
    path: Path
    relative_path: str
    current_commit: str
    remote_commit: str

    @property
    def changed(self) -> bool:
        return self.current_commit != self.remote_commit


def run_git(*arguments: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise UpdateError(completed.stderr.strip() or f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def load_manifest() -> dict[str, Any]:
    value = json.loads(COMPATIBILITY_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("components"), dict):
        raise UpdateError("compatibility.json has an invalid component structure")
    return value


def load_modules() -> configparser.ConfigParser:
    modules = configparser.ConfigParser()
    if not modules.read(ROOT / ".gitmodules", encoding="utf-8"):
        raise UpdateError(".gitmodules is missing")
    return modules


def write_manifest(value: dict[str, Any]) -> None:
    temporary = COMPATIBILITY_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(COMPATIBILITY_PATH)


def validate_component(
    label: str,
    manifest: dict[str, Any],
    modules: configparser.ConfigParser,
) -> tuple[str, dict[str, Any], str, Path]:
    definition = COMPONENTS[label]
    key = definition["key"]
    expected_path = definition["path"]
    component = manifest["components"].get(key)
    if not isinstance(component, dict):
        raise UpdateError(f"compatibility.json is missing {key}")
    relative_path = str(component.get("path") or "")
    if relative_path != expected_path:
        raise UpdateError(f"{key} path must be exactly {expected_path}")
    path = (ROOT / relative_path).resolve()
    components_root = (ROOT / "components").resolve()
    if path.parent != components_root:
        raise UpdateError(f"component path escaped the expected root: {relative_path}")

    section = f'submodule "{expected_path}"'
    if not modules.has_section(section) or modules.get(section, "path", fallback="") != expected_path:
        raise UpdateError(f".gitmodules does not declare the expected path: {expected_path}")
    if not (path / ".git").exists():
        raise UpdateError(f"submodule is not initialized: {path.relative_to(ROOT)}")
    return key, component, relative_path, path


def preflight_component(
    label: str,
    manifest: dict[str, Any],
    modules: configparser.ConfigParser,
) -> UpdatePlan:
    key, component, relative_path, path = validate_component(label, manifest, modules)
    if run_git("status", "--porcelain", cwd=path):
        raise UpdateError(f"submodule contains uncommitted changes: {path.relative_to(ROOT)}")

    branch = str(component.get("branch") or "main")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", branch):
        raise UpdateError(f"unsafe branch name for {relative_path}")
    remote_ref = f"refs/remotes/origin/{branch}"
    refspec = f"+refs/heads/{branch}:{remote_ref}"
    run_git("fetch", "--prune", "origin", refspec, cwd=path)
    current = run_git("rev-parse", "HEAD", cwd=path)
    remote = run_git("rev-parse", remote_ref, cwd=path)
    ahead = int(run_git("rev-list", "--count", f"{remote_ref}..HEAD", cwd=path))
    if ahead:
        raise UpdateError(
            f"{relative_path} has {ahead} commit(s) not published on origin/{branch}; "
            "push or reconcile them in the component repository first"
        )
    return UpdatePlan(
        label=label,
        key=key,
        path=path,
        relative_path=relative_path,
        current_commit=current,
        remote_commit=remote,
    )


def apply_plans(plans: list[UpdatePlan], manifest: dict[str, Any]) -> list[str]:
    changed_paths: list[str] = []
    for plan in plans:
        if not plan.changed:
            continue
        run_git("checkout", "--detach", plan.remote_commit, cwd=plan.path)
        manifest["components"][plan.key]["commit"] = plan.remote_commit
        changed_paths.append(plan.relative_path)
    return changed_paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update public component submodules and compatibility.json without committing or pushing."
    )
    parser.add_argument(
        "component",
        nargs="?",
        default="all",
        choices=["all", *COMPONENTS],
    )
    arguments = parser.parse_args()

    try:
        if run_git("status", "--porcelain"):
            raise UpdateError("superproject worktree must be clean before updating components")
        manifest = load_manifest()
        modules = load_modules()
        labels = list(COMPONENTS) if arguments.component == "all" else [arguments.component]
        plans = [preflight_component(label, manifest, modules) for label in labels]
        changed_paths = apply_plans(plans, manifest)
        if changed_paths:
            write_manifest(manifest)

        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_system.py")],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode != 0:
            raise UpdateError("component verification failed; inspect the compatibility changes")
    except (OSError, ValueError, UpdateError) as error:
        print(f"update failed: {error}", file=sys.stderr)
        return 1

    if not changed_paths:
        print("all selected components are already pinned to origin/main")
        return 0

    print("updated component checkout(s) and compatibility.json:")
    for path in changed_paths:
        print(f"  {path}")
    print("review with: git diff --submodule=log")
    print("then stage the changed component path(s) and compatibility.json explicitly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
