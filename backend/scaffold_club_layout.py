#!/usr/bin/env python3
"""Scaffold split club source layout from aggregate clubs.config.json."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).parent
REPO_DIR = BACKEND_DIR.parent
DEFAULT_CONFIG = BACKEND_DIR / "clubs.config.json"
DEFAULT_CLUBS_DIR = BACKEND_DIR / "clubs"
DEFAULT_MANIFEST = DEFAULT_CLUBS_DIR / "manifest.json"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _ensure_gitkeep(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")


def _copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists() or not source.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def _copy_member_photos(short_name: str, club_dir: Path) -> int:
    source_dir = REPO_DIR / "ID_photos" / short_name
    target_dir = club_dir / "member_id_photos"
    if not source_dir.exists() or not source_dir.is_dir():
        return 0

    count = 0
    for source in source_dir.iterdir():
        if source.is_file():
            shutil.copy2(source, target_dir / source.name)
            count += 1
    return count


def scaffold(
    config_path: Path,
    clubs_dir: Path,
    manifest_path: Path,
    force: bool,
    copy_logos: bool,
    copy_backgrounds: bool,
    copy_member_photos: bool,
) -> tuple[int, int, int]:
    payload = _load_json(config_path)
    clubs = payload.get("clubs", []) if isinstance(payload, dict) else []

    manifest_entries: list[dict[str, Any]] = []
    logos_copied = 0
    backgrounds_copied = 0
    photos_copied = 0

    for club in clubs:
        if not isinstance(club, dict):
            continue

        short_name = str(club.get("shortName", "")).strip()
        if not short_name:
            continue

        club_dir = clubs_dir / short_name
        assets_dir = club_dir / "assets"
        imports_beats = club_dir / "imports" / "beats"
        imports_members = club_dir / "imports" / "members"
        photos_dir = club_dir / "member_id_photos"
        club_file = club_dir / "club.json"

        assets_dir.mkdir(parents=True, exist_ok=True)
        _ensure_gitkeep(imports_beats)
        _ensure_gitkeep(imports_members)
        _ensure_gitkeep(photos_dir)

        if force or not club_file.exists():
            _write_json(club_file, club)
        else:
            print(f"Skipped existing {club_file} (use --force to overwrite)")

        if copy_logos:
            source_logo = BACKEND_DIR / "club_logos" / f"{short_name}.png"
            target_logo = assets_dir / "logo.png"
            if _copy_if_exists(source_logo, target_logo):
                logos_copied += 1

        if copy_backgrounds:
            source_background = BACKEND_DIR / "club_logos" / f"{short_name}_background.png"
            target_background = assets_dir / "background.png"
            if _copy_if_exists(source_background, target_background):
                backgrounds_copied += 1

        if copy_member_photos:
            photos_copied += _copy_member_photos(short_name, club_dir)

        manifest_entries.append(
            {
                "shortName": short_name,
                "path": f"{short_name}/club.json",
                "enabled": True,
            }
        )

    manifest_entries.sort(key=lambda item: item["shortName"])
    manifest_payload = {
        "version": 1,
        "description": "Club source manifest for generating backend/clubs.config.json",
        "clubs": manifest_entries,
    }
    _write_json(manifest_path, manifest_payload)

    return logos_copied, backgrounds_copied, photos_copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold backend/clubs from clubs.config.json")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--clubs-dir", type=Path, default=DEFAULT_CLUBS_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--copy-logos", action="store_true")
    parser.add_argument("--copy-backgrounds", action="store_true")
    parser.add_argument("--copy-member-photos", action="store_true")
    args = parser.parse_args()

    logos_copied, backgrounds_copied, photos_copied = scaffold(
        config_path=args.config,
        clubs_dir=args.clubs_dir,
        manifest_path=args.manifest,
        force=args.force,
        copy_logos=args.copy_logos,
        copy_backgrounds=args.copy_backgrounds,
        copy_member_photos=args.copy_member_photos,
    )

    manifest_resolved = args.manifest.resolve()
    clubs_resolved = args.clubs_dir.resolve()
    clubs_count = len(_load_json(args.manifest).get("clubs", []))

    print(f"Scaffolded {clubs_count} clubs under {clubs_resolved}")
    print(f"Manifest: {manifest_resolved}")
    if args.copy_logos:
        print(f"Copied logos: {logos_copied}")
    if args.copy_backgrounds:
        print(f"Copied backgrounds: {backgrounds_copied}")
    if args.copy_member_photos:
        print(f"Copied member photos: {photos_copied}")
    print("Next: run backend/build_clubs_config.py --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
