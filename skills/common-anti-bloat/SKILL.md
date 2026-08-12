---
name: common-anti-bloat
description: Bloat guard. Use when the user worries about bloat or 屎山; before adding a package, dependency, abstraction, config section, or design doc; and when reviewing a diff for what it should have deleted.
license: MIT. LICENSE.txt has complete terms
metadata:
  author: wind
  email: "573966@qq.com"
  homepage: https://github.com/wind-c
  version: "1.1"
---

# common-anti-bloat

Bloat guard. Pre-flight checklist before writing new code. Detective scan during code review. Periodic deletion audit.

**Calibrate to your language before using — see §0.** Seven of the ten signals transfer
unchanged; three have thresholds or detection methods that are wrong in some languages, and
one barely exists in compiled ones.

---

## 0. Calibrate to your language first

Seven signals (A1, A2, A3, A4, A6, A7, A9) transfer as written once you use the language
variant each one names inline. **Three do not, and using them uncalibrated produces confident
nonsense**: A5's thresholds assume a language's file-granularity conventions, A8's assume its
packaging culture, and A10 largely does not exist where a compiler already checks imports.

| | **A5** package-for-a-file | **A8** dependency-for-a-one-liner | **A10** dead code past CI | other |
|---|---|---|---|---|
| **Rust** | raise the bar — a crate is a *compile boundary* with real build cost, so 500 lines is low | keep; crates.io has many small crates by design | mostly **covered by `cargo check --all-targets`** — run that instead | A2: `#[cfg(feature)]` variant |
| **Go** | **largely N/A** — small packages are idiomatic (`errors`, `io/fs`) | rarely fires; the stdlib is fat | **covered by `go build ./...`** | A2: build tags |
| **Java / C#** | **file count is meaningless** (one public type per file is mandated) — judge on total lines, ~200 | rarely fires; nobody ships a one-function artifact | covered by the compiler | A2: no compile gate → use the "lying config" variant |
| **Python / Ruby** | as written | as written; 30 lines is a fair budget | 🔴 **primary signal — must run.** Imports resolve at runtime, so dead references survive a green suite indefinitely | A3: also scan single-file modules, not just directories |
| **TypeScript** | as written | 🔴 **strongest here** — npm micro-package culture is where `left-pad` came from | strict mode: covered by `tsc --noEmit`; loose/JS: primary signal | |
| **C / C++** | judge per file, not per directory | as written | covered by the compiler / linker | 🔴 A3: prototypes are often *files* (`parser_v2.c`), so scan filenames too, not only directory names |

**Rule for dropping a gate**: only when the language has no such construct (see §4). Record
which one and why. Re-tuning a threshold is not dropping a gate — write the new number down.

> **Evidence base, stated honestly**: the thresholds here were derived from **two** projects —
> one Rust (170k lines, the 31k-line `main.rs` and 2,051-document examples) and one Python
> (12k lines, the false-positive measurements in A3/A6 and the doc-staleness split in A7).
> The Java, Go, TypeScript and C rows above are reasoned from language mechanics, **not
> measured**. Treat them as starting points and correct them from your own repo — then update
> this table.

---

## 1. The ten signals

Full write-ups — signal, example, detection command, prevention — live in
[`references/SIGNALS.md`](references/SIGNALS.md). **Read it when scanning a diff or running the audit** (§3);
the pre-flight gates in §2 stand on their own and do not need it.

| | | | |
|---|---|---|---|
| **A1** core depends on future-tier | **A2** config declares dead paths | **A3** prototype past its expiry | **A4** entry point as business logic |
| **A5** a package holding one file | **A6** abstraction with one implementation | **A7** documents that no longer hold | **A8** dependency for a one-liner |
| **A9** two copies of one fact | **A10** dead code that still passes CI | | |

## 2. Pre-flight checklist（steps）

Run before writing any new code — each item on this list blocks one bloat pattern. During code review, apply the same gates to the diff — each "Yes" is a finding to flag, not a blocker. Each step is a binary gate. **"Yes" means stop and fix the issue before continuing.** Answer honestly — every item on this list was violated at least once in a project that grew to 170k lines before its first release candidate.

1. **"Does this change serve the CURRENT milestone?"**
   *Yes* → continue. *No* → stop. Future features wait for future milestones.

2. **"Is the new code going into an entry point (main.rs, index.ts, cmd/) rather than a library?"**
   *Yes* → stop. Move it to a library crate/package. Entry points are for assembly only.

3. **"Does any new config section lack a corresponding feature gate?"**
   *Yes* → stop. Add the gate. Dead config compiles into every binary.

4. **"Is this a prototype?"**
   *Yes* → write an expiry date in the module header NOW. *No* → continue.

5. **"Does this change alter external semantics (protocol, storage, API, security, deployment)?"**
   *Yes* → a design doc is required (one-page max), but must replace an existing one in the living-docs pool. *No* → no new doc.

6. **"Does this need a new package/crate, or can it be a file in an existing one?"**
   *New package* → must satisfy at least two: distinct compile boundary, distinct domain boundary, ≥3 files or ≥500 lines expected.

7. **"What existing code, config, dependency, or doc can this change DELETE or CONSOLIDATE?"**
   *Nothing* → explain why in the commit message. *Something* → delete it first, then add.

8. **"Am I writing down a fact that already exists somewhere else?"**
   *Yes* → stop. Derive it (import/generate/read at startup), or add a test asserting the two
   stay equal. Shipping two hand-maintained copies with a "keep in sync" comment is the
   pattern that rots silently — see A9.

---

## 3. Quarterly bloat audit（steps）

Run every three months. Produces an ADR under `docs/adr/NNNN-quarterly-deletion-review.md`.

### Step 1 — Dead import scan

For each "core" or "domain" module, list its imports. Flag any import from a module that represents an optional, future, or higher-tier feature. For each flag: delete the import and its usage, or justify why it's now a permanent dependency.

### Step 2 — Duplicate implementation scan

Run **A3**'s directory-name scan (`references/SIGNALS.md`). A hit counts only when the de-qualified
sibling also exists, both are maintained, and they cover the same capability on the same
platform. Then: delete (expiry reached) or graduate (delete the prototype, keep production).

### Step 3 — Stale living-doc scan

Run **A7**'s undated-document check (`references/SIGNALS.md`). Every undated document with a dead
reference: fix it or delete it. Dated documents are historical records — leave them, and
add one line at the top naming what superseded them. **Keep every document that records a
falsified hypothesis or a measured baseline, permanently, at any age** — those are the
cheapest fences you own.

### Step 4 — Dependency audit

List every direct dependency. For each: when was it last updated? Is ≥30% of its API surface in use? Can it be inlined? Flag candidates for removal.

### Step 5 — Test relevance check

For each test file: does the production code it tests still exist? If not, delete the test. A test for removed code is dead weight.

### Step 6 — Entry-point liveness

Run **A10**'s import check (`references/SIGNALS.md`) over every standalone script and declared entry
point — including the dotted-path pass, which is the one that catches deletions inside your
own package. Anything that raises has been dead since an earlier refactor and the green
suite never noticed. Repair it, or park it somewhere labelled as parked **and fix the
documents that still point at it**.

### Step 7 — File the ADR

Record: what was deleted, what was kept and why, what was flagged for the next review. The ADR is evidence that deletion review happened — it is a mechanical record, not a design document.

---

## 4. Relationship to project-specific anti-bloat skills

This skill provides language-agnostic pattern recognition. Repositories with known bloat history should supplement it with a repo-local `.codex/skills/anti-bloat/SKILL.md` that contains: concrete file paths, exact line counts, real commit hashes, and project-specific grep commands for each anti-pattern. The global skill recognizes the abstract pattern; the local skill proves it with evidence from this codebase.

The AGENTS.md must reference the local skill. When both exist, the agent reads the local skill first (evidence from this project), then falls back to this one (general patterns for novel situations).

The eight checklist questions and seven quarterly review steps in this document are the
canonical list. Local overrides may **add** specificity freely.

A gate may be **dropped only for one reason**: the signal does not exist in this
language or runtime — e.g. A2's compile-time feature gating in an interpreted project,
or A6 where structural typing makes implementor-counting meaningless. Record which gate
was dropped and why, in the local skill. "It is inconvenient here" is not a reason;
"this language has no such construct" is.
