"""Check content.json: every id it references exists, the skill's copy matches, and every link responds.

Run from the repo root:  python3 tools/check_content.py
Exits non-zero if a reference is broken or a link fails.
"""
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# These sites answer scripts with errors but work in a browser; check them by hand.
BLOCKS_SCRIPTS = {"consumer.ftc.gov", "www.facebook.com", "ico.org.uk"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"

content = json.load(open("content.json"))
steps = {s["id"]: s for s in content["steps"]}
levels = {l["n"] for l in content["levels"]}
parts = {p["id"] for p in content["parts"]}
questions = {q["id"]: q for q in content["questions"]}
sources = {s["id"] for s in content["sources"]}
problems = []

# references
for s in content["steps"]:
    if s["level"] not in levels | {0}:
        problems.append(f"step {s['id']}: unknown level {s['level']}")
    for l in s.get("links", []):
        cond = l.get("showIf")
        if cond and cond.get("question", "") not in questions and "minLevel" not in cond:
            problems.append(f"step {s['id']}: link condition on unknown question {cond.get('question')}")
for l in content["levels"]:
    for sid in l["guards"] + l["climb"]:
        if sid not in steps:
            problems.append(f"level {l['n']}: unknown step {sid}")
        elif steps[sid]["level"] != l["n"] or bool(steps[sid].get("up")) != (sid in l["climb"]):
            problems.append(f"level {l['n']}: step {sid} has level {steps[sid]['level']} and up={bool(steps[sid].get('up'))}")
for q in content["questions"]:
    if q.get("part") not in parts:
        problems.append(f"question {q['id']}: unknown part {q.get('part')}")
    for part in q.get("options", []) + q.get("effects", []):
        for sid in part.get("add", []) + part.get("done", []):
            if sid not in steps:
                problems.append(f"question {q['id']}: unknown step {sid}")
    for cond in [q.get("showIf")] + [e.get("if") for e in q.get("effects", [])]:
        if cond and "minLevel" not in cond and cond.get("question") not in questions:
            problems.append(f"question {q['id']}: condition on unknown question {cond.get('question')}")
        if cond and "minLevel" in cond and q.get("place"):
            problems.append(f"question {q['id']}: the level question can't depend on the level")
    if q.get("place") and (q.get("multi") or any("level" not in o for o in q.get("options", []))):
        problems.append(f"question {q['id']}: the level question takes one answer and every option needs a level")
    if "covers" in q and q["covers"] not in levels:
        problems.append(f"question {q['id']}: covers unknown level {q['covers']}")
    for o in q.get("options", []):
        if o.get("src") and o["src"] not in sources:
            problems.append(f"question {q['id']}: unknown source {o['src']}")
        if o.get("note") and any(c.isdigit() for c in o["note"]) and not o.get("src"):
            problems.append(f"question {q['id']}: the note on '{o['value']}' has a number but no source")

if sum(1 for q in content["questions"] if q.get("place")) != 1:
    problems.append("questions: exactly one question sets the level (place)")

# every guardrail can be counted: each essential step has an answer that marks it in place
marks_done = {sid for q in content["questions"] for o in q.get("options", []) for sid in o.get("done", [])}
for l in content["levels"]:
    if l.get("case") and l["case"].get("src") not in sources:
        problems.append(f"level {l['n']}: unknown source {l['case'].get('src')}")
    if l.get("echo") and l["echo"].get("question") not in questions:
        problems.append(f"level {l['n']}: echo of unknown question {l['echo'].get('question')}")
    essential = [sid for sid in l["guards"] if sid in steps and steps[sid]["tier"] == 1]
    if not essential:
        problems.append(f"level {l['n']}: no essential (tier 1) guardrail")
    for sid in essential:
        if sid not in marks_done:
            problems.append(f"level {l['n']}: no answer marks the essential step {sid} as in place")

# the skill ships its own copy of the content
SKILL_COPY = "skills/exposure-scale/assets/content.json"
if open(SKILL_COPY).read() != open("content.json").read():
    problems.append(f"{SKILL_COPY} differs from content.json. Run: cp content.json {SKILL_COPY}")
r = subprocess.run([sys.executable, "skills/exposure-scale/scripts/exposure.py", "validate"], capture_output=True, text=True)
if r.returncode:
    problems += [f"skill: {l}" for l in r.stdout.strip().splitlines()]

# links
urls = {}
for s in content["steps"]:
    for l in s.get("links", []):
        if "url" in l:
            urls.setdefault(l["url"], []).append(s["id"])
for l in content["sources"]:
    urls.setdefault(l["url"], []).append("sources")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return url, r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return url, e.code, e.geturl()
    except Exception as e:
        return url, None, type(e).__name__


with ThreadPoolExecutor(8) as ex:
    results = sorted(ex.map(fetch, urls), key=lambda r: (r[1] == 200, r[0]))

by_hand = []
for url, status, final in results:
    short = urllib.parse.urlsplit(final)._replace(query="", fragment="").geturl() if final else ""
    moved = f"  → {short}" if short and short.rstrip("/") != url.rstrip("/") else ""
    print(f"{status or 'ERR':>4}  {url}{moved}")
    if status != 200:
        if urllib.parse.urlsplit(url).hostname in BLOCKS_SCRIPTS:
            by_hand.append(url)
        else:
            problems.append(f"link {url} ({', '.join(urls[url])}): {status or final}")

if by_hand:
    print("\nBlocks scripts, open in a browser:\n" + "\n".join(by_hand))

print()
print("\n".join(problems) if problems else "All references and links OK.")
sys.exit(1 if problems else 0)
