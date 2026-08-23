from __future__ import annotations

import configparser
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import update_component


class UpdateComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.root_patch = mock.patch.object(update_component, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temporary.cleanup)

        self.component_path = self.root / "components" / "windows-lead"
        self.component_path.mkdir(parents=True)
        (self.component_path / ".git").write_text("gitdir: placeholder\n", encoding="utf-8")
        self.manifest = {
            "components": {
                "windows_lead": {
                    "path": "components/windows-lead",
                    "branch": "main",
                    "commit": "a" * 40,
                }
            }
        }
        self.modules = configparser.ConfigParser()
        self.modules.add_section('submodule "components/windows-lead"')
        self.modules.set(
            'submodule "components/windows-lead"',
            "path",
            "components/windows-lead",
        )

    def test_preflight_fetches_into_remote_tracking_ref(self) -> None:
        calls: list[tuple[tuple[str, ...], Path]] = []

        def fake_git(*arguments: str, cwd: Path = self.root) -> str:
            calls.append((arguments, cwd))
            if arguments[:2] == ("status", "--porcelain"):
                return ""
            if arguments[0] == "fetch":
                return ""
            if arguments == ("rev-parse", "HEAD"):
                return "a" * 40
            if arguments == ("rev-parse", "refs/remotes/origin/main"):
                return "b" * 40
            if arguments[:2] == ("rev-list", "--count"):
                return "0"
            self.fail(f"unexpected git call: {arguments}")

        with mock.patch.object(update_component, "run_git", side_effect=fake_git):
            plan = update_component.preflight_component(
                "windows-lead",
                self.manifest,
                self.modules,
            )

        self.assertEqual(plan.remote_commit, "b" * 40)
        self.assertIn(
            (
                (
                    "fetch",
                    "--prune",
                    "origin",
                    "+refs/heads/main:refs/remotes/origin/main",
                ),
                self.component_path,
            ),
            calls,
        )

    def test_manifest_cannot_redirect_checkout_outside_components(self) -> None:
        self.manifest["components"]["windows_lead"]["path"] = "../outside"
        with mock.patch.object(update_component, "run_git") as run_git:
            with self.assertRaisesRegex(update_component.UpdateError, "must be exactly"):
                update_component.preflight_component(
                    "windows-lead",
                    self.manifest,
                    self.modules,
                )
        run_git.assert_not_called()

    def test_all_preflights_complete_before_any_checkout(self) -> None:
        first = update_component.UpdatePlan(
            label="windows-lead",
            key="windows_lead",
            path=self.component_path,
            relative_path="components/windows-lead",
            current_commit="a" * 40,
            remote_commit="b" * 40,
        )
        with mock.patch.object(
            update_component,
            "preflight_component",
            side_effect=[first, update_component.UpdateError("second component failed")],
        ), mock.patch.object(update_component, "apply_plans") as apply_plans:
            with self.assertRaisesRegex(update_component.UpdateError, "second component failed"):
                plans = [
                    update_component.preflight_component(label, {}, self.modules)
                    for label in ("windows-lead", "mac-runner")
                ]
                update_component.apply_plans(plans, {})
        apply_plans.assert_not_called()


if __name__ == "__main__":
    unittest.main()
