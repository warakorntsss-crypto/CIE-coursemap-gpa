# Session Handoff — 2026-06-07 — CIE Course Map

Context for a new session. Read this + `D:\CLAUDE_WORK\MISTAKE.md` (2026-06-07 entry) + the
CIE entry in `D:\CLAUDE_WORK\MEMO.md`.

## What this session built
Interactive + draw.io **study course map** for the **B.Eng. Civil Engineering (International
Program)** curriculum (CIE 2568 · 4-yr · 149 cr). Data sourced from NotebookLM notebook
`cie_curriculum` (id `d4b2b73c-b942-4867-bfac-16c86c6c3025`).

## Files (all in `D:\CLAUDE_WORK\CourseMaps\`)
- `curriculum_data.py` — **single source of truth**: `COURSES` (55, col/short/name/credits/cat),
  `PREREQS` (39 edges, coreq flag), `CAT` colors, `SEMS` credit totals, `DESC` one-liners.
- `build-map.py` → `CIE-CivilEng-CourseMap.drawio` (9 semester columns, color-by-category,
  prereq arrows).
- `build-interactive.py` → `index.html` (self-contained blueprint-themed app).
- Rebuild: edit `curriculum_data.py` → `python build-interactive.py` (and/or `build-map.py`).

## index.html features (all Playwright-verified this session)
- Hover (desktop) / tap (mobile) a course → it + transitive **prereqs (cyan)** + **unlocks
  (amber)** glow; rest dims. Tap pins the glow + opens panel.
- ★ star (localStorage `cie_stars_v1`); per-course notes (`cie_notes_v1`); panel shows
  description / prereqs / unlocks / notes.
- Filter: category legend chips + "starred only". Search box. Zoom: Fit / + / − / 1:1.
  Sticky semester headers (height measured in JS, no overlap). Responsive/mobile.
- Routing: adjacent-col edges = clean single-bend elbows; spanning edges = gap-band lanes.
  Verified 0 wire-box crossings (2357 path samples).

## Design decisions locked
- Layout = semester-timeline (9 cols Y1S1…Y4S2 + summer), color by category, prereq arrows.
- Output = editable `.drawio` + interactive HTML, both from shared data.
- Aesthetic = engineering blueprint (dark grid, cyan glow, amber stars). Built via `frontend-design`.

## Known issues / postmortem (full list in MISTAKE.md + MEMO.md backlog)
- **Data unverified vs source PDF** (`pdftoppm` was missing). Notebook smells passed through:
  `CE313 → co-req 251312` (typo for 251313?), `CE499 → 251399` (course not in plan).
- OR-prerequisites flattened to AND; co-reqs mostly dropped (only CHEM162→CHEM167 dashed).
- Electives are placeholders (no real options listed).
- Built routing 3× (should have specced once).

## Recommended next steps (priority order)
1. **Verify data**: extract source PDF text (`pypdf`/`pdfplumber`), diff vs `curriculum_data.py`,
   fix the 251312/251399 smells, add citations.
2. **Build-time validation** in the generators: edge endpoints exist, no cycles (topo-sort),
   column credit sums match, prereq in earlier/same semester.
3. Model **AND/OR/coreq** prereqs as first-class.
4. Student features: "mark completed" → earned/remaining credits + "available now" highlight.
5. stars+notes+progress **JSON export/import** (offered, not built).
6. A11y (category not color-only, keyboard nav, ARIA, reduced-motion); Sugiyama routing + minimap.

## Env notes
- Work scope = `D:\CLAUDE_WORK\` only (CLAUDE.md rule).
- Local HTTP serve for browser test: `python -m http.server <port>` from `CourseMaps\`
  (file:// is blocked in the Playwright MCP). Stop the bg job after; don't kill all python.
- `notebooklm` notebook key for this curriculum: `cie_curriculum`. Query via `/peet-ask --notebook cie_curriculum ...`.
