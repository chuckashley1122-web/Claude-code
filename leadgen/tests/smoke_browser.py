"""Browser-path smoke test. Run: python tests/smoke_browser.py"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from leadgen.browser import proxy, chromium_path

from playwright.sync_api import sync_playwright

launch = {"args": ["--no-sandbox"]}
if chromium_path():
    launch["executable_path"] = chromium_path()
if proxy():
    launch["proxy"] = {"server": proxy()}
print("launch kwargs:", {k: v for k, v in launch.items()})

with sync_playwright() as p:
    b = p.chromium.launch(**launch)
    pg = b.new_page()
    pg.goto("https://github.com/D4Vinci/Scrapling", wait_until="domcontentloaded", timeout=45000)
    print("BROWSER OK title =", pg.title()[:80])
    b.close()
