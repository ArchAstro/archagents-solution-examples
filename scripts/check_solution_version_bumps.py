#!/usr/bin/env python3
"""
Fail a PR if any solution directory has content changes without a
corresponding version bump in solutions/<slug>/sample.yaml.

Why this exists:
  release.yml only cuts a new GitHub Release tarball when it sees a
  <slug>-<version> release that does not already exist. Editing files in a
  solution without bumping sample.yaml's version is a silent publishing
  no-op: CI validates the bytes, but release.yml skips the already-released
  version.

Logic:
  - Diff solutions/** against the PR base ref.
  - Group changed paths by solutions/<slug>.
  - For each slug where sample.yaml exists on both sides, fail if the
    version: field is identical between base and HEAD.
  - Skip slugs where sample.yaml is new or deleted.

Usage:
    python3 scripts/check_solution_version_bumps.py [BASE_REF]

BASE_REF defaults to origin/main. CI passes origin/${{ github.base_ref }}.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOLUTIONS_ROOT = "solutions"
SAMPLE_FILENAME = "sample.yaml"
VERSION_RE = re.compile(r'^version:\s*["\']?(v\d+\.\d+\.\d+)["\']?\s*(?:#.*)?$')


def verify_ref(ref: str, repo_root: pathlib.Path = REPO_ROOT) -> None:
    """
    Confirm ref resolves to a commit and is not flag-shaped.

    This prevents a user-controlled base ref from being interpreted as a
    git flag if this script is run outside the intended GitHub Actions path.
    """
    if ref.startswith("-"):
        raise ValueError(
            f"Refusing to use ref {ref!r}: looks like a flag, not a revision."
        )
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        raise ValueError(
            f"Could not resolve {ref!r} to a commit. "
            "In CI this is typically origin/${{ github.base_ref }}; "
            "ensure actions/checkout ran with fetch-depth: 0."
        )


def changed_solution_paths(
    base_ref: str, repo_root: pathlib.Path = REPO_ROOT
) -> list[str]:
    """Return changed paths under solutions/."""
    out = subprocess.check_output(
        ["git", "diff", "--name-only", base_ref, "HEAD", "--", SOLUTIONS_ROOT],
        cwd=repo_root,
    ).decode()
    return [line for line in out.splitlines() if line.startswith(f"{SOLUTIONS_ROOT}/")]


def solution_slugs_for_paths(paths: list[str]) -> list[str]:
    """Return sorted unique solution slugs from diff paths."""
    slugs: set[str] = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == SOLUTIONS_ROOT and parts[1]:
            slugs.add(parts[1])
    return sorted(slugs)


def _parse_version(text: str) -> Optional[str]:
    for line in text.splitlines():
        match = VERSION_RE.match(line.strip())
        if match:
            return match.group(1)
    return None


def version_at(
    ref: str, path: str, repo_root: pathlib.Path = REPO_ROOT
) -> Optional[str]:
    """Return path's sample.yaml version at ref, or None if missing/unparseable."""
    try:
        text = subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
        ).decode()
    except subprocess.CalledProcessError:
        return None
    return _parse_version(text)


def find_unbumped_solutions(
    base_ref: str, repo_root: pathlib.Path = REPO_ROOT
) -> list[tuple[str, str]]:
    """Return (slug, version) pairs for touched solutions without version bumps."""
    paths = changed_solution_paths(base_ref, repo_root)
    unbumped: list[tuple[str, str]] = []
    for slug in solution_slugs_for_paths(paths):
        sample_path = f"{SOLUTIONS_ROOT}/{slug}/{SAMPLE_FILENAME}"
        base_version = version_at(base_ref, sample_path, repo_root)
        head_version = version_at("HEAD", sample_path, repo_root)
        if base_version is None or head_version is None:
            continue
        if base_version == head_version:
            unbumped.append((slug, head_version))
    return unbumped


def main() -> int:
    base_ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"

    try:
        verify_ref(base_ref)
    except ValueError as exc:
        print(f"check_solution_version_bumps: {exc}", file=sys.stderr)
        return 2

    unbumped = find_unbumped_solutions(base_ref)
    changed_slugs = solution_slugs_for_paths(changed_solution_paths(base_ref))

    if not unbumped:
        if changed_slugs:
            print(f"OK: all {len(changed_slugs)} touched solution(s) have version bumps.")
        else:
            print("No solution directories touched.")
        return 0

    print("Version-bump check FAILED:", file=sys.stderr)
    print("", file=sys.stderr)
    for slug, version in unbumped:
        print(
            f"  solutions/{slug}: files changed but sample.yaml version is "
            f"unchanged at {version}.\n"
            f"    Bump version: in solutions/{slug}/sample.yaml so release.yml\n"
            f"    cuts a new tarball with your changes. Keep\n"
            f"    solution.yaml solution_version in sync; validation will fail if\n"
            f"    those two fields differ.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
