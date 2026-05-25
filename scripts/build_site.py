"""Tiny site validation/build helper.

The static site is committed directly. This script performs a conservative
presence check and creates a generated marker for CI-style smoke tests.
"""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    site = Path("site")
    required = [site / "index.html", site / "assets" / "styles.css", site / "assets" / "app.js"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"missing site files: {', '.join(missing)}")
    generated = site / "generated"
    generated.mkdir(exist_ok=True)
    (generated / "BUILD_OK.txt").write_text("SciTrace site assets validated.\n", encoding="utf-8")
    print("site assets validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
