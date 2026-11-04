"""Package debugging files with portable names before Actions artifact upload."""

import hashlib
import json
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

VOLUMES = Path(__file__).resolve().parents[1] / "app" / "volumes"


def portable_part(part: str) -> str:
    cleaned = re.sub(r'[<>:"\\|?*\x00-\x1f]', "_", part).rstrip(" .")
    if cleaned != part or len(cleaned) > 120:
        digest = hashlib.sha256(part.encode("utf-8")).hexdigest()[:12]
        return f"{cleaned[:100] or 'file'}-{digest}"
    return cleaned


def main() -> None:
    sources = (VOLUMES / "runtime", VOLUMES / "hcaptcha" / ".challenge")
    files = sorted(
        path
        for source in sources
        if source.exists()
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    if not files:
        print("No runtime files to package")
        return

    destination = VOLUMES / "artifacts" / "epic-runtime.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    names = {}
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            original = path.relative_to(VOLUMES)
            portable = "/".join(portable_part(part) for part in original.parts)
            archive.write(path, portable)
            if portable != original.as_posix():
                names[portable] = original.as_posix()
        archive.writestr("original-paths.json", json.dumps(names, ensure_ascii=False, indent=2))
    print(f"Packaged {len(files)} runtime files: {destination.name}")


if __name__ == "__main__":
    main()
