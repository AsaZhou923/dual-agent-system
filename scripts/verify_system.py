#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPATIBILITY_PATH = ROOT / "compatibility.json"
DEPENDENCIES_PATH = ROOT / "dependencies.lock.json"
SYSTEM_SCHEMA_PATH = ROOT / "contracts" / "mac-job-v1-system.schema.json"


class VerificationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VerificationError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def run_git(*arguments: str, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise VerificationError(completed.stderr.strip() or f"git {' '.join(arguments)} failed")
    return completed.stdout.strip()


def staged_gitlink(path: str) -> str:
    output = run_git("ls-files", "--stage", "--", path)
    if not output:
        raise VerificationError(f"missing gitlink for {path}")
    fields = output.split(maxsplit=3)
    if len(fields) != 4 or fields[0] != "160000" or not re.fullmatch(r"[0-9a-f]{40}", fields[1]):
        raise VerificationError(f"{path} is not a valid staged submodule gitlink")
    return fields[1]


def component_gitlink(path: str, *, prefer_worktree: bool) -> str:
    component_path = ROOT / path
    if prefer_worktree and (component_path / ".git").exists():
        return run_git("rev-parse", "HEAD", cwd=component_path)
    return staged_gitlink(path)


def normalized_repository(value: str) -> str:
    return value.removesuffix(".git").rstrip("/")


def verify_metadata(*, prefer_worktree_gitlinks: bool = False) -> dict[str, Any]:
    compatibility = load_json(COMPATIBILITY_PATH)
    dependencies = load_json(DEPENDENCIES_PATH)
    load_json(SYSTEM_SCHEMA_PATH)

    if compatibility.get("schema") != "dual-agent-system/compatibility-v1":
        raise VerificationError("unsupported compatibility manifest schema")
    if compatibility.get("network_scope") != "intranet-only":
        raise VerificationError("network_scope must remain intranet-only")

    buzz = dependencies.get("buzz")
    if not isinstance(buzz, dict):
        raise VerificationError("dependencies.lock.json must define Buzz")
    for field in ("repository", "branch", "commit", "upstream_repository", "upstream_commit"):
        if not isinstance(buzz.get(field), str) or not buzz[field]:
            raise VerificationError(f"Buzz dependency field is required: {field}")
    for field in ("commit", "upstream_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", buzz[field]):
            raise VerificationError(f"Buzz {field} must be a full lowercase Git commit")
    if buzz.get("vendored") is not False:
        raise VerificationError("Buzz must remain an external non-vendored dependency")

    modules = configparser.ConfigParser()
    modules.read(ROOT / ".gitmodules", encoding="utf-8")
    components = compatibility.get("components")
    if not isinstance(components, dict) or set(components) != {"windows_lead", "mac_runner"}:
        raise VerificationError("compatibility manifest must pin exactly two components")

    for component in components.values():
        if not isinstance(component, dict):
            raise VerificationError("component entry must be an object")
        path = component.get("path")
        expected_commit = component.get("commit")
        repository = component.get("repository")
        if not all(isinstance(value, str) and value for value in (path, expected_commit, repository)):
            raise VerificationError("component path, commit, and repository are required")
        if component_gitlink(path, prefer_worktree=prefer_worktree_gitlinks) != expected_commit:
            raise VerificationError(f"{path} gitlink does not match compatibility.json")

        section = f'submodule "{path}"'
        if not modules.has_section(section):
            raise VerificationError(f".gitmodules is missing {section}")
        if modules.get(section, "path") != path:
            raise VerificationError(f".gitmodules path mismatch for {path}")
        if normalized_repository(modules.get(section, "url")) != normalized_repository(repository):
            raise VerificationError(f".gitmodules URL mismatch for {path}")

    readiness = compatibility.get("readiness", {})
    if readiness.get("job_contract") != "verified-policy-v2-component-intersection":
        raise VerificationError("job contract readiness must describe the policy-v2 component intersection")
    if readiness.get("write_mode") != "policy-v2-compatible-cutover-pending":
        raise VerificationError("write mode must remain behind the policy-v2 production cutover gate")
    if readiness.get("live_cross_machine") != "pending-policy-v2-retest":
        raise VerificationError("policy-v2 live cross-machine verification must remain pending")
    return compatibility


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def schema_enum(schema: dict[str, Any], field: str) -> set[Any] | None:
    value = schema.get("properties", {}).get(field, {}).get("enum")
    return set(value) if isinstance(value, list) else None


def schema_item_enum(schema: dict[str, Any], field: str) -> set[Any] | None:
    value = schema.get("properties", {}).get(field, {}).get("items", {}).get("enum")
    return set(value) if isinstance(value, list) else None


def verify_components(compatibility: dict[str, Any]) -> None:
    components = compatibility["components"]
    for component in components.values():
        path = ROOT / component["path"]
        if not (path / ".git").exists():
            raise VerificationError(f"submodule is not initialized: {path.relative_to(ROOT)}")
        actual_commit = run_git("rev-parse", "HEAD", cwd=path)
        if actual_commit != component["commit"]:
            raise VerificationError(f"checked-out commit mismatch for {path.relative_to(ROOT)}")
        if run_git("status", "--porcelain", cwd=path):
            raise VerificationError(f"submodule worktree is dirty: {path.relative_to(ROOT)}")

    windows_path = ROOT / components["windows_lead"]["path"]
    mac_path = ROOT / components["mac_runner"]["path"]
    windows = load_module("dual_agent_windows_lead_verify", windows_path / "windows_lead.py")
    mac = load_module("dual_agent_mac_runner_verify", mac_path / "runner.py")

    protocols = compatibility["protocols"]
    job_protocol = protocols["job"]
    system_schema = load_json(ROOT / job_protocol["system_profile"])
    windows_schema = load_json(ROOT / job_protocol["producer_schema"])
    mac_schema = load_json(ROOT / job_protocol["consumer_schema"])

    fixture_paths = job_protocol.get("fixtures")
    if not isinstance(fixture_paths, list) or not fixture_paths or not all(
        isinstance(path, str) and path for path in fixture_paths
    ):
        raise VerificationError("job protocol must define non-empty policy-v2 fixtures")

    fixture_profiles: set[str] = set()
    for fixture_path in fixture_paths:
        fixture = load_json(ROOT / fixture_path)
        if windows.validate_job(fixture) != fixture:
            raise VerificationError(
                f"Windows Lead normalized compatibility fixture unexpectedly: {fixture_path}"
            )
        mac.SimpleSchemaValidator(mac_schema).validate(fixture)
        mac.SimpleSchemaValidator(system_schema).validate(fixture)
        canonical, _wire = mac.normalize_job_payload(fixture)
        for field in (
            "policy_version",
            "permission_profile",
            "capabilities",
            "network",
            "verification_profiles",
        ):
            if canonical.get(field) != fixture.get(field):
                raise VerificationError(f"Mac Runner changed {field} in fixture: {fixture_path}")
        canonical_scope = canonical.get("scope", {})
        fixture_scope = fixture.get("scope", {})
        if canonical_scope.get("root") != fixture_scope.get("root") or canonical_scope.get(
            "paths", []
        ) != fixture_scope.get("paths", []):
            raise VerificationError(f"Mac Runner changed scope in fixture: {fixture_path}")
        if fixture.get("owner_approval") != canonical.get("owner_approval"):
            raise VerificationError(f"Mac Runner changed owner approval in fixture: {fixture_path}")
        if fixture.get("capabilities") == ["self-update-runner"]:
            expected_profile = getattr(mac, "SELF_UPDATE_TEST_PROFILE", None)
            if fixture.get("verification_profiles") != [expected_profile]:
                raise VerificationError(
                    f"self-update fixture does not use the Mac Runner reserved profile: {fixture_path}"
                )
        fixture_profiles.add(str(fixture["permission_profile"]))

    system_properties = set(system_schema["properties"])
    system_required = set(system_schema["required"])
    for name, schema in (("Windows Lead", windows_schema), ("Mac Runner", mac_schema)):
        properties = set(schema["properties"])
        required = set(schema["required"])
        if not system_properties <= properties:
            missing = sorted(system_properties - properties)
            raise VerificationError(f"{name} does not recognize system fields: {missing}")
        if not required <= system_required:
            missing = sorted(required - system_required)
            raise VerificationError(f"system profile omits fields required by {name}: {missing}")

    for field in (
        "schema",
        "task_type",
        "execution_route",
        "preferred_worker",
        "permission_profile",
    ):
        system_values = schema_enum(system_schema, field)
        if system_values is None:
            continue
        for name, schema in (("Windows Lead", windows_schema), ("Mac Runner", mac_schema)):
            component_values = schema_enum(schema, field)
            if component_values is not None and not system_values <= component_values:
                unsupported = sorted(system_values - component_values)
                raise VerificationError(f"{name} rejects {field} values: {unsupported}")

    system_profiles = schema_enum(system_schema, "permission_profile")
    declared_profiles = set(job_protocol.get("permission_profiles", []))
    if system_profiles != declared_profiles or fixture_profiles != system_profiles:
        raise VerificationError("system schema, compatibility manifest, and fixtures must cover the same profiles")

    system_capabilities = schema_item_enum(system_schema, "capabilities")
    declared_capabilities = set(job_protocol.get("operational_capabilities", []))
    if system_capabilities != declared_capabilities:
        raise VerificationError("system schema and compatibility manifest capability sets differ")
    for name, schema in (("Windows Lead", windows_schema), ("Mac Runner", mac_schema)):
        component_capabilities = schema_item_enum(schema, "capabilities")
        if component_capabilities is not None and not system_capabilities <= component_capabilities:
            unsupported = sorted(system_capabilities - component_capabilities)
            raise VerificationError(f"{name} rejects operational capabilities: {unsupported}")

    load_json(ROOT / protocols["result"]["producer_schema"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify pinned Dual Agent system metadata and contracts.")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="verify gitlinks and root metadata without initialized submodules",
    )
    arguments = parser.parse_args()
    try:
        compatibility = verify_metadata(prefer_worktree_gitlinks=not arguments.metadata_only)
        if not arguments.metadata_only:
            verify_components(compatibility)
    except (OSError, ValueError, VerificationError) as error:
        print(f"verification failed: {error}", file=sys.stderr)
        return 1
    scope = "metadata" if arguments.metadata_only else "metadata and initialized components"
    print(f"verified {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
