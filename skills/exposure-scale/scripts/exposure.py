#!/usr/bin/env python3
"""Exposure Scale in the terminal. Questions, plan and step help come from assets/content.json.

Usage: python3 scripts/exposure.py <command> [args]

  status              where things stand and what to do next
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
STEP = {s["id"]: s for s in STEPS}
QUESTION = {q["id"]: q for q in QUESTIONS}
EMAIL = CONTENT["emailProviders"]
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
    if not q.get("optionsFrom"):
        return q["options"]
    sel = a.get(q["optionsFrom"])
    if not isinstance(sel, list):
        return []
    return [{"value": o["value"], "label": o["label"]} for o in options_of(QUESTION[q["optionsFrom"]], a) if o["value"] in sel]


def meets(c, a):
    """Conditions: {question, equals | notEquals | minCount}. minCount ignores exclusive options such as "None"."""
    if not c:
        return True
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


def main_email(a):
    m = a.get("email_accounts")
    return a.get("main_email") or (m[0] if isinstance(m, list) and len(m) == 1 else None)


def visible(a):
    return [q for q in QUESTIONS if meets(q.get("showIf"), a)]


def question_text(q, a):
    p = EMAIL.get(main_email(a)) or {}
    return q["text"].replace("{mainEmail}", p.get("name", "your main email"), 1)


def links_of(s, a):
    out = []
    for l in s.get("links", []):
        if "emailProvider" in l:
            link = (EMAIL.get(main_email(a)) or {}).get(l["emailProvider"])
            if link:
                out.append(link)
        elif meets(l.get("showIf"), a):
            out.append(l)
    return out


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


# Effort lanes: 10 min or less → Minutes, up to 60 → An evening, longer or with an effortLabel → Bigger
LANES = [("minutes", "Minutes", "10 min or less each"), ("evening", "An evening", "up to an hour"), ("bigger", "Bigger", "purchases, calls or ongoing")]


def lane(s):
    return "bigger" if s.get("effortLabel") or s["minutes"] > 60 else "minutes" if s["minutes"] <= 10 else "evening"


def order(steps):
    rank = {k: i for i, (k, _, _) in enumerate(LANES)}
    return sorted(steps, key=lambda s: (rank[lane(s)], -s["impact"], s["minutes"]))


def fmt(m):
    if m < 60:
        return f"{m} min"
    return f"{m // 60} h" + (f" {m % 60} min" if m % 60 else "")


def kind(s):
    return "Cyber + AI" if len(s["kind"]) > 1 else "AI" if s["kind"][0] == "ai" else "Cyber"


def dots(n):
    return "●" * n + "○" * (3 - n)


def effort(s):
    return s.get("effortLabel") or fmt(s["minutes"])


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
def run(cmd, timeout=10):
    """Run a read-only command. Returns combined output, or None if it can't run."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    # macOS tools prefix stderr lines with a timestamp and process name
    return "\n".join(re.sub(r"^\d{4}-\d\d-\d\d [\d:.]+ \w+\[\d+:\d+\] ", "", l) for l in lines).strip()


def defaults_read(domain, key):
    out = run(["defaults", "read", domain, key])
    return None if out is None or "does not exist" in out else out.strip()


def probe_password_manager():
    names = ["1Password", "Bitwarden", "KeePassXC", "Dashlane", "Proton Pass", "Enpass", "NordPass", "LastPass", "Keeper"]
    if OS == "macos":
        dirs = [Path("/Applications"), Path.home() / "Applications"]
        where = "Applications folders"
    elif OS == "windows":
        dirs = [Path(os.environ.get(v, "")) for v in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA") if os.environ.get(v)]
        dirs += [d / "Programs" for d in dirs]
        where = "Program Files and AppData"
    else:
        found = [n for n in ["bitwarden", "keepassxc", "1password", "proton-pass", "enpass"] if shutil.which(n)]
        return ("found" if found else "none"), (f"Found: {', '.join(found)}" if found else "No password manager app found on PATH."), ["which bitwarden keepassxc 1password proton-pass enpass"]
    found = []
    for d in dirs:
        try:
            entries = [e.name for e in d.iterdir()]
        except OSError:
            continue
        found += [n for n in names if any(e.lower().startswith(n.lower()) for e in entries) and n not in found]
    if found:
        return "found", f"Found: {', '.join(found)}.", [f"looked in {where}"]
    return "none", "No password manager app found. A browser, phone or extension manager may still be in use.", [f"looked in {where}"]


def probe_auto_updates():
    if OS == "macos":
        keys = ["AutomaticallyInstallMacOSUpdates", "CriticalUpdateInstall"]
        vals = {k: defaults_read("/Library/Preferences/com.apple.SoftwareUpdate", k) for k in keys}
        ev = [f"defaults read /Library/Preferences/com.apple.SoftwareUpdate {k} → {v or 'not set'}" for k, v in vals.items()]
        if vals["AutomaticallyInstallMacOSUpdates"] == "1":
            return "on", "This Mac installs macOS updates automatically.", ev
        if vals["AutomaticallyInstallMacOSUpdates"] == "0":
            return "off", "This Mac does not install macOS updates automatically.", ev
        return "unknown", "Couldn't read the setting.", ev
    if OS == "windows":
        out = run(["reg", "query", r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", "/v", "NoAutoUpdate"])
        ev = [f"reg query ...\\WindowsUpdate\\AU /v NoAutoUpdate → {out or 'not set'}"]
        if out and re.search(r"NoAutoUpdate\s+REG_DWORD\s+0x1", out):
            return "off", "A policy turns automatic updates off.", ev
        return "on", "No policy blocks automatic updates (Windows default is on).", ev
    conf = Path("/etc/apt/apt.conf.d/20auto-upgrades")
    if conf.exists():
        on = re.search(r'Unattended-Upgrade\s+"1"', conf.read_text(errors="ignore"))
        return ("on" if on else "off"), ("Unattended upgrades are on." if on else "Unattended upgrades are off."), [f"read {conf}"]
    out = run(["systemctl", "is-enabled", "dnf-automatic-install.timer"]) or run(["systemctl", "is-enabled", "dnf-automatic.timer"])
    if out:
        return ("on" if out.startswith("enabled") else "off"), f"dnf-automatic timer: {out}", ["systemctl is-enabled dnf-automatic*.timer"]
    return "unknown", "No unattended-upgrades or dnf-automatic setup found.", [f"checked {conf} and dnf-automatic timers"]


def probe_screen_lock():
    if OS == "macos":
        out = run(["sysadminctl", "-screenLock", "status"])
        ev = [f"sysadminctl -screenLock status → {out or 'no output'}"]
        if not out:
            return "unknown", "Couldn't read the setting.", ev
        if "off" in out:
            return "off", "This Mac doesn't ask for a password after sleep or the screen saver.", ev
        m = re.search(r"delay is (\w+(?: seconds)?)", out)
        delay = m.group(1) if m else "unknown"
        return "on", f"This Mac asks for a password after sleep or the screen saver (delay: {delay}).", ev
    out = run(["gsettings", "get", "org.gnome.desktop.screensaver", "lock-enabled"])
    ev = [f"gsettings get org.gnome.desktop.screensaver lock-enabled → {out or 'not available'}"]
    if out in ("true", "false"):
        return ("on" if out == "true" else "off"), f"GNOME screen lock is {'on' if out == 'true' else 'off'}.", ev
    return "unknown", "Couldn't read the setting.", ev


def probe_lockdown_mode():
    v = defaults_read(".GlobalPreferences", "LDMGlobalEnabled")
    ev = [f"defaults read .GlobalPreferences LDMGlobalEnabled → {v or 'not set'}"]
    return ("on", "Lockdown Mode is on.", ev) if v == "1" else ("off", "Lockdown Mode is off on this Mac.", ev)


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
    {"id": "password_manager", "label": "Password manager", "os": ["macos", "windows", "linux"], "fn": probe_password_manager,
     "steps": ["password_manager"], "questions": ["passwords"]},
    {"id": "auto_updates", "label": "Automatic updates (this computer)", "os": ["macos", "windows", "linux"], "fn": probe_auto_updates,
     "steps": ["auto_updates"], "questions": ["updates"]},
    {"id": "screen_lock", "label": "Screen lock (this computer)", "os": ["macos", "linux"], "fn": probe_screen_lock,
     "steps": ["screen_lock"], "questions": []},
    {"id": "lockdown_mode", "label": "Lockdown Mode (this Mac)", "os": ["macos"], "fn": probe_lockdown_mode,
     "steps": ["lockdown_mode"], "questions": []},
    {"id": "agents", "label": "AI tools and what they can reach", "os": ["macos", "windows", "linux"], "fn": probe_agents,
     "steps": ["agent_inventory", "agent_confirm", "agent_revoke"], "questions": ["ai_assistants", "ai_agents"]},
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
    parts = [f"Questions {len([x for x in v if x['id'] in a])}/{len(v)}",
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
    print(f"Question {v.index(q) + 1} of {len(v)} · id: {q['id']}")
    print(question_text(q, a))
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
        if x.get("optionsFrom") == q["id"] and x["id"] in a and not (isinstance(a[q["id"]], list) and a[x["id"]] in a[q["id"]]):
            del a[x["id"]]
    save(state)
    st = status_map(state)
    print(f"Recorded · {q['label']}: {ans_text(q, a[q['id']], a)}")
    if a[q["id"]] != "skip":
        sel = a[q["id"]] if q.get("multi") else [a[q["id"]]]
        notes = [o["note"] for o in options_of(q, a) if o["value"] in sel and o.get("note")]
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
    for key, name, desc in LANES:
        items = order([s for s in todo if lane(s) == key])
        print(f"\n{name.upper()} ({desc}) · {len(items)} {'step' if len(items) == 1 else 'steps'}")
        for s in items:
            tags = [effort(s), f"impact {dots(s['impact'])}", kind(s)] + (["baseline"] if s["tier"] == 1 else [])
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
    print(f"{effort(s)} · impact {dots(s['impact'])} ({s['impact']} of 3) · {kind(s)}" + (" · baseline" if s["tier"] == 1 else "") + f" · status: {status}")
    if h.get("how"):
        print(f"How: {h['how']}")
    phone = a.get("phone")
    for p in (["ios", "android"] if phone == "both" else [phone]):
        if (h.get("phone") or {}).get(p):
            print(f"On your {'iPhone' if p == 'ios' else 'Android phone'}: {h['phone'][p]}")
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


COMMANDS = {"status": cmd_status, "next": cmd_next, "answer": cmd_answer, "answers": cmd_answers, "plan": cmd_plan,
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
