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
steps = {s["id"] for s in content["steps"]}
areas = {a["id"] for a in content["areas"]}
questions = {q["id"]: q for q in content["questions"]}
problems = []

# references
for s in content["steps"]:
    if s["area"] not in areas:
        problems.append(f"step {s['id']}: unknown area {s['area']}")
    for l in s.get("links", []):
        cond = l.get("showIf")
        if cond and cond["question"] not in questions:
            problems.append(f"step {s['id']}: link condition on unknown question {cond['question']}")
for q in content["questions"]:
    for part in q.get("options", []) + q.get("effects", []):
        for sid in part.get("add", []) + part.get("done", []):
            if sid not in steps:
                problems.append(f"question {q['id']}: unknown step {sid}")
    for cond in [q.get("showIf")] + [e.get("if") for e in q.get("effects", [])]:
        if cond and cond["question"] not in questions:
            problems.append(f"question {q['id']}: condition on unknown question {cond['question']}")
    if q.get("optionsFrom") and q["optionsFrom"] not in questions:
        problems.append(f"question {q['id']}: options from unknown question {q['optionsFrom']}")

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
