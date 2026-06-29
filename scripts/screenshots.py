"""Generate window screenshots of the demo report for README."""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "examples" / "demo_generator" / "demo-report.html"
OUT_DIR = ROOT / "docs" / "images"
VIEWS = [
    ("dashboard", "Dashboard"),
    ("features", "Features"),
    ("rules", "Rules"),
    ("scenarios", "Scenarios"),
    ("results", "Results"),
    ("tags", "Tags"),
    ("statistics", "Statistics"),
    ("environment", "Environment"),
]


def main() -> int:
    if not REPORT.exists():
        print(f"Report not found: {REPORT}")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(REPORT.as_uri())
        page.wait_for_load_state("networkidle")
        # Give charts a moment to render
        page.wait_for_timeout(500)

        for route, _label in VIEWS:
            button = page.locator(f".nav-item[data-route='{route}']")
            if button.count():
                button.click()
                page.wait_for_timeout(400)
            # Scroll to top so the sidebar and topbar are always visible
            page.evaluate("window.scrollTo(0, 0)")
            path = OUT_DIR / f"{route}.png"
            page.screenshot(path=path)
            print(f"Wrote {path}")

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
