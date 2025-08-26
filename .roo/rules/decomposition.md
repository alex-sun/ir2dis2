# Rule: Micro‑Task Decomposition + Strict TDD

**One‑liner:** Always split features into the smallest possible micro‑steps (5–30 minutes each). For every step, write/ensure tests first, run them, make them pass (green), refactor safely, and only then move on.

---

## Canonical wording (paste into your system/developer prompt)
1) Decompose every feature into micro‑steps (each 5–30 minutes of work).  
2) For the current step, define a clear **Definition of Done (DoD)** and testable acceptance criteria.  
3) **Tests first**: add/adjust the minimal tests so they fail initially (red).  
4) **Run tests** and show the command/output (or provide exact command to run).  
5) Implement the **minimal** code necessary to go green — no parallel refactors or “bonus” features.  
6) Re‑run tests. If red, **do not** proceed; explain what will be fixed and do it.  
7) When green, perform a short **refactor without changing behavior**.  
8) Commit the step (see message template below), then select the **next micro‑step** and repeat.

**Forbidden:** advancing with red tests, doing multiple unrelated changes at once, silent behavior changes, or adding extra features “while I’m here”.

---