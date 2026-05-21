#!/usr/bin/env python3
"""Build aggregate clubs.config.json from split per-club source files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path(__file__).parent / "clubs" / "manifest.json"
DEFAULT_OUTPUT = Path(__file__).parent / "clubs.config.json"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    clubs = manifest.get("clubs")
    if not isinstance(clubs, list):
        raise ValueError("Manifest must contain a 'clubs' list")

    return manifest


def build_clubs_payload(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(manifest_path)
    manifest_dir = manifest_path.parent

    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    for entry in manifest.get("clubs", []):
        if not isinstance(entry, dict):
            raise ValueError("Each manifest club entry must be an object")

        if entry.get("enabled", True) is False:
            continue

        short_name = str(entry.get("shortName", "")).strip()
        rel_path = str(entry.get("path", "")).strip()
        if not short_name or not rel_path:
            raise ValueError("Each manifest entry must include shortName and path")

        if short_name in seen:
            raise ValueError(f"Duplicate shortName in manifest: {short_name}")
        seen.add(short_name)

        club_file = (manifest_dir / rel_path).resolve()
        if not club_file.exists():
            raise FileNotFoundError(f"Club file not found for {short_name}: {club_file}")

        club = _load_json(club_file)
        if not isinstance(club, dict):
            raise ValueError(f"Club file must contain a JSON object: {club_file}")

        file_short = str(club.get("shortName", "")).strip()
        if file_short and file_short != short_name:
            raise ValueError(
                f"shortName mismatch for {short_name}: manifest={short_name}, file={file_short}"
            )

        club["shortName"] = short_name
        result.append(club)

    result.sort(key=lambda item: str(item.get("shortName", "")))
    return result


def run_check(manifest_path: Path) -> int:
    clubs = build_clubs_payload(manifest_path)
    print(f"OK: {len(clubs)} clubs validated from {manifest_path}")
    return 0


def run_build(manifest_path: Path, output_path: Path) -> int:
    clubs = build_clubs_payload(manifest_path)
    payload = {"clubs": clubs}
    _write_json(output_path, payload)
    print(f"Wrote {len(clubs)} clubs to {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build backend/clubs.config.json from backend/clubs/manifest.json"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Validate only")
    args = parser.parse_args()

    try:
        if args.check:
            return run_check(args.manifest)
        return run_build(args.manifest, args.output)
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
