#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "DominikTroendle")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "languages.svg")
TOP_N = 5
EXCLUDE = {s.strip().lower() for s in os.environ.get("EXCLUDE_LANGS", "").split(",") if s.strip()}

ACCENT = "#3dcfb6"
COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26",
    "CSS": "#663399", "SCSS": "#c6538c", "Python": "#3572A5", "Shell": "#89e051",
    "Java": "#b07219", "C#": "#178600", "PHP": "#4F5D95", "Vue": "#41b883",
    "Dockerfile": "#384d54", "PowerShell": "#012456", "Go": "#00ADD8",
}
FALLBACK = "#8b949e"


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    totals = {}
    page = 1
    while True:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            for lang, size in api(repo["languages_url"]).items():
                if lang.lower() in EXCLUDE:
                    continue
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(totals):
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    total = sum(v for _, v in items) or 1
    W, H = 440, 150
    bar_x, bar_w, bar_y, bar_h = 20, W - 40, 50, 8

    segs, x = [], bar_x
    for i, (lang, size) in enumerate(items):
        w = bar_w * size / total
        segs.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="{bar_h}" fill="{COLORS.get(lang, FALLBACK)}"/>')
        x += w

    legend = []
    for i, (lang, size) in enumerate(items):
        col, row = i % 2, i // 2
        lx, ly = 20 + col * 210, 88 + row * 26
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{COLORS.get(lang, FALLBACK)}"/>'
            f'<text class="t" x="{lx + 18}" y="{ly}">{escape(lang)} {100 * size / total:.1f}%</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Most used languages">
<title>Most used languages</title>
<style>
  .bg{{fill:#0d1117}} .t{{font:400 14px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:#e6edf3}}
  .h{{font:700 17px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:{ACCENT}}}
  @media (prefers-color-scheme: light){{.bg{{fill:#ffffff}} .t{{fill:#1f2328}}}}
</style>
<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="4"/></clipPath>
<rect class="bg" x="1" y="1" width="{W - 2}" height="{H - 2}" rx="6" stroke="{ACCENT}" stroke-width="1.5"/>
<text class="h" x="20" y="32">Most Used Languages</text>
<g clip-path="url(#bar)">{"".join(segs)}</g>
{"".join(legend)}
</svg>
'''


if __name__ == "__main__":
    try:
        data = collect()
    except Exception as e:  # kein leeres Bild veroeffentlichen
        print(f"Fehler beim Abruf: {e}", file=sys.stderr)
        sys.exit(1)
    if not data:
        print("Keine Sprachdaten gefunden.", file=sys.stderr)
        sys.exit(1)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(render(data))
    print("geschrieben:", OUT)
