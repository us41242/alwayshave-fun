"""
build_index_html.py — server-render the homepage trail grid into index.html.

The homepage grid was JS-only: Googlebot crawled index.html (the one page it
reliably visits) and saw zero trail links, so it never discovered the 40+ trail
pages. This bakes real <a href> cards (grouped by state, sorted by score, same
markup the JS produces) between the GRID:START / GRID:END markers so a single
homepage crawl discovers every trail. JS still hydrates over it on load.

Runs every 30 min in the pipeline so baked scores stay fresh (hard rule 4).
"""

import json
import glob
import re
import html as html_lib

INDEX_PATH = "index.html"
DATA_DIR = "data/conditions"

STATE_NAMES = {
    "NV": "Nevada", "UT": "Utah", "AZ": "Arizona",
    "CO": "Colorado", "CA": "California", "NM": "New Mexico",
}
DIFF_CLASS = {"easy": "diff-easy", "moderate": "diff-moderate",
              "hard": "diff-hard", "expert": "diff-expert"}


def score_color(s):
    if s >= 85: return "#16a34a"
    if s >= 70: return "#65a30d"
    if s >= 50: return "#d97706"
    if s >= 30: return "#ea580c"
    return "#dc2626"


def esc(v):
    return html_lib.escape(str(v or ""))


def card_html(d):
    state = (d.get("state") or "").upper()
    slug = d.get("slug") or ""
    href = f"/{state.lower()}/{esc(slug)}"
    score = d.get("score")
    label = d.get("score_label") or ""
    color = score_color(score) if isinstance(score, (int, float)) else "#888"
    diff = d.get("difficulty") or ""
    dog_ok = (d.get("dog_friendly") or "").lower() == "yes"
    dog = ('<span class="card-sep">·</span>'
           '<span class="card-dog" title="Dogs welcome on this trail">🐕 Dogs OK</span>'
           ) if dog_ok else ""
    park = (f'<div class="card-park">{esc(d.get("park_name"))}</div>'
            if d.get("park_name") else "")
    badge = (f'<div class="card-score-badge" style="color:{color};border-color:{color}">'
             f'<span class="snum">{esc(score)}</span><span class="sdenom">/100</span></div>')
    return f'''
        <a class="trail-card" href="{href}" style="--score-color:{color}">
          <div class="card-photo state-{esc(state)}" id="photo-{esc(slug)}">
            <div class="card-photo-overlay"></div>
            {badge}
            <div class="card-photo-label">
              <div class="card-name">{esc(d.get("name"))}</div>
              {park}
            </div>
          </div>
          <div class="card-body">
            <span class="{DIFF_CLASS.get(diff.lower(), "")}">{esc(diff)}</span>
            <span class="card-sep">·</span>
            <span>{esc(d.get("length_mi"))} mi</span>
            <span class="card-sep">·</span>
            <span>{esc(state)}</span>
            {dog}
            <span class="card-sep">·</span>
            <div class="card-conditions"><span class="score-label-text" style="color:{color}">{esc(label)}</span></div>
          </div>
        </a>'''


def build_grid():
    trails = []
    for path in glob.glob(f"{DATA_DIR}/*.json"):
        with open(path, encoding="utf-8") as f:
            trails.append(json.load(f))
    # Group by state, states alphabetical, trails by score desc (mirrors JS).
    states = sorted({(t.get("state") or "").upper() for t in trails})
    html = ""
    for state in states:
        group = sorted(
            (t for t in trails if (t.get("state") or "").upper() == state),
            key=lambda t: t.get("score") if isinstance(t.get("score"), (int, float)) else -1,
            reverse=True,
        )
        if not group:
            continue
        n = len(group)
        html += (f'\n      <div class="region-heading">{STATE_NAMES.get(state, state)} '
                 f'— {n} trail{"s" if n != 1 else ""}</div>\n')
        html += '      <div class="trail-grid">'
        html += "".join(card_html(t) for t in group)
        html += "\n      </div>"
    return html, len(trails)


def main():
    grid, n = build_grid()
    with open(INDEX_PATH, encoding="utf-8") as f:
        page = f.read()
    new_block = f"<!-- GRID:START (server-rendered by scripts/build_index_html.py; JS hydrates over it) -->{grid}\n      <!-- GRID:END -->"
    new_page, count = re.subn(
        r"<!-- GRID:START.*?GRID:END -->",
        lambda _m: new_block,  # lambda avoids backreference interpretation in replacement
        page,
        flags=re.DOTALL,
    )
    if count != 1:
        raise SystemExit(f"expected exactly 1 GRID marker block, found {count}")
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_page)
    print(f"index.html — homepage grid rendered, {n} trails")


if __name__ == "__main__":
    main()
