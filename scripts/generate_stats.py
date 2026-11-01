#!/usr/bin/env python3
import json, os, time, urllib.request
from collections import defaultdict
from html import escape
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "lokesh15kl")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = Path("assets")
OUT.mkdir(exist_ok=True)

BG, TEXT, MUTED = "#1b1b2a", "#e6edf3", "#9aa4b2"
BLUE, PURPLE, CYAN, BORDER = "#70a5ff", "#c792ea", "#20c9b5", "#39394d"

def api_get(url):
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": f"{USERNAME}-profile-analytics",
               "X-GitHub-Api-Version": "2022-11-28"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def all_repos():
    repos, page = [], 1
    while True:
        batch = api_get(f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(0.15)
    return repos

def card(title, subtitle, body, width=760, height=220):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#6d28d9"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="15" fill="{BG}" stroke="{BORDER}"/>
<rect x="1" y="1" width="{width-2}" height="7" rx="4" fill="url(#accent)"/>
<text x="30" y="47" fill="{TEXT}" font-family="Arial,sans-serif" font-size="23" font-weight="700">{escape(title)}</text>
<text x="30" y="72" fill="{MUTED}" font-family="Arial,sans-serif" font-size="12">{escape(subtitle)}</text>
{body}</svg>'''

def stat(x, value, label, color):
    return (f'<text x="{x}" y="139" text-anchor="middle" fill="{color}" font-family="Arial,sans-serif" font-size="36" font-weight="700">{value}</text>'
            f'<text x="{x}" y="169" text-anchor="middle" fill="{MUTED}" font-family="Arial,sans-serif" font-size="14">{escape(label)}</text>')

def make_stats(user, repos):
    owned = [r for r in repos if not r.get("fork", False)]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    forks = sum(r.get("forks_count", 0) for r in owned)
    body = stat(145, len(owned), "Public repositories", BLUE)
    body += f'<line x1="285" y1="105" x2="285" y2="180" stroke="{BORDER}" stroke-width="2"/>'
    body += stat(380, stars, "Total stars", PURPLE)
    body += f'<line x1="475" y1="105" x2="475" y2="180" stroke="{BORDER}" stroke-width="2"/>'
    body += stat(615, forks, "Total forks", CYAN)
    subtitle = f"GitHub profile analytics for @{USERNAME}  |  {user.get('followers', 0)} followers"
    (OUT / "github-stats.svg").write_text(card("GitHub Statistics", subtitle, body), encoding="utf-8")

def make_languages(repos):
    totals = defaultdict(int)
    for repo in repos:
        if repo.get("fork", False) or not repo.get("languages_url"):
            continue
        try:
            languages = api_get(repo["languages_url"])
        except Exception as exc:
            print(f"Skipping language data for {repo.get('name')}: {exc}")
            continue
        for lang, size in languages.items():
            totals[lang] += size
        time.sleep(0.12)

    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:6]
    total = sum(totals.values())
    if not ranked or not total:
        body = f'<text x="30" y="135" fill="{MUTED}" font-family="Arial,sans-serif" font-size="15">No public language data found.</text>'
    else:
        colors = ["#3572A5", "#f1e05a", "#e34c26", "#563d7c", "#2b7489", "#00ADD8"]
        x, y, bar_width = 30.0, 105, 700.0
        body = ""
        for (lang, amount), color in zip(ranked, colors):
            segment = bar_width * amount / total
            body += f'<rect x="{x:.1f}" y="{y}" width="{segment:.1f}" height="13" fill="{color}"/>'
            x += segment
        for i, ((lang, amount), color) in enumerate(zip(ranked, colors)):
            col, row = i % 3, i // 3
            lx, ly = 35 + col * 240, 151 + row * 35
            body += f'<circle cx="{lx}" cy="{ly-5}" r="5" fill="{color}"/>'
            body += f'<text x="{lx+13}" y="{ly}" fill="{TEXT}" font-family="Arial,sans-serif" font-size="13">{escape(lang)}</text>'
            body += f'<text x="{lx+205}" y="{ly}" text-anchor="end" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">{amount/total*100:.1f}%</text>'
    subtitle = "Based on byte counts across your non-fork public repositories"
    (OUT / "top-languages.svg").write_text(card("Most Used Languages", subtitle, body), encoding="utf-8")

def main():
    user = api_get(f"https://api.github.com/users/{USERNAME}")
    repos = all_repos()
    make_stats(user, repos)
    make_languages(repos)
    print(f"Generated analytics for @{USERNAME}; checked {len(repos)} public repositories.")

if __name__ == "__main__":
    main()
