#!/usr/bin/env python3
"""Exposure Scale in the terminal. Questions, plan and step help come from assets/content.json.

Usage: python3 scripts/exposure.py <command> [args]

  status              where things stand and what to do next
  level               where the answers place you on the five levels, the next level and the risks
  next                the current question
  answer Q CHOICE     answer question Q with option number(s), value(s) or "skip"; prints the next question
  answers             answers so far (change one by answering it again)
  plan                the plan, by effort
  step ID             how to do one step
  check ID            read-only check on this computer for one step
  detect              run every read-only check for this computer
  open ID [N]         open the step's settings page, or its Nth link
  done ID | todo ID | drop ID    mark a step done, put it back in the plan, or remove it
  reset --yes         delete saved answers

Answers are stored only in ~/.exposure-scale/state.json (set EXPOSURE_SCALE_HOME to change the folder).
Needs Python 3.8+ and nothing else. Makes no network requests.
"""
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CONTENT = json.loads((SKILL / "assets" / "content.json").read_text(encoding="utf-8"))
ASSIST = json.loads((SKILL / "assets" / "assist.json").read_text(encoding="utf-8"))
STEPS = CONTENT["steps"]
QUESTIONS = CONTENT["questions"]
LEVELS = CONTENT["levels"]
AROUND = CONTENT["around"]
PARTS = {p["id"]: p["name"] for p in CONTENT["parts"]}
STEP = {s["id"]: s for s in STEPS}
QUESTION = {q["id"]: q for q in QUESTIONS}
SCRIPT = "exposure.py"

OS = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}.get(platform.system(), "other")
OS_NAME = {"macos": "macOS", "windows": "Windows", "linux": "Linux", "other": "this system"}[OS]

# ===== state =====
HOME = Path(os.environ.get("EXPOSURE_SCALE_HOME") or Path.home() / ".exposure-scale")
STATE_FILE = HOME / "state.json"


def load():
    try:
        s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        s = {}
    return {"answers": s.get("answers", {}), "overrides": s.get("overrides", {}), "checks": s.get("checks", {})}


def save(state):
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(HOME), prefix=".state-")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"version": 1, **state}, f, indent=1, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, STATE_FILE)


# ===== logic (mirrors index.html; tools/compare_logic.mjs keeps them in step) =====
def options_of(q, a):
    """optionsFrom reuses the options picked in another question; the question's own options follow them."""
    if not q.get("optionsFrom"):
        return q["options"]
    sel = a.get(q["optionsFrom"])
    picked = []
    if isinstance(sel, list):
        picked = [{k: o[k] for k in ("value", "label", "level") if k in o}
                  for o in options_of(QUESTION[q["optionsFrom"]], a) if o["value"] in sel and not o.get("exclusive")]
    return picked + q.get("options", [])


def meets(c, a):
    """Conditions: {question, equals | notEquals | minCount} or {minLevel}. minCount ignores exclusive options such as "None"."""
    if not c:
        return True
    if "minLevel" in c:
        return placement(a)["reach"] >= c["minLevel"]
    v = a.get(c["question"])
    if "equals" in c:
        return v == c["equals"]
    if "notEquals" in c:
        return v != c["notEquals"]
    if "minCount" in c:
        if not isinstance(v, list):
            return False
        exclusive = {o["value"] for o in options_of(QUESTION[c["question"]], a) if o.get("exclusive")}
        return len([x for x in v if x not in exclusive]) >= c["minCount"]
    return True


def visible(a):
    return [q for q in QUESTIONS if meets(q.get("showIf"), a)]


def placement(a):
    """Options carry a level. "self" is the person's guess, "tried" the furthest thing done last month, "habit" what
    they do most weeks. Their level is the habit (or what they tried, until that's answered); reach is the furthest
    of both, and the risks of every level up to it apply."""
    def top(role):
        m = None
        for q in QUESTIONS:
            v = a.get(q["id"])
            if q.get("place") != role or v is None or v == "skip" or not meets(q.get("showIf"), a):
                continue
            sel = v if q.get("multi") else [v]
            for o in options_of(q, a):
                if o["value"] in sel and o.get("level") is not None:
                    m = max(m or 0, o["level"])
        return m
    tried, habit = top("tried"), top("habit")
    level = habit if habit is not None else tried
    return {"self": top("self"), "tried": tried, "habit": habit, "level": level, "reach": max(tried or 0, habit or 0)}


def level_no(p):
    return None if p["level"] is None else max(1, p["level"])  # "None of these" still sits on level 1


def placed(a):
    return level_no(placement(a)) is not None and not any(q.get("place") and q["id"] not in a for q in visible(a))


def level_steps(a):
    """The level adds the guardrails of every level up to your reach and the steps that get you to the next level."""
    p = placement(a)
    n = level_no(p)
    if n is None:
        return []
    out = [i for l in LEVELS if l["n"] <= p["reach"] for i in l["guards"]]
    return out + (LEVELS[n]["climb"] if n < len(LEVELS) else [])


def links_of(s, a):
    return [l for l in s.get("links", []) if meets(l.get("showIf"), a)]


def effects_of(q, ans, a):
    add, done = [], []
    if ans is None or ans == "skip":
        return add, done
    sel = ans if q.get("multi") else [ans]
    parts = [o for o in options_of(q, a) if o["value"] in sel] + [e for e in q.get("effects", []) if meets(e.get("if"), a)]
    for p in parts:
        add += p.get("add", [])
        done += p.get("done", [])
    return add, done


def status_map(state):
    a, st = state["answers"], {}
    for i in level_steps(a):
        if st.get(i) != "done":
            st[i] = "todo"
    for q in visible(a):
        add, done = effects_of(q, a.get(q["id"]), a)
        for i in add:
            if st.get(i) != "done":
                st[i] = "todo"
        for i in done:
            st[i] = "done"
    out = {}
    for s in STEPS:
        o = state["overrides"].get(s["id"])
        v = None if o == "off" else (o or st.get(s["id"]))
        if v:
            out[s["id"]] = v
    return out


def current(a):
    return next((q for q in visible(a) if q["id"] not in a), None)


# Lanes: steps that need someone else → With others; on your own, 10 min or less → Minutes, longer → An evening
LANES = [("minutes", "Minutes", "10 min or less, on your own"), ("evening", "An evening", "longer, on your own"), ("others", "With others", "needs family, your bank or a company")]


def lane(s):
    return "others" if s.get("withOthers") else "minutes" if s["minutes"] <= 10 else "evening"


def order(steps):
    rank = {k: i for i, (k, _, _) in enumerate(LANES)}
    return sorted(steps, key=lambda s: (rank[lane(s)], -s["impact"], s["minutes"]))


def fmt(m):
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h" + (f" {m % 60} min" if m % 60 else "")


def dots(n):
    return "●" * n + "○" * (3 - n)


def effort(s):
    return fmt(s["minutes"])


def ans_text(q, ans, a):
    if ans == "skip":
        return "Skipped"
    sel = ans if q.get("multi") else [ans]
    return ", ".join(o["label"] for o in options_of(q, a) if o["value"] in sel) or "—"


def help_kinds(sid):
    h = ASSIST.get(sid, {})
    kinds = []
    if any(sid in p["steps"] for p in available_probes()):
        kinds.append("check")
    if (h.get("open") or {}).get(OS) or STEP[sid].get("links"):
        kinds.append("open")
    if h.get("template"):
        kinds.append("draft")
    if h.get("review"):
        kinds.append("review")
    return kinds or ["guide"]


# ===== read-only checks on this computer =====
def read_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def probe_agents():
    """Which AI tools are installed and what they can reach. Prints names and modes only, never keys, tokens or env values."""
    h, lines, ev = Path.home(), [], []
    apps = []
    if OS == "macos":
        apps = [n for n in ["ChatGPT", "Claude", "Perplexity", "Copilot"] if (Path("/Applications") / f"{n}.app").exists()]
        ev.append("looked in /Applications")
    if apps:
        lines.append(f"Desktop apps: {', '.join(apps)}")
    claude = h / ".claude"
    if claude.is_dir():
        s = read_json(claude / "settings.json") or {}
        perm = s.get("permissions") or {}
        parts = [f"permission mode {perm.get('defaultMode', 'default')}", f"{len(perm.get('allow', []))} always-allowed rules"]
        if s.get("skipDangerousModePermissionPrompt"):
            parts.append("skip-permissions prompt dismissed")
        cfg = read_json(h / ".claude.json") or {}
        servers = sorted(cfg.get("mcpServers") or {})
        projects = sum(1 for v in (cfg.get("projects") or {}).values() if isinstance(v, dict) and v.get("mcpServers"))
        plugins = sorted(k for k, v in (s.get("enabledPlugins") or {}).items() if v)
        parts.append(f"connected tools: {', '.join(servers) if servers else 'none'}")
        if projects:
            parts.append(f"{projects} project(s) with their own connected tools")
        if plugins:
            parts.append(f"plugins: {', '.join(plugins)}")
        lines.append("Claude Code: " + "; ".join(parts))
        ev.append("read ~/.claude/settings.json and ~/.claude.json (names and modes only)")
    codex = h / ".codex" / "config.toml"
    if codex.exists():
        t = codex.read_text(encoding="utf-8", errors="ignore")
        top = t.split("\n[", 1)[0]
        mode = lambda k: (re.search(rf'^{k}\s*=\s*"([\w-]+)"', top, re.M) or [None, "default"])[1]
        servers = sorted(set(m.strip('"') for m in re.findall(r'^\[mcp_servers\.("?[^\]."]+"?)\]', t, re.M)))
        plugins = re.findall(r'^\[plugins\."([^"]+)"\]\s*\n\s*enabled\s*=\s*true', t, re.M)
        trusted = len(re.findall(r'^trust_level\s*=\s*"trusted"', t, re.M))
        lines.append(f"Codex: approval {mode('approval_policy')}; sandbox {mode('sandbox_mode')}; connected tools: {', '.join(servers) or 'none'}; "
                     f"{len(plugins)} plugins on; {trusted} trusted folder(s)")
        ev.append("read ~/.codex/config.toml (names and modes only)")
    for name, path in [("Gemini CLI", h / ".gemini" / "settings.json"), ("Cursor", h / ".cursor" / "mcp.json")]:
        if path.parent.is_dir():
            d = read_json(path) or {}
            servers = sorted(d.get("mcpServers") or {})
            lines.append(f"{name}: connected tools: {', '.join(servers) or 'none'}")
            ev.append(f"read ~/{path.relative_to(h).as_posix()} if present (names only)")
    if not lines:
        return "none", "No AI agent tools found in the usual places.", ev
    return "found", "\n".join(lines), ev


PROBES = [
    {"id": "agents", "label": "AI tools and what they can reach", "os": ["macos", "windows", "linux"], "fn": probe_agents,
     "steps": ["agent_inventory", "agent_confirm", "agent_revoke", "vet_skills"], "questions": ["did", "ai_assistants", "ai_reach", "approvals"]},
]


def available_probes():
    return [p for p in PROBES if OS in p["os"]]


def run_probe(p, state):
    result, summary, evidence = p["fn"]()
    state["checks"][p["id"]] = {"result": result, "summary": summary, "at": time.strftime("%Y-%m-%d")}
    return result, summary, evidence


# ===== output =====
def status_line(state):
    a, st = state["answers"], status_map(state)
    v = visible(a)
    todo = [s for s in STEPS if st.get(s["id"]) == "todo"]
    base = sum(s["minutes"] for s in todo if s["tier"] == 1)
    q = current(a)
    lv = level_no(placement(a)) if placed(a) else None
    parts = [f"Questions {len([x for x in v if x['id'] in a])}/{len(v)}",
             f"level {lv} ({LEVELS[lv - 1]['name']})" if lv else None,
             f"plan: {len(todo)} to do, {list(st.values()).count('done')} in place",
             f"{fmt(base)} to baseline" if base else "baseline reached" if not q and st else None]
    if q:
        nxt = f"ask the user, then {SCRIPT} answer {q['id']} <choice>"
    elif todo:
        s = order(todo)[0]
        nxt = f"{SCRIPT} step {s['id']} ({s['title']})"
    else:
        nxt = "nothing left. Plan complete." if st else f"{SCRIPT} next"
    return "── " + " · ".join(p for p in parts if p) + f"\n── Next: {nxt}"


def show_question(q, state):
    a, v = state["answers"], visible(state["answers"])
    opts = options_of(q, a)
    print(f"Question {v.index(q) + 1} of {len(v)} · {PARTS[q['part']]} · id: {q['id']}")
    print(q["text"])
    if q.get("hint"):
        print(q["hint"])
    for i, o in enumerate(opts, 1):
        print(f"  {i}. {o['label']}" + (f" ({o['detail']})" if o.get("detail") else ""))
    for p in available_probes():
        c = state["checks"].get(p["id"])
        if q["id"] in p["questions"] and c:
            print(f"Detected on this computer ({p['label']}): {c['summary']}")
    how = "one or more, comma-separated" if q.get("multi") else "one"
    print(f"Answer ({how}): {SCRIPT} answer {q['id']} <number or value> · or: {SCRIPT} answer {q['id']} skip")


def guess_note(p):
    n, t = level_no(p), []
    if p["self"] is not None:
        t.append("Same as your guess." if p["self"] == n else f"You guessed {p['self']}.")
    if (p["tried"] or 0) > n:
        t.append(f"You’ve tried {p['tried']}.")
    return " ".join(t)


def cmd_level(state, args):
    a, st = state["answers"], status_map(state)
    if not placed(a):
        print(f"Not placed yet. The first questions do that: {SCRIPT} next")
        print(status_line(state))
        return
    p = placement(a)
    n = level_no(p)
    print(f"Level {n} of 5 · {LEVELS[n - 1]['name']}. {LEVELS[n - 1]['line']} {guess_note(p)}".rstrip())
    print()
    for l in LEVELS:
        mark = "→" if l["n"] == n else "✓" if l["n"] < n else "·" if l["n"] <= p["reach"] else " "
        print(f"  {mark} {l['n']} {l['name']:<10} {l['line']}")
    print("  (→ your level, ✓ below it, · tried)")
    mark = lambda i: "[x]" if st.get(i) == "done" else "[ ]"
    if n < len(LEVELS):
        nx = LEVELS[n]
        print(f"\nNEXT: {nx['n']} · {nx['name']}. {nx['up']}")
        for i in nx["climb"]:
            if st.get(i):
                print(f"  {mark(i)} {i:<24} {STEP[i]['title']} · {effort(STEP[i])}")
        if nx["n"] > p["reach"]:
            print(f"  What comes with it: {nx['risk']}")
    else:
        print("\nTop of the scale. Nothing left to hand over; the guardrails below keep it safe.")
    print("\nRISKS UP TO YOUR LEVEL (each level adds its own)")
    rows = [(f"{l['n']} · {l['name']}", l["risk"], l["n"]) for l in reversed(LEVELS) if l["n"] <= p["reach"]]
    for name, risk, lv in rows + [(AROUND["name"], AROUND["risk"], 0)]:
        its = [s for s in STEPS if s["level"] == lv and not s.get("up") and st.get(s["id"])]
        done = sum(1 for s in its if st[s["id"]] == "done")
        print(f"{name}: {risk}" + (f" ({done}/{len(its)} in place)" if its else ""))
        for s in its:
            print(f"  {mark(s['id'])} {s['id']:<24} {s['title']}")
    print("\nThe levels follow research on AI autonomy; which risks sit at which level is a reading of the evidence, not a measurement.")
    print(status_line(state))


def cmd_status(state, args):
    a = state["answers"]
    if not a and not state["overrides"]:
        print("No answers yet. The check takes about three minutes; answers stay on this computer.")
    print(status_line(state))


def cmd_next(state, args):
    q = current(state["answers"])
    if q:
        show_question(q, state)
    else:
        print(f"Every question is answered. See the plan: {SCRIPT} plan")
    print(status_line(state))


def parse_choice(q, raw, a):
    opts = options_of(q, a)
    if raw.strip().lower() == "skip":
        return "skip"
    picks = [p for p in re.split(r"[,\s]+", raw.strip()) if p]
    values = []
    for p in picks:
        if p.isdigit() and 1 <= int(p) <= len(opts):
            values.append(opts[int(p) - 1]["value"])
        elif any(o["value"] == p for o in opts):
            values.append(p)
        else:
            choices = ", ".join(f"{i}={o['value']}" for i, o in enumerate(opts, 1))
            sys.exit(f"'{p}' isn't an option for {q['id']}. Options: {choices}, or skip.")
    values = list(dict.fromkeys(values))
    if not values:
        sys.exit("Give at least one option, or skip.")
    if not q.get("multi"):
        if len(values) > 1:
            sys.exit(f"{q['id']} takes one answer.")
        return values[0]
    exclusive = [o["value"] for o in opts if o.get("exclusive")]
    if any(v in exclusive for v in values) and len(values) > 1:
        sys.exit("'None' can't be combined with other options.")
    return values


def cmd_answer(state, args):
    if len(args) < 2:
        sys.exit(f"Usage: {SCRIPT} answer QUESTION CHOICE")
    a = state["answers"]
    q = QUESTION.get(args[0])
    if not q or q not in visible(a):
        sys.exit(f"'{args[0]}' isn't an open question. Open: {', '.join(x['id'] for x in visible(a))}")
    a[q["id"]] = parse_choice(q, " ".join(args[1:]), a)
    # drop answers to questions whose options came from this one, if that choice is gone
    for x in QUESTIONS:
        if x.get("optionsFrom") == q["id"] and x["id"] in a and a[x["id"]] != "skip" and not any(o["value"] == a[x["id"]] for o in options_of(x, a)):
            del a[x["id"]]
    save(state)
    st = status_map(state)
    print(f"Recorded · {q['label']}: {ans_text(q, a[q['id']], a)}")
    sel = a[q["id"]] if q.get("multi") else [a[q["id"]]]
    notes = [o["note"] for o in options_of(q, a) if o["value"] in sel and o.get("note")]
    if q.get("place") and a[q["id"]] != "skip" and placed(a):
        p = placement(a)
        n = level_no(p)
        print(f"Level {n} · {LEVELS[n - 1]['name']}. {LEVELS[n - 1]['line']} {guess_note(p)}".rstrip())
        print(f"The full picture: {SCRIPT} level")
    elif q.get("place") == "self" and a[q["id"]] != "skip":
        print("Noted. Now what you actually do.")
    elif q.get("place") and notes:
        print(" ".join(notes))
    elif a[q["id"]] != "skip" and not q.get("place"):
        if notes:
            print(" ".join(notes))
        add, done = effects_of(q, a[q["id"]], a)
        add = [i for i in dict.fromkeys(add) if st.get(i) == "todo"]
        done = list(dict.fromkeys(done))
        eff = []
        if add:
            eff.append(f"+{len(add)} to do · {fmt(sum(STEP[i]['minutes'] for i in add))}")
        if done:
            eff.append(f"✓ {len(done)} in place")
        print("Effect: " + (" · ".join(eff) or "no change"))
    print()
    cmd_next(state, [])


def cmd_answers(state, args):
    a = state["answers"]
    shown = [q for q in visible(a) if q["id"] in a]
    if not shown:
        print("No answers yet.")
    for q in shown:
        print(f"  {q['id']:<20} {q['label']}: {ans_text(q, a[q['id']], a)}")
    print(f"Change one: {SCRIPT} answer <id> <choice>")
    print(status_line(state))


def cmd_plan(state, args):
    st = status_map(state)
    if not st:
        print(f"The plan fills in as you answer. Start: {SCRIPT} next")
        return
    todo = [s for s in STEPS if st.get(s["id"]) == "todo"]
    done = [s for s in STEPS if st.get(s["id"]) == "done"]
    base = [s for s in todo if s["tier"] == 1]
    total = fmt(sum(s["minutes"] for s in todo))
    if base:
        print(f"{fmt(sum(s['minutes'] for s in base))} to baseline · {len(base)} baseline {'step' if len(base) == 1 else 'steps'} left · everything: {total} across {len(todo)} steps")
    else:
        print(f"Baseline reached · {len(todo)} further steps, about {total}")
    print(f"{len(done)} in place · {len(todo)} to do")
    if placed(state["answers"]):
        n = level_no(placement(state["answers"]))
        print(f"Level {n} · {LEVELS[n - 1]['name']} (details: {SCRIPT} level)")
    for key, name, desc in LANES:
        items = order([s for s in todo if lane(s) == key])
        print(f"\n{name.upper()} ({desc}) · {len(items)} {'step' if len(items) == 1 else 'steps'}")
        for s in items:
            tags = [effort(s), f"impact {dots(s['impact'])}"] + (["baseline"] if s["tier"] == 1 else []) + (["level up"] if s.get("up") else [])
            print(f"  [ ] {s['id']:<24} {s['title']} · {' · '.join(tags)} · help: {'/'.join(help_kinds(s['id']))}")
        if not items:
            print("  Nothing here.")
    if done:
        print(f"\nIn place ({len(done)}): " + "; ".join(s["title"] for s in done))
    print(status_line(state))


def get_step(args):
    if not args or args[0] not in STEP:
        sys.exit(f"Unknown step '{args[0] if args else ''}'. Step ids are listed by: {SCRIPT} plan")
    return STEP[args[0]]


def cmd_step(state, args):
    s = get_step(args)
    a, st, h = state["answers"], status_map(state), ASSIST.get(args[0], {})
    status = {"todo": "in plan", "done": "done"}.get(st.get(s["id"]), "not in plan")
    print(f"Step: {s['id']} · {s['title']}")
    print(f"{effort(s)} · impact {dots(s['impact'])} ({s['impact']} of 3)" + (" · baseline" if s["tier"] == 1 else "")
          + (f" · gets them to level {s['level']}" if s.get("up") else "") + f" · status: {status}")
    if h.get("how"):
        print(f"How: {h['how']}")
    for p, name in (("ios", "iPhone"), ("android", "Android")):
        if (h.get("phone") or {}).get(p):
            print(f"{name}: {h['phone'][p]}")
    if (h.get("computer") or {}).get(OS):
        print(f"On this computer ({OS_NAME}): {h['computer'][OS]}")
    links = links_of(s, a)
    for i, l in enumerate(links, 1):
        print(f"Link {i}: {l['label']} · {l['url']}")
    if (h.get("open") or {}).get(OS) or links:
        print(f"Open it: {SCRIPT} open {s['id']}" + (" [link number]" if len(links) > 1 else ""))
    for p in available_probes():
        if s["id"] in p["steps"]:
            print(f"Check this computer: {SCRIPT} check {s['id']} ({p['label']})")
    if h.get("template"):
        print(f"Draft from: {h['template']} (fill it in with the user, save it where they choose, never send it)")
    if h.get("review"):
        print(f"Review: {h['review']}")
    print(f"When it's done: {SCRIPT} done {s['id']}")
    print(status_line(state))


def cmd_check(state, args):
    s = get_step(args)
    probes = [p for p in available_probes() if s["id"] in p["steps"]]
    if not probes:
        print(f"No check for this step on {OS_NAME}. Ask the user, then: {SCRIPT} done {s['id']}")
        return
    for p in probes:
        result, summary, evidence = run_probe(p, state)
        print(f"{p['label']}: {result}")
        print(summary)
        for e in evidence:
            print(f"  ran: {e}")
    save(state)
    print("This covers this computer only. Confirm with the user before marking the step done.")
    print(status_line(state))


def cmd_detect(state, args):
    for p in available_probes():
        result, summary, evidence = run_probe(p, state)
        print(f"{p['label']}: {result}")
        for line in summary.splitlines():
            print(f"  {line}")
    save(state)
    print("\nNothing was changed. Findings show next to the matching questions; the user still answers them.")
    print(status_line(state))


def cmd_open(state, args):
    s = get_step(args)
    h = ASSIST.get(s["id"], {})
    links = links_of(s, state["answers"])
    pick = args[1] if len(args) > 1 else None
    if pick and pick.isdigit() and 1 <= int(pick) <= len(links):
        target = links[int(pick) - 1]["url"]
    else:
        target = (h.get("open") or {}).get(OS) or (links[0]["url"] if links else None)
    if not target:
        sys.exit(f"Nothing to open for {s['id']}.")
    if OS == "windows":
        os.startfile(target)  # noqa: works for URLs and ms-settings: pages
    else:
        opener = "open" if OS == "macos" else "xdg-open"
        if not shutil.which(opener):
            sys.exit(f"Can't open pages here. Give the user this link: {target}")
        subprocess.run([opener, target], check=False)
    print(f"Opened: {target}")
    print(f"Once the user has changed the setting: {SCRIPT} done {s['id']}")


def set_override(state, sid, value, msg):
    state["overrides"][sid] = value
    save(state)
    print(msg)
    print(status_line(state))


def cmd_done(state, args):
    s = get_step(args)
    set_override(state, s["id"], "done", f"Done: {s['title']}")


def cmd_todo(state, args):
    s = get_step(args)
    set_override(state, s["id"], "todo", f"In plan: {s['title']}")


def cmd_drop(state, args):
    s = get_step(args)
    set_override(state, s["id"], "off", f"Removed from plan: {s['title']}")


def cmd_reset(state, args):
    if "--yes" not in args:
        sys.exit(f"This deletes all saved answers in {STATE_FILE}. Run: {SCRIPT} reset --yes")
    try:
        STATE_FILE.unlink()
    except FileNotFoundError:
        pass
    print("Saved answers deleted.")


def cmd_validate(state, args):
    """For maintainers: check assist.json, probes, templates and SKILL.md against content.json."""
    problems = []
    for sid, h in ASSIST.items():
        if sid not in STEP:
            problems.append(f"assist.json: unknown step {sid}")
        if h.get("template") and not (SKILL / h["template"]).exists():
            problems.append(f"assist.json: {sid} template {h['template']} missing")
    # the website marks these steps "Agent helps"; the skill must offer more than a how-to line
    for s in STEPS:
        if s.get("agentHelp") and help_kinds(s["id"]) in (["guide"], ["open"]):
            problems.append(f"content.json: {s['id']} has agentHelp but the skill has no check, template or review for it")
    for l in LEVELS:
        problems += [f"content.json: level {l['n']} lists unknown step {i}" for i in l["guards"] + l["climb"] if i not in STEP]
        problems += [f"content.json: level {l['n']} climbs with {i}, which isn't a level-{l['n']} up step" for i in l["climb"]
                     if i in STEP and not (STEP[i].get("up") and STEP[i]["level"] == l["n"])]
    for p in PROBES:
        problems += [f"probe {p['id']}: unknown step {i}" for i in p["steps"] if i not in STEP]
        problems += [f"probe {p['id']}: unknown question {i}" for i in p["questions"] if i not in QUESTION]
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    front = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", m.group(1), re.M)) if m else {}
    name, desc = front.get("name", ""), front.get("description", "")
    if name != SKILL.name or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        problems.append(f"SKILL.md: name '{name}' must match the folder and use a-z, 0-9 and single hyphens")
    if not 0 < len(desc) <= 1024:
        problems.append(f"SKILL.md: description is {len(desc)} characters (1–1024)")
    if len(text.splitlines()) > 500:
        problems.append("SKILL.md: over 500 lines")
    print("\n".join(problems) or "Skill OK.")
    sys.exit(1 if problems else 0)


COMMANDS = {"status": cmd_status, "level": cmd_level, "next": cmd_next, "answer": cmd_answer, "answers": cmd_answers, "plan": cmd_plan,
            "step": cmd_step, "check": cmd_check, "detect": cmd_detect, "open": cmd_open, "done": cmd_done,
            "todo": cmd_todo, "drop": cmd_drop, "reset": cmd_reset, "validate": cmd_validate}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__.strip())
        sys.exit(0 if len(sys.argv) < 2 else 2)
    COMMANDS[sys.argv[1]](load(), sys.argv[2:])


if __name__ == "__main__":
    main()
