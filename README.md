# common-anti-bloat

A bloat guard for codebases that are still growing — **executable detectors, not principles**.

[中文](README.zh.md) · MIT · by [wind](https://github.com/wind-c)

---

## The idea

Most anti-bloat advice is a value system: *keep it simple, delete more, avoid premature
abstraction.* You already agree, and nothing changes — because agreement isn't actionable.

This skill takes the opposite shape. Every pattern comes with **a command you can run** and
**a number it should return**. You don't decide whether the codebase feels bloated; you run
the check and read the answer.

Three consequences fall out of that:

- **A detector that lies is worse than no detector.** It returns a number, and the number
  reads as evidence. So each signal names the language where its method breaks — and §0
  makes you calibrate before the first run.
- **Every threshold is a measurement, not a taste.** The numbers here come from two real
  projects (one Rust ~170k lines, one Python ~12k). Where a row was reasoned rather than
  measured, it says so.
- **Deleting is a first-class step.** Item 7 of the checklist asks what this change removes,
  and refusing to answer costs you a line in the commit message.

## What it catches

Ten signals, each with a detection command:

| | | |
|---|---|---|
| **A1** core depends on future-tier | **A2** config declares dead paths | **A3** prototype past its expiry |
| **A4** entry point as business logic | **A5** a package holding one file | **A6** abstraction with one implementation |
| **A7** documents that no longer hold | **A8** dependency for a one-liner | **A9** two copies of one fact |
| **A10** dead code that still passes CI | | |

Two of them are worth calling out, because they are the ones that rot a codebase silently
while the line count looks fine:

- **A9 — two copies of one fact.** Not bloat by size, bloat by *obligation*: every copy adds
  a maintenance duty nothing enforces. A comment saying *"keep this in sync with X"* is a bug
  report, not documentation.
- **A10 — dead code that still passes CI.** A green suite says nothing about code the suite
  never touches. Largely a dynamic-language problem: where the compiler resolves imports,
  run the compiler instead.

## How it triggers

Model-invoked. It fires on its own when you:

- worry aloud about bloat, rot, or a codebase turning into a mess
- are about to add **a package, a dependency, an abstraction, a config section, or a design doc**
- ask what a diff should have **deleted**

Or invoke it by name.

## Layout

```
SKILL.md                      always loaded — calibration table, 8 pre-flight gates, 7 audit steps
references/SIGNALS.md         on demand    — the ten signals in full, with evidence
scripts/dead-import-scan.py   when run     — A10 detector, exits 1 on a hit, drops into CI
```

The three tiers exist because two of the three ways you use this skill don't need the signal
write-ups: the pre-flight gates stand alone, and only a review or an audit reaches for
`references/`.

## Using it

**Before writing code** — eight binary gates; a "yes" means stop and fix, not stop and think.
The last one is the one people skip: *am I writing down a fact that already exists somewhere else?*

**Reviewing a diff** — same gates applied to the change; each "yes" is a finding to raise.

**Periodically** — seven audit steps, ending in a short ADR that records what was deleted.
The ADR is a mechanical receipt, not a design document.

**First, once per project** — read §0 and reset the thresholds for your language. A5, A8 and
A10 are wrong out of the box in some ecosystems: 500 lines means different things in Java and
Python, npm's micro-package culture makes A8 bite far harder than Maven's, and A10 barely
exists where `cargo check` or `tsc --noEmit` already runs.

## Install

Tell your code agent to install this skill:

> Install the common-anti-bloat skill from https://github.com/wind-c/anti-bloat-skills

Or do it by hand:

**CLAUDE.md (per-project)**

```bash
# new project
curl -o CLAUDE.md https://raw.githubusercontent.com/wind-c/anti-bloat-skills/main/CLAUDE.md

# existing project (append)
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/wind-c/anti-bloat-skills/main/CLAUDE.md >> CLAUDE.md
```

**Cursor rules (per-project)**

```bash
# copy the rule file into your project
mkdir -p .cursor/rules
curl -o .cursor/rules/anti-bloat.mdc https://raw.githubusercontent.com/wind-c/anti-bloat-skills/main/.cursor/rules/anti-bloat.mdc
```

**Claude Code Plugin**

```
/plugin marketplace add wind-c/anti-bloat-skills
/plugin install common-anti-bloat@common-anti-bloat
```

**OpenCode**

First clone the repo:

```bash
git clone https://github.com/wind-c/anti-bloat-skills.git
```

Then copy the skill:

```bash
# Linux / macOS
mkdir -p ~/.config/opencode/skills/common-anti-bloat
cp -r skills/common-anti-bloat/* ~/.config/opencode/skills/common-anti-bloat/

# Windows PowerShell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills\common-anti-bloat"
Copy-Item -Recurse -Force "skills\common-anti-bloat\*" "$env:USERPROFILE\.config\opencode\skills\common-anti-bloat\"
```

## Validation

```bash
skills-ref validate common-anti-bloat     # → Valid skill (exit 0)
```

## License

MIT — see [LICENSE.txt](skills/common-anti-bloat/LICENSE.txt)

Conforms to the [Agent Skills specification](https://agentskills.io/specification).
