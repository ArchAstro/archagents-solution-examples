#!/usr/bin/env python3
"""
Unit tests for scripts/check_solution_version_bumps.py.

Each test builds a temporary git repo with a base commit and a head commit,
then checks whether changed solution directories require a sample.yaml
version bump.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = SCRIPTS_DIR / "check_solution_version_bumps.py"

_spec = importlib.util.spec_from_file_location("version_bump_check", SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
sys.modules["version_bump_check"] = mod
_spec.loader.exec_module(mod)


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        stderr=subprocess.STDOUT,
    ).decode()


def _init_repo() -> Path:
    repo = Path(tempfile.mkdtemp())
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "solutions").mkdir()
    return repo


def _write_solution(
    repo: Path,
    slug: str,
    version: str,
    extra_files: dict[str, str] | None = None,
) -> None:
    solution_dir = repo / "solutions" / slug
    solution_dir.mkdir(exist_ok=True)
    (solution_dir / "sample.yaml").write_text(
        textwrap.dedent(
            f"""\
            schema_version: 2
            version: {version}
            name: "Test {slug}"
            tagline: "Test solution {slug}"
            min_cli_version: "0.28.0"
            steps:
              - type: deploy_solution
                solution_file: solution.yaml
            """
        )
    )
    (solution_dir / "solution.yaml").write_text(
        textwrap.dedent(
            f"""\
            kind: Solution
            lookup_key: {slug}-solution
            solution_id: 00000000-0000-4000-8000-000000000000
            solution_version: {version}
            name: "Test {slug}"
            description: "Test solution {slug}"
            category_keys: [sample]
            tag_keys: [test]
            templates: []
            """
        )
    )
    for name, content in (extra_files or {}).items():
        path = solution_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)


class FindUnbumpedSolutionsTest(unittest.TestCase):
    def test_no_solution_changes_returns_empty(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0")
        _commit(repo, "initial")
        (repo / "README.md").write_text("hello")
        _commit(repo, "docs only")

        self.assertEqual(mod.find_unbumped_solutions("HEAD~1", repo), [])

    def test_solution_changed_without_version_bump_is_flagged(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0", {"agents/alpha.yaml": "name: alpha\n"})
        _commit(repo, "initial")
        (repo / "solutions" / "alpha" / "agents" / "alpha.yaml").write_text(
            "name: edited\n"
        )
        _commit(repo, "edit solution")

        self.assertEqual(
            mod.find_unbumped_solutions("HEAD~1", repo),
            [("alpha", "v0.1.0")],
        )

    def test_solution_changed_with_version_bump_is_clean(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0", {"agents/alpha.yaml": "name: alpha\n"})
        _commit(repo, "initial")
        _write_solution(repo, "alpha", "v0.1.1", {"agents/alpha.yaml": "name: edited\n"})
        _commit(repo, "bump and edit")

        self.assertEqual(mod.find_unbumped_solutions("HEAD~1", repo), [])

    def test_sample_yaml_changed_without_version_bump_is_flagged(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0")
        _commit(repo, "initial")
        sample = repo / "solutions" / "alpha" / "sample.yaml"
        sample.write_text(sample.read_text().replace("Test solution alpha", "Updated"))
        _commit(repo, "edit tagline only")

        self.assertEqual(
            mod.find_unbumped_solutions("HEAD~1", repo),
            [("alpha", "v0.1.0")],
        )

    def test_new_solution_is_skipped(self) -> None:
        repo = _init_repo()
        (repo / ".gitkeep").write_text("")
        _commit(repo, "initial empty")
        _write_solution(repo, "newcomer", "v0.1.0")
        _commit(repo, "add solution")

        self.assertEqual(mod.find_unbumped_solutions("HEAD~1", repo), [])

    def test_deleted_solution_is_skipped(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "departing", "v0.1.0")
        _commit(repo, "initial")
        _git(repo, "rm", "-qr", "solutions/departing")
        _commit(repo, "remove solution")

        self.assertEqual(mod.find_unbumped_solutions("HEAD~1", repo), [])

    def test_multiple_solutions_only_reports_unbumped_ones(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0", {"agents/alpha.yaml": "a\n"})
        _write_solution(repo, "beta", "v0.2.0", {"agents/beta.yaml": "b\n"})
        _commit(repo, "initial")
        _write_solution(repo, "alpha", "v0.1.1", {"agents/alpha.yaml": "a-edit\n"})
        (repo / "solutions" / "beta" / "agents" / "beta.yaml").write_text("b-edit\n")
        _commit(repo, "alpha bumped beta forgot")

        self.assertEqual(
            mod.find_unbumped_solutions("HEAD~1", repo),
            [("beta", "v0.2.0")],
        )

    def test_nested_file_change_without_bump_is_flagged(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0", {"scripts/tool.aascript": "one\n"})
        _commit(repo, "initial")
        (repo / "solutions" / "alpha" / "scripts" / "tool.aascript").write_text("two\n")
        _commit(repo, "edit nested")

        self.assertEqual(
            mod.find_unbumped_solutions("HEAD~1", repo),
            [("alpha", "v0.1.0")],
        )


class VerifyRefTest(unittest.TestCase):
    def test_accepts_valid_ref(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0")
        _commit(repo, "initial")

        mod.verify_ref("HEAD", repo)

    def test_rejects_flag_shaped_ref(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0")
        _commit(repo, "initial")

        with self.assertRaises(ValueError):
            mod.verify_ref("--exec=evil", repo)

    def test_rejects_unknown_ref(self) -> None:
        repo = _init_repo()
        _write_solution(repo, "alpha", "v0.1.0")
        _commit(repo, "initial")

        with self.assertRaises(ValueError):
            mod.verify_ref("origin/no-such-branch", repo)


if __name__ == "__main__":
    unittest.main()
