# CIE Course Map + GPA Tracker

Interactive study map and GPA tracker for the **B.Eng. Civil Engineering (International Program)**
curriculum (CIE 2568 · 4-year · 149 credits, Chiang Mai University).

Everything is generated from one shared dataset into two outputs: an editable draw.io diagram and a
self-contained interactive HTML app (`index.html`, opens by double-click — no server, no build step).

## Features (`index.html`)

- **Prerequisite map** — 55 courses across 9 semester columns, colored by category, connected by
  prerequisite arrows. Hover/tap a course to glow its full transitive **prerequisites** (cyan) and
  what it **unlocks** (amber); the rest dims. Tap to pin + open a detail panel
  (description / prereqs / unlocks / notes).
- **Grade + GPA tracker** — per-course grade dropdown (A / B+ / B / C+ / C / D+ / D / F / W).
  A "Progress" panel shows **GPA per semester**, a Summer line, the **cumulative GPA**, and
  **credits studied**. CMU scale: A=4, B+=3.5, B=3, C+=2.5, C=2, D+=1.5, D=1, F=0; W excluded.
- **Internship / Co-op eligibility** — `⚑ intern` and `⚑ co-op` highlight the subjects each track
  requires: a green ring when the grade meets the minimum (A–D for internship, A–C for co-op), a red
  ring when it doesn't; everything else dims. The `⚑ tracks` page prints a full eligibility report —
  requirements, subject table with the student's grades, the GPA check (> 1.75 by Y3/S1 for the
  internship, > 2.00 cumulative for co-op), an ELIGIBLE / NOT ELIGIBLE verdict, and a
  **"Contact your Academic Advisor"** warning when a condition is unmet. The student's study year is
  derived from the ID prefix (e.g. `67…` → Year 3); a non-numeric prefix shows "Year unknown".
  Source of the rules: CIE Year-End Meeting 2-68 deck.
- **Editable electives** — for elective slots the student can edit the registered **course code**
  and type the **actual course name**; both flow into the printed documents.
- **Save as PDF** — a formal A4 document via the browser print dialog, in two layouts:
  - **Detailed** — per-semester tables (code / title / credit / grade + semester GPA), a summary
    box, an advisor's comment box, and student + advisor signature blocks.
  - **1-Page** — a compact year-as-column grid showing code + grade + per-year GPA only, sized to
    fit a single page.
- Stars, notes, grades, elective edits, student name/ID, and advisor comment all persist in the
  browser (`localStorage`).

## Files

| File | Purpose |
|------|---------|
| `curriculum_data.py` | **Single source of truth** — courses, credits, categories, prerequisites, descriptions. |
| `build-interactive.py` | Generates `index.html` (the interactive app). |
| `build-map.py` | Generates `CIE-CivilEng-CourseMap.drawio` (editable diagram). |
| `index.html` | The generated, self-contained app. |
| `CIE-CivilEng-CourseMap.drawio` | The generated draw.io diagram. |

## Rebuild

```bash
# edit curriculum_data.py, then:
python build-interactive.py     # -> index.html
python build-map.py             # -> CIE-CivilEng-CourseMap.drawio
```

## Data note

Curriculum data was sourced from a NotebookLM notebook and has **not** yet been diffed against the
official curriculum PDF. A couple of source smells remain to verify (e.g. a `CE313` co-requisite
code and a `CE499` prerequisite that isn't in the plan). Treat course/credit/prereq details as
draft until verified against the primary source.
