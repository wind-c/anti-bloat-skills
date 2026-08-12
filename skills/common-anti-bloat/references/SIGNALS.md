# Bloat signals — reference

Ten patterns with a detection method each. **Calibrate first** (§0 of `SKILL.md`): an
**uncalibrated** detector still returns a number, and that number is worse than no number —
it reads as evidence. Every "measured" note below is what an uncalibrated run actually
produced.

This file is *recognition* material — reached when scanning a diff or running the audit.
The gates you run before writing code live in `SKILL.md` and do not need this file.

---

Each signal includes a **detection method** that needs nothing beyond grep and file-system
inspection.

Two carry an **inline language split**: A2 (does the language compile?) and A6 (nominal or
structural typing?). Three need **numbers reset per language**: A5, A8, A10 — see the §0 table.

### A1 — Core depends on future-tier

**Signal**: A module labeled "core", "domain", or "engine" importing from a module that represents an optional, higher-edition, or future feature.

**Example**: A single-node dispatcher importing cluster-orchestration types. A payment engine importing analytics-dashboard DTOs. A library crate depending on a CLI framework.

**Detection**: List the imports of your "core" modules. For each import, ask: does removing this capability break the current milestone? If no, it's a potential A1.

**Prevention**: Every cross-tier import must survive the question "is the imported module in the same edition as the importer?" If not, decouple with a trait/interface at the boundary, or reject the import. Tier-spanning imports are the most common bloat vector.

### A2 — Configuration compiles dead paths

**Signal**: Config schema, validation, or defaults for a feature that no active code path reads — but the config module compiles them unconditionally.

**Example**: A config module with TLS cluster sections compiled into a single-node build. A feature-flag-gated feature whose config block isn't gated by the same flag.

**Detection**: For each config section, grep for its keys in the rest of the codebase. Any section with zero reads outside config/ itself is dead. This works in every language.

**Prevention** — *split by language family, because the mechanism differs*:

- **Compiled with feature flags** (Rust/C++/Go build tags): gate both sides. `#[cfg(feature = "X")]` must wrap the consumer code AND its config declaration, or dead config compiles into every binary.
- **Interpreted / data-driven config** (Python/JS/Ruby, YAML/TOML/JSON): there is no compile step and no binary to bloat — the config is *data*, so this signal degrades from "wasted bytes" to "**lying documentation**". A settings key that nothing reads tells the next person a feature exists when it doesn't. The gate is therefore a **convention plus a test**: mark unimplemented keys explicitly (`# ⛔GATE: not wired yet`), and keep a test that fails when a key has zero readers.

> Do not import the compiled-language prescription into an interpreted project. The
> detection transfers; the prevention does not.

### A3 — Prototype sidestepping expiry

**Signal**: Two modules, packages, or crates implementing the same capability — one labeled "spike", "poc", "prototype", "experimental", or "v0"; the other as production. Both are actively maintained.

**Example**: A `payment-spike` package alongside `payment`. A `routing-v1` module coexisting with `routing-v2`.

**Detection** — **match names, not file contents.** A3 is about two *units* coexisting, so look at directory and manifest names only:

```bash
# package / module / crate names — not source text
find . -maxdepth 3 -type d \( -name '*spike*' -o -name '*poc*' -o -name '*prototype*' \
   -o -name '*experimental*' -o -name '*_old' -o -name '*_deprecated' \)
# then: does a sibling exist with the qualifier stripped?
```

A hit only counts when the de-qualified sibling **also exists and is maintained**.

> 🔴 **Do not content-grep for these words, and never include `v0|v1` in the pattern.**
> Measured on a real 128-file Python project: content-grep returned **4 hits, all false
> positives** — `scene_prototypes` and `command_prototypes` are legitimate domain nouns
> (prototype vectors), `spike` appeared in a comment, and `v1` came from the URL
> `/v1/embeddings`. Every OpenAI-compatible endpoint contains `/v1/`. True positives: zero.
>
> Also note `app/` + `app2/` style pairs: two front-ends for **different platforms**
> (web and native) are not A3 even though the names look like v1/v2. A3 requires
> *the same capability on the same platform*, not similar names.

**Prevention**: Every prototype must carry an expiry date in its module header and package manifest. At expiry: delete or graduate. Graduation implies immediate deletion of the prototype — never maintain both.

### A4 — Entry point as business logic

**Signal**: The application entry point (`main.rs`, `index.ts`, `__main__.py`, `cmd/root.go`, CLI handler) exceeds ~300 lines, or imports domain types directly rather than delegating to a library.

**Example**: A `main.rs` at 31,000 lines declaring 15+ cluster modules and wiring cross-node RPC. An `index.ts` that constructs database connections, validates business rules, and formats API responses.

**Detection**: Check the entry point file size. If it's the largest or second-largest file in the project, it's an A4. Also check: does it import "domain" types directly (models, services, repositories)? It should only import assembly/wiring types.

**Prevention**: The entry point does exactly three things: load configuration, assemble dependencies, start the lifecycle loop. Everything else belongs in a library crate/package. If two entry-point files need the same data structure, that structure already belongs in a library.

### A5 — Package for a file, crate for a module

**Signal**: A new package/crate created to hold one or two files totaling under ~200 lines, when an existing package could have absorbed them.

**Example**: A `string-utils` package with a single `capitalize()` function. A `types` crate re-exporting two structs.

**Detection**: Check the file count and line count of each leaf package/crate. Any with <3 files and <500 lines is a candidate for inlining into its parent.

**Prevention**: New crates/packages require at least two of: (a) a distinct compile boundary, (b) a distinct domain boundary, (c) at least 3 files or 500 lines expected within the current milestone. Otherwise, use a module/file in the nearest existing parent.

### A6 — Premature abstraction

**Signal**: An interface, trait, abstract class, or protocol with exactly one real implementation (test mocks don't count). The abstraction was created "in case we need to swap implementations later."

**Example**: A `StorageBackend` trait with only `RocksDbStorageBackend`. A `PaymentProvider` interface with only `StripeProvider`.

**Detection** — **depends on whether your language's typing is nominal or structural**:

- **Nominal typing** (Rust traits, Java/C# interfaces, Python ABC with explicit inheritance):
  count the declared implementors. Count = 1 (excluding test doubles) → candidate A6.
- **Structural typing** (Python `Protocol`, Go interfaces, TypeScript interfaces):
  **implementors do not name the abstraction**, so counting subclasses always returns 0 and
  flags everything. Count **call sites that accept the abstraction and are actually passed
  two different concrete types** — usually one production type and one offline/mock type.
  If the only second type exists solely for tests, that is still a real reason to keep the
  seam: it is what makes the code runnable without hardware.

> 🔴 Measured on a real Python project: subclass-counting reported **0 implementors for 10 of
> 11 Protocols**, including `ReachyAdapter` (which has two: `MockReachy` and `RealReachy`) and
> `LocalVLM` (`OpenAICompatChat` and `FakeVLM`). Applying the nominal rule there would have
> flagged every abstraction in the codebase. Use the structural rule, or skip A6 — running it
> uncalibrated buys nothing.

**Prevention**: Keep the first implementation concrete. Extract the interface only when the second implementation arrives — you'll know exactly what the interface should look like because you have two real consumers driving it.

### A7 — Docs outgrowing code

**Signal**: Design documents, implementation plans, adversarial reviews, observation records, and diagnostic reports collectively outnumber source files.

**Example**: 2,051 documents for a project that hasn't shipped — 627 designs, 511 plans, 913 reports, of which a significant fraction are one-time observations ("recorded a failed Docker build").

**🔴 Count is not the metric.** Measured on two projects: the 2,051-document one above sits at **1 doc per 83 lines of code**; a healthy 147-document project sits at **1 doc per 80 lines**. Identical density — the absolute count just tracks codebase size. A rule of "docs ≥ source files" fires on both and tells you nothing.

**Detection** — two questions, neither about volume:

1. **Can a reader tell current from historical?** Dated filenames (`design_20260710.md`) are historical records; undated ones get read as current. Without that convention every document claims to be current, and the corpus is unusable at any size.
2. **Of the documents a reader would take as current, how many still hold?**

```bash
# undated docs whose referenced paths no longer exist = the actual debt
for f in $(ls docs/**/*.md | grep -vE '[0-9]{8}|[0-9]{4}-[0-9]{2}-[0-9]{2}'); do
  grep -oE '`[a-z_]+/[A-Za-z0-9_./-]+`' "$f" | tr -d '`' | while read p; do
    [ -e "$p" ] || echo "$f -> $p"; done; done
```

Measured on that 147-document project: 89 **dated** records were 62% "stale" — correct, they describe the past — while only **4 undated** documents contained dead references. Four is the debt; the other 143 are fine.

What *is* pathological in the 2,051-document case is composition, not count: 913 were one-time observations ("recorded a failed Docker build"). Those never should have been documents. That is the finding — the number is not.

**Prevention**:

- Diagnostics, one-off fixes and build investigations go in commit messages and issue trackers, never in `docs/`.
- **Date the filename** of anything that records a moment (report, plan, handoff, session). Undated means you are promising it is current, so you must keep it current.
- When a document stops being true: **dated** → leave it, add one line at the top pointing at what superseded it. **Undated** → fix it or delete it.

> ⛔ **Keep every document that records a falsified hypothesis or a measured baseline —
> permanently, at any age.** Those are not artifacts, they are fences. A report saying "we tested swapping the ASR model
> and it changed nothing" costs one page and saves the next person a week of re-running it.
> Deleting it re-opens a door that was closed at real expense.
>
> This is why a fixed-size "living docs pool" — every new design doc must evict an old one —
> is the wrong rule: negative results are the most expensive kind to obtain and the easiest
> to mistake for clutter, so they are exactly what such a pool evicts first.

### A8 — Dependency for a one-liner

**Signal**: An external library added to supply functionality that can be implemented in the project in under 30 lines.

**Example**: `left-pad`, `is-odd`, `uuid` (when the platform has a built-in), micro-utility crates with a single exported function.

**Detection**: For each dependency added in the current change, ask: "Can I implement the functionality I actually need from this library in <30 lines?" If yes, implement it; if no, evaluate: "Am I using >30% of this library's API surface?" If no, consider extracting only the needed subset.

**Prevention**: Before adding a dependency, write the 30-line implementation. If it covers your use case, ship it. If it doesn't, the dependency is justified — but document which 30% you're using and why the other 70% doesn't matter.

### A9 — Two copies of one fact

**Signal**: The same fact — a mapping, a threshold, a word list, a path pattern — is written
in two places that must agree, with nothing forcing them to. **This is not bloat by line
count; it is bloat by obligation.** Each copy adds a maintenance duty that no tool enforces,
and the failure mode is drift, which is *silent*.

**Example**: A keyword→action map declared once in the wake-word module and again in the
config loader. They drifted; the feature was gated off, so nothing failed — until someone
enabled it, at which point it failed silently rather than loudly. Another: a `.gitignore`
pattern naming a directory that a later refactor moved, so a 10 MB generated database
quietly became eligible for commit while `git status` looked normal.

**Detection**:

```bash
# 1. the honest admission — code that knows it has a twin
grep -rn "keep in sync\|must match\|同步\|mirrors\|duplicated in\|see also:" --include='*' .

# 2. constants defined in code AND in config
#    for each config key, check whether a literal of the same value exists in source
# 3. any literal list of >3 items appearing in two files
```

The strongest signal is a comment telling a human to remember something. **A comment saying
"keep this in sync with X" is a bug report, not documentation.**

Verification is separate from detection: for each suspected pair, change one copy and confirm
something fails. If nothing fails, they were never linked and the drift is already possible.

**Prevention**: One of the two must be **derived** from the other — import it, generate it, or
read it at startup. If derivation is genuinely impossible (different languages, build stages,
or repositories), then a **test must assert the two are equal**, and that test must fail loudly
when they diverge. Two hand-maintained copies with a comment between them is the pattern that
rots; the comment is what makes it feel safe.

### A10 — Dead code that still passes CI

**Signal**: A module, script, or entry point that nothing imports and no test exercises. It
rots invisibly — **a green suite says nothing about code the suite never touches**. Unlike A3
(two live implementations) this is a *single* unit that has quietly stopped working.

**Example**: A standalone smoke-test script importing a package deleted weeks earlier. Every
test passed the whole time; it surfaced only when someone ran it by hand, and by then it was
not merely broken but obsolete — the skills it asserted on were gone too. Three documents
still told readers to run it.

**Applicability**: largely a **dynamic-language** signal. Where the compiler already resolves
imports (`cargo check --all-targets`, `go build ./...`, `tsc --noEmit`) run that instead —
see §0.

**Detection**: [`scripts/dead-import-scan.py`](../scripts/dead-import-scan.py) — static, no
imports executed, exits 1 on a hit so it drops into CI:

```bash
python scripts/dead-import-scan.py mypkg scripts/*.py
```

It makes **two** passes and both are load-bearing: a top-level pass, and a dotted pass for
your own package. Without the second, `mypkg.deleted.thing` looks healthy because `mypkg`
still imports — which is precisely how the example above survived for weeks.

Then the reverse direction: for each module, count inbound imports across source *and* tests.
Zero inbound and not an entry point → nothing can be using it.

**Prevention**: run it in CI. It costs seconds and converts invisible rot into an immediate
red. On a hit, decide deliberately: repair, or park it somewhere labelled as parked — **and
fix the documents that still point at it**, which is the part usually missed.
