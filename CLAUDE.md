# Anti-Bloat Guidelines

Bloat guard for codebases that are still growing — executable detectors, not principles.
Every signal comes with a command you can run and a number it should return.

## Calibrate first

Three signals need per-language tuning before use. Apply these defaults unless overridden:

| Signal | Rust | Go | Java/C# | Python/Ruby | TypeScript | C/C++ |
|--------|------|----|---------|-------------|------------|-------|
| A5 (one-file package) | raise bar — crate is a compile cost | N/A — small packages are idiomatic | N/A — one type/file is mandated | ~500 lines | ~500 lines | per file, not directory |
| A8 (dep for one-liner) | keep — small crates are normal | rarely fires — fat stdlib | rarely fires | as written (30 lines) | strongest here | as written |
| A10 (dead code past CI) | covered by `cargo check` | covered by `go build ./...` | covered by compiler | primary signal — must run | strict: `tsc --noEmit` | covered by compiler/linker |

## The Ten Signals

Full write-ups in `skills/common-anti-bloat/references/SIGNALS.md`. Summary:

| # | Signal | Detection |
|---|--------|-----------|
| A1 | core depends on future-tier | grep for imports from optional/future modules in core |
| A2 | config declares dead paths | grep config keys, check if feature gates exist for each |
| A3 | prototype past its expiry | scan for dirs/files with `_v2`, `_prototype`, `_new` suffixes past their date |
| A4 | entry point as business logic | check `main.rs`/`cmd/`/`index.ts` — business logic belongs in libraries |
| A5 | a package holding one file | count files per package/directory |
| A6 | abstraction with one implementation | count implementors of each interface/trait |
| A7 | documents that no longer hold | check undated docs for dead references |
| A8 | dependency for a one-liner | audit each dep — can it be inlined under 30 lines? |
| A9 | two copies of one fact | grep for identical logic blocks, "keep in sync" comments |
| A10 | dead code that still passes CI | run `scripts/dead-import-scan.py` (dynamic languages) or compiler (static) |

## Pre-Flight Checklist

Run before writing new code. Each item blocks one bloat pattern. **"Yes" means stop and fix.**

1. **Does this change serve the CURRENT milestone?** — No → stop. Future features wait.
2. **Is new code going into an entry point (main.rs, index.ts, cmd/)?** — Yes → move to a library.
3. **Does any new config section lack a corresponding feature gate?** — Yes → add the gate.
4. **Is this a prototype?** — Yes → write an expiry date in the module header NOW.
5. **Does this change alter external semantics?** — Yes → a one-page design doc is required.
6. **Does this need a new package/crate?** — Must satisfy ≥2: distinct compile boundary, distinct domain boundary, ≥3 files or ≥500 lines expected.
7. **What existing code, config, dependency, or doc can this change DELETE?** — Nothing → explain why in the commit message.
8. **Am I writing down a fact that already exists elsewhere?** — Yes → derive or add a sync test. Don't ship two hand-maintained copies.

## Code Review Gates

Apply the same eight gates to every diff. Each "Yes" is a finding to flag.

## Surgery Rules

- Touch only what you must. Don't refactor adjacent code that isn't broken.
- Match existing style, even if you'd do it differently.
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked — mention it instead.
- Every changed line should trace directly to the user's request.

## Quarterly Audit

Run `skills/common-anti-bloat/references/SIGNALS.md`§3:
1. Dead import scan
2. Duplicate implementation scan
3. Stale living-doc scan
4. Dependency audit
5. Test relevance check
6. Entry-point liveness
7. File an ADR (`docs/adr/NNNN-quarterly-deletion-review.md`)
