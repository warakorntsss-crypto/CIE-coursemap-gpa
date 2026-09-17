# CIE Course Map — Google Apps Script backend (v4)

Turns your Google Sheet into the live database. **v2 layout**: one tab per semester (grades), a
`students` tab (login/identity), and an `extras` tab (notes / stars / elective overrides).

Sheet: `https://docs.google.com/spreadsheets/d/<YOUR_SHEET_ID>/edit` — this repo is public, so the
real Sheet ID is deliberately not committed. The script is container-bound and reaches the Sheet
through `getActiveSpreadsheet()`, so it never needs the ID in code; you only need it to open the
Sheet yourself.

Auth is **server-side**: login + register are validated in the script, and the public read endpoint
**never returns the password column**. Login returns the student's profile + grades + extras in ONE
call (fast).

> ⚠ `setup()` **wipes and reseeds** every tab it touches. Run it once on an empty / throwaway Sheet.

---

## 1. Paste the script

Open the Sheet → **Extensions → Apps Script**. Delete `Code.gs`, paste the whole block, **Save**.

```javascript
/***** CIE Course Map — Sheets backend (v4) *****
 * Layout:
 *   students : student_id | password | name | advisor | advisor_comment | role | track | extra_sems | plan_sems
 *   <Y1S1..> : student_id | <course_key columns...>   (cell = grade)   one row / student
 *   extras   : id | student_id | course_key | starred | note | elec_code | elec_name | moved_col
 *   custom   : id | student_id | course_key | code | name | cr | cat | col | major_gpa | retake_of | attempt
 *
 * v3 adds three things, all additive:
 *   track     — "regular" | "coop". Which curriculum the student is following.
 *   moved_col — per-course placement override: the semester the student ACTUALLY took it in.
 *               The grade still lives in the course's home semester tab, so a move needs no
 *               semester-tab schema change.
 *   custom    — student-added courses that are not in the curriculum. Their GRADE is not
 *               stored here: it goes into the semester tab like every other course, because
 *               setGrade now creates a missing course column on demand (see below).
 *
 * GET  ?action=ping                 -> {ok:true}
 * GET  ?sheet=<Y1S1|extras|...>     -> [rows]   (students is blocked / password stripped)
 * POST {action:"login",   student_id, password}   -> {ok,profile,grades,extras,customs} | {ok:false}
 * POST {action:"register",student_id, name, password, advisor} -> {ok,profile} | {ok:false,error}
 * POST {action:"setGrade",student_id, sem, course_key, grade}  -> {ok:true}
 * POST {action:"setExtra",student_id, course_key, data:{...}}   -> {ok:true}
 * POST {action:"setProfile",student_id, data:{name,advisor_comment,track,extra_sems,plan_sems}} -> {ok:true}
 * POST {action:"setExtra",  student_id, course_key, remove:true}                -> {ok:true}
 * POST {action:"setCustom", student_id, course_key, data:{code,name,cr,cat,col,major_gpa,retake_of,attempt}} -> {ok:true}
 * POST {action:"setCustom", student_id, course_key, remove:true}               -> {ok:true}
 *
 * Run setup() ONCE from the editor to build all tabs + demo seed.
 ************************************************/

var STUDENT_HEADERS = ["student_id", "password", "name", "advisor", "advisor_comment", "role", "track", "extra_sems", "plan_sems"];
var EXTRA_HEADERS   = ["id", "student_id", "course_key", "starred", "note", "elec_code", "elec_name", "moved_col"];
// v3: student-added courses that are not in the printed curriculum (free electives taken
// off-plan, repeated subjects, summer courses). Their grade lives HERE, not in a semester tab.
var CUSTOM_HEADERS  = ["id", "student_id", "course_key", "code", "name", "cr", "cat", "col", "major_gpa", "retake_of", "attempt"];

// Semester tab name -> the course-keys that live in that semester (from curriculum_data.py).
// NOTE: duplicated from the curriculum. Curriculum is stable; if courses move, update here + setup.
var SEM_ORDER = ["Y1S1","Y1S2","Y2S1","Y2S2","Y3S1","Y3S2","Summer","Y4S1","Y4S2"];
var SEM_TABS = {
  "Y1S1":   ["ENGL101","CHEM162","CHEM167","MATH161","PHYS105","PHYS115","ENGR103","ENGR104","ENGR191"],
  "Y1S2":   ["ENGL102","PG104","MATH162","PHYS106","PHYS116","CE102","ENGR106","ENGR107","GE_ELEC1"],
  "Y2S1":   ["ENGL201","CS100","GEOL275","MATH261","STAT263","CE211","CE261"],
  "Y2S2":   ["ENGL225","MATH362","CE212","CE216","CE262","ENGR201","GE_ELEC2"],
  "Y3S1":   ["CE292","CE311","CE336","CE363","CE371","CE372","GE_ELEC3"],
  "Y3S2":   ["CE313","CE333","CE334","CE343","CE364","CE374","FREE_ELEC1"],
  "Summer": ["CE400"],
  "Y4S1":   ["CE413","CE451","MAJ_ELEC1","FREE_ELEC2","CE401"],   // CE401 = co-op work term (251401, 6 cr)
  "Y4S2":   ["ENGR192","ENGR194","DESIGN_DEV","MAJ_ELEC2"]
};

/* ---------- routing ---------- */

function doGet(e) {
  try {
    var p = (e && e.parameter) || {};
    if (p.action === "ping") return jsonOut({ ok: true });
    if (p.sheet) {
      if (String(p.sheet).toLowerCase() === "students") {
        return jsonOut(readAll("students").map(stripPassword));   // never expose passwords
      }
      return jsonOut(readAll(p.sheet));
    }
    return jsonOut({ ok: true });
  } catch (err) { return jsonOut({ error: String(err) }); }
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var b = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    switch (b.action) {
      case "login":      return jsonOut(login(b));
      case "register":   return jsonOut(register(b));
      case "setGrade":   return jsonOut(setGrade(b));
      case "setExtra":   return jsonOut(setExtra(b));
      case "setProfile": return jsonOut(setProfile(b));
      case "setCustom":  return jsonOut(setCustom(b));
      default:           return jsonOut({ error: "unknown action: " + b.action });
    }
  } catch (err) {
    return jsonOut({ error: String(err) });
  } finally { lock.releaseLock(); }
}

/* ---------- generic helpers ---------- */

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
function getSheet(name) {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), want = String(name || "").toLowerCase(), all = ss.getSheets();
  for (var i = 0; i < all.length; i++) if (all[i].getName().toLowerCase() === want) return all[i];
  throw new Error("no sheet named '" + name + "'");
}
function headersOf(sh) {
  var lc = sh.getLastColumn(); if (lc === 0) return [];
  return sh.getRange(1, 1, 1, lc).getValues()[0].map(function (h) { return String(h); });
}
function readAll(name) {
  var sh = getSheet(name), headers = headersOf(sh), lastRow = sh.getLastRow();
  if (lastRow < 2 || headers.length === 0) return [];
  var values = sh.getRange(2, 1, lastRow - 1, headers.length).getValues(), out = [];
  for (var r = 0; r < values.length; r++) {
    var row = values[r];
    if (row.every(function (c) { return c === "" || c === null; })) continue;
    var obj = {};
    for (var c = 0; c < headers.length; c++) obj[headers[c]] = (row[c] === null) ? "" : row[c];
    out.push(obj);
  }
  return out;
}
function stripPassword(o) { var c = {}; for (var k in o) if (k !== "password") c[k] = o[k]; return c; }

// 1-based row whose <header> column == value; -1 if none.
function rowIndexBy(sh, headers, header, value) {
  var col = headers.indexOf(header); if (col === -1) return -1;
  var lastRow = sh.getLastRow(); if (lastRow < 2) return -1;
  var vals = sh.getRange(2, col + 1, lastRow - 1, 1).getValues();
  for (var i = 0; i < vals.length; i++) if (String(vals[i][0]) === String(value)) return i + 2;
  return -1;
}
function appendObj(sh, headers, data) {
  sh.appendRow(headers.map(function (h) { return (data[h] === undefined || data[h] === null) ? "" : data[h]; }));
}

/* ---------- actions ---------- */

function studentRow(student_id) {
  var sh = getSheet("students"), headers = headersOf(sh);
  var r = rowIndexBy(sh, headers, "student_id", student_id);
  if (r === -1) return null;
  var vals = sh.getRange(r, 1, 1, headers.length).getValues()[0], obj = {};
  for (var c = 0; c < headers.length; c++) obj[headers[c]] = (vals[c] === null) ? "" : vals[c];
  return obj;
}

// Every tab whose name looks like a semester, in sheet order. Discovered rather than read from
// SEM_ORDER: a grade written into a student-created tab like "Y5S1" MUST be readable back, or
// the app would look like it had silently lost the grade.
function semTabNames() {
  var all = SpreadsheetApp.getActiveSpreadsheet().getSheets(), out = [];
  for (var i = 0; i < all.length; i++) {
    var n = all[i].getName();
    if (SEMTAB_RE.test(n)) out.push(n);
  }
  // Order matters: gradesFor() lets a later tab overwrite an earlier one when the same course
  // key appears twice. v3 iterated SEM_ORDER, so keep that exact precedence for the nine
  // curriculum tabs and append discovered extra-year tabs after them -- otherwise sheet order
  // alone could silently flip which of two duplicate cells wins.
  out.sort(function (a, b) {
    var ia = SEM_ORDER.indexOf(a), ib = SEM_ORDER.indexOf(b);
    if (ia === -1) ia = 1e6;
    if (ib === -1) ib = 1e6;
    return (ia - ib) || (a < b ? -1 : a > b ? 1 : 0);
  });
  return out;
}

function gradesFor(student_id) {
  var grades = {}, tabs = semTabNames();
  for (var s = 0; s < tabs.length; s++) {
    var name = tabs[s], rows = readAll(name);
    for (var i = 0; i < rows.length; i++) {
      if (String(rows[i].student_id) !== String(student_id)) continue;
      var row = rows[i];
      for (var k in row) if (k !== "student_id" && row[k] !== "" && row[k] !== null) grades[k] = String(row[k]);
    }
  }
  return grades;
}
function extrasFor(student_id) {
  return readAll("extras").filter(function (r) { return String(r.student_id) === String(student_id); });
}
function customsFor(student_id) {
  // Tolerate a missing `custom` tab: this runs inside login(), and throwing here would lock
  // every student out of the app if the code is deployed before migrate_v3() has created it.
  if (!SpreadsheetApp.getActiveSpreadsheet().getSheetByName("custom")) return [];
  return readAll("custom").filter(function (r) { return String(r.student_id) === String(student_id); });
}

function login(b) {
  var row = studentRow(b.student_id);
  if (!row || String(row.password) !== String(b.password)) return { ok: false };
  return { ok: true, profile: stripPassword(row), grades: gradesFor(b.student_id),
           extras: extrasFor(b.student_id), customs: customsFor(b.student_id) };
}

function register(b) {
  var sid = String(b.student_id || "").trim();
  if (!sid || !String(b.password || "")) return { ok: false, error: "student id and password required" };
  if (studentRow(sid)) return { ok: false, error: "ID already taken" };
  var sh = getSheet("students");
  appendObj(sh, headersOf(sh), {
    student_id: sid, password: String(b.password), name: b.name || sid,
    advisor: b.advisor || "", advisor_comment: "", role: "student", extra_sems: 0, plan_sems: ""
  });
  // seed a student_id-only row in every semester tab
  for (var s = 0; s < SEM_ORDER.length; s++) {
    var t = getSheet(SEM_ORDER[s]); appendObj(t, headersOf(t), { student_id: sid });
  }
  var row = studentRow(sid);
  return { ok: true, profile: stripPassword(row), grades: {}, extras: [], customs: [] };
}

// A semester tab the curriculum never had -- "Y5S1" and beyond, once a student extends their
// plan past year 4 -- is created on demand, the same way a missing course column is. The name
// guard keeps junk out; SEMTAB_RE is also what tells gradesFor() which tabs hold grades.
var SEMTAB_RE = /^(Y\d+S\d+|Summer\d*)$/;
function ensureSemTab(name) {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), want = String(name || "");
  var all = ss.getSheets();
  for (var i = 0; i < all.length; i++) if (all[i].getName().toLowerCase() === want.toLowerCase()) return all[i];
  if (!SEMTAB_RE.test(want)) throw new Error("not a semester tab name: '" + want + "'");
  var sh = ss.insertSheet(want);
  sh.getRange(1, 1, 1, 1).setValue("student_id");
  sh.setFrozenRows(1);
  return sh;
}

function setGrade(b) {
  var sh = ensureSemTab(b.sem), headers = headersOf(sh);
  var col = headers.indexOf(b.course_key);
  // A course key with no column yet — the co-op work term, a student-added course, or a future
  // curriculum addition — gets its column created here rather than failing the write. The guard
  // keeps junk keys out; a key one student invents just leaves a blank column for everyone else.
  if (col === -1 && /^[A-Z][A-Z0-9_]{1,23}$/.test(String(b.course_key))) {
    sh.getRange(1, headers.length + 1).setValue(b.course_key);
    headers = headersOf(sh); col = headers.indexOf(b.course_key);
  }
  if (col === -1) return { ok: false, error: "no column " + b.course_key + " in " + b.sem };
  var r = rowIndexBy(sh, headers, "student_id", b.student_id);
  if (r === -1) { appendObj(sh, headers, { student_id: b.student_id }); r = sh.getLastRow(); }
  sh.getRange(r, col + 1).setValue(b.grade || "");
  return { ok: true };
}

function setExtra(b) {
  var sh = getSheet("extras"), headers = headersOf(sh);
  var id = String(b.student_id) + "_" + String(b.course_key);
  var d = b.data || {};
  // moved_col: the semester column the STUDENT actually took this course in, when it differs
  // from the curriculum. "" = follows the plan. The grade itself still lives in the course's
  // home semester tab, so moving a course needs no semester-tab schema change.
  var fields = { id: id, student_id: b.student_id, course_key: b.course_key,
    starred: d.starred || "", note: d.note || "", elec_code: d.elec_code || "", elec_name: d.elec_name || "",
    moved_col: (d.moved_col === 0 || d.moved_col) ? d.moved_col : "" };
  var r = rowIndexBy(sh, headers, "id", id);
  // b.remove === true deletes the row outright, the same way setCustom does. Without this the
  // only way to "clear" an extras row was to upsert a blank one, so every student-added course
  // that was later deleted left an empty row behind for good.
  if (b.remove) { if (r !== -1) sh.deleteRow(r); return { ok: true }; }
  if (r === -1) { appendObj(sh, headers, fields); return { ok: true }; }
  for (var k in fields) { var c = headers.indexOf(k); if (c !== -1) sh.getRange(r, c + 1).setValue(fields[k]); }
  return { ok: true };
}

// Returns the `custom` tab, creating it if it is not there yet, so a write works even on a
// Sheet where migrate_v3() has not been run.
function ensureCustomTab() {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), sh = ss.getSheetByName("custom");
  if (!sh) {
    sh = ss.insertSheet("custom");
    sh.getRange(1, 1, 1, CUSTOM_HEADERS.length).setValues([CUSTOM_HEADERS]);
    sh.setFrozenRows(1);
  }
  return sh;
}

// v3: upsert (or delete) one student-added course. b.remove === true deletes the row.
function setCustom(b) {
  var sh = ensureCustomTab(), headers = headersOf(sh);
  var id = String(b.student_id) + "_" + String(b.course_key);
  var r = rowIndexBy(sh, headers, "id", id);
  if (b.remove) { if (r !== -1) sh.deleteRow(r); return { ok: true }; }
  var d = b.data || {};
  var fields = { id: id, student_id: b.student_id, course_key: b.course_key,
    code: d.code || "", name: d.name || "", cr: (d.cr === 0 || d.cr) ? d.cr : "",
    cat: d.cat || "elec", col: (d.col === 0 || d.col) ? d.col : "",
    // whether this course counts toward the Major GPA. The student can override the default
    // their category implies, so it is stored rather than re-derived on load.
    major_gpa: (d.major_gpa === true || d.major_gpa === "TRUE") ? "TRUE" : "FALSE",
    // retake linkage: retake_of is the course_key of the attempt this one re-takes ("" for a
    // plain added course), attempt is 2 for a first re-take, 3 for a re-take of that, ...
    retake_of: d.retake_of || "",
    attempt: (d.attempt === 0 || d.attempt) ? d.attempt : "" };
  if (r === -1) { appendObj(sh, headers, fields); return { ok: true }; }
  for (var k in fields) { var c = headers.indexOf(k); if (c !== -1) sh.getRange(r, c + 1).setValue(fields[k]); }
  return { ok: true };
}

function setProfile(b) {
  var sh = getSheet("students"), headers = headersOf(sh);
  var r = rowIndexBy(sh, headers, "student_id", b.student_id);
  if (r === -1) return { ok: false, error: "no such student" };
  var d = b.data || {};
  // extra_sems: how many semester columns past the printed plan this student has grown
  // (year 5 and beyond). A plain scalar on the students row -- login returns it in `profile`
  // and the client falls back to 0 when it is blank.
  // plan_sems: PLAN-MODE. The semester columns the student has marked as planned rather than
  // already taken, as a comma-separated list of column indexes ("5,7,8"); blank = none. Stored
  // as one scalar for the same reason as extra_sems -- it is a property of the student, not of
  // any one course, so it does not belong in `extras`.
  ["name", "advisor_comment", "track", "extra_sems", "plan_sems"].forEach(function (k) {
    if (d[k] === undefined) return;
    var c = headers.indexOf(k); if (c !== -1) sh.getRange(r, c + 1).setValue(d[k]);
  });
  return { ok: true };
}

/* ---------- one-time setup: tabs + headers + demo seed ---------- */

// ---- v2 -> v3 migration. ADDITIVE and idempotent: it only ever appends missing tabs,
// headers and columns, and never clears a cell. Run this ONCE from the editor.
// Do NOT run setup() on a live Sheet — that wipes and reseeds every tab.
function migrate_v3() {
  var ss = SpreadsheetApp.getActiveSpreadsheet(), added = [];

  // 1. new header columns on existing tabs
  [["students", STUDENT_HEADERS], ["extras", EXTRA_HEADERS], ["custom", CUSTOM_HEADERS]].forEach(function (pair) {
    if (!SpreadsheetApp.getActiveSpreadsheet().getSheetByName(pair[0])) return;   // created below
    var sh = getSheet(pair[0]), have = headersOf(sh);
    pair[1].forEach(function (h) {
      if (have.indexOf(h) === -1) {
        sh.getRange(1, sh.getLastColumn() + 1).setValue(h);
        added.push(pair[0] + "." + h);
        have = headersOf(sh);
      }
    });
  });

  // 2. default every existing student to the regular track
  var st = getSheet("students"), sh2 = headersOf(st), tc = sh2.indexOf("track");
  if (tc !== -1 && st.getLastRow() > 1) {
    var rng = st.getRange(2, tc + 1, st.getLastRow() - 1, 1), vals = rng.getValues();
    for (var i = 0; i < vals.length; i++) if (vals[i][0] === "" || vals[i][0] === null) vals[i][0] = "regular";
    rng.setValues(vals);
  }

  // 3. the custom tab
  if (!ss.getSheetByName("custom")) {
    var cs = ss.insertSheet("custom");
    cs.getRange(1, 1, 1, CUSTOM_HEADERS.length).setValues([CUSTOM_HEADERS]);
    cs.setFrozenRows(1);
    added.push("tab custom");
  }

  // 4. any course key listed in SEM_TABS that has no column yet (e.g. CE401 for the co-op track)
  for (var s = 0; s < SEM_ORDER.length; s++) {
    var name = SEM_ORDER[s], tab = getSheet(name), have = headersOf(tab);
    SEM_TABS[name].forEach(function (key) {
      if (have.indexOf(key) === -1) {
        tab.getRange(1, tab.getLastColumn() + 1).setValue(key);
        added.push(name + "." + key);
        have = headersOf(tab);
      }
    });
  }

  var msg = added.length ? ("added: " + added.join(", ")) : "already up to date";
  Logger.log(msg);        // the editor does not show a return value -- log it so the run is visible
  return msg;
}

function setup() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // students
  writeTab(ss, "students", STUDENT_HEADERS, [
    ["admin",    "17025", "Administrator", "",         "", "admin",   "regular", 0, ""],
    ["65010001", "1234",  "Anan Suk",      "Dr. Pim",  "", "student", "regular", 0, ""],
    ["65010002", "1234",  "Bee Charoen",   "Dr. Chai", "", "student", "regular", 0, ""]
  ]);

  // 9 semester tabs: header = student_id + course-keys; seed the 3 students (grades blank,
  // plus a couple of demo grades for 65010001 in Y1S1).
  for (var s = 0; s < SEM_ORDER.length; s++) {
    var name = SEM_ORDER[s], headers = ["student_id"].concat(SEM_TABS[name]);
    var rows = [["admin"], ["65010001"], ["65010002"]].map(function (r) {
      var line = new Array(headers.length).fill(""); line[0] = r[0]; return line;
    });
    if (name === "Y1S1") {  // demo grades for 65010001
      var i = headers.indexOf("MATH161"); if (i !== -1) rows[1][i] = "A";
      var j = headers.indexOf("ENGL101"); if (j !== -1) rows[1][j] = "B+";
    }
    writeTab(ss, name, headers, rows);
  }

  // extras (seed one note/star matching the demo grades)
  writeTab(ss, "extras", EXTRA_HEADERS, [
    ["65010001_MATH161", "65010001", "MATH161", "TRUE", "felt solid on calc", "", "", ""]
  ]);

  // student-added courses: empty to start
  writeTab(ss, "custom", CUSTOM_HEADERS, []);   // definitions only; grades live in the semester tabs

  var def = ss.getSheetByName("Sheet1");
  if (def && ss.getSheets().length > 1) ss.deleteSheet(def);
}

function writeTab(ss, name, headers, rows) {
  var sh = ss.getSheetByName(name) || ss.insertSheet(name);
  sh.clear();
  sh.getRange(1, 1, 1, headers.length).setValues([headers]);
  sh.setFrozenRows(1);
  if (rows && rows.length) {
    // pad/trim every seed row to the header width — setValues() throws on a ragged range,
    // and the header lists grow when the schema does.
    var padded = rows.map(function (r) {
      var line = new Array(headers.length).fill("");
      for (var i = 0; i < headers.length && i < r.length; i++) line[i] = r[i];
      return line;
    });
    sh.getRange(2, 1, padded.length, headers.length).setValues(padded);
  }
}
```

---

## 1a. What v4 adds on top of v3

- `custom` gains **`retake_of`** and **`attempt`** — a re-take is stored as its own course row that
  points back at the attempt it repeats.
- **Semester tabs are created on demand.** A student who extends their plan past Year 4 gets grades
  written to `Y5S1`, `Y5S2`, `Y6S1`, … `setGrade` now creates such a tab the same way it already
  creates a missing course column. Tab names are guarded by `SEMTAB_RE` (`Y<n>S<n>` or `Summer`).
- **Grade reads discover semester tabs instead of using the fixed `SEM_ORDER` list.** This one is
  not optional: without it a grade written to `Y5S1` would never be read back on login and would
  look exactly like silent data loss. `semTabNames()` matches every existing tab too, so nothing
  about the current nine changes.

`migrate_v3` is header-driven — it tops up each tab against its `*_HEADERS` constant — so **re-running
it is all that v4 needs**; it will add the two new `custom` columns. There is no separate `migrate_v4`.

## 1b. Upgrading a LIVE Sheet (v2 → v4)

If the Sheet already has real student data, **do not run `setup()`** — it clears and reseeds every
tab. Run the additive migration instead:

Editor → function dropdown → **`migrate_v3`** → **Run**. It only appends what is missing and never
clears a cell, so it is safe to run twice. It:

1. adds the `track` column to `students` and `moved_col` to `extras`;
2. sets every existing student's `track` to `regular`;
3. creates the `custom` tab;
4. adds any course-key column listed in `SEM_TABS` that the semester tab does not have yet —
   currently `CE401` in `Y4S1` (the co-op work term);
5. adds `retake_of` and `attempt` to `custom`, and `extra_sems` + `plan_sems` to `students` (v4).

`setGrade` also creates a missing course column on demand now, so a student-added course needs no
manual cell: its grade lands in its home semester tab like every other course, and `gradesFor()`
picks it up unchanged. The `custom` tab therefore stores only the course *definition*.

It returns a summary string such as `added: students.track, extras.moved_col, tab custom, Y4S1.CE401`
(or `already up to date`), and logs it to the Execution log.

Then publish the new code. **This is the step that is easy to get wrong:**

> **Deploy → Manage deployments → click the ✏️ pencil → set the `Version` dropdown to
> `New version` → Deploy.**

`migrate_v3` runs from the editor against the *saved* code, so the Sheet changes even when the
deployment does not. The `/exec` URL serves the *deployed version*, which is separate. Inside the
edit dialog the `Version` dropdown **defaults to the version already deployed** — clicking Deploy
without switching it to `New version` re-publishes the old code and nothing changes, with no error.

Editing the existing deployment (rather than **New deployment**) keeps the same `/exec` URL, so
`data.js` needs no change. Creating a *new* deployment mints a different URL and the app would keep
talking to the old one.

**Verify it actually took** — a `setCustom` call must not come back `unknown action`:

```
curl -s -X POST "<your /exec URL>"   -d '{"action":"setCustom","student_id":"__check__","course_key":"ZZTEST1","data":{"code":"0","name":"x","cr":3,"cat":"elec","col":2}}'
# {"ok":true}  -> new code is live   |   {"error":"unknown action: setCustom"} -> still the old version
# then clean up:
curl -s -X POST "<your /exec URL>" -d '{"action":"setCustom","student_id":"__check__","course_key":"ZZTEST1","remove":true}'
```

## 2. Initialize

Editor → function dropdown → **`setup`** → **Run** → **complete the authorization prompt**
(Review permissions → your account → Advanced → Go to project → Allow). Watch the **Execution log**
finishes with no error. The Sheet now has `students`, 9 semester tabs, and `extras`.

**Demo logins:** `65010001` / `1234` (has 2 grades) · `65010002` / `1234` · `admin` / `17025`.

## 3. Deploy

**Deploy → New deployment → Web app** · Execute as **Me** · access **Anyone** · Deploy → copy the
`/exec` URL. (Editing the script later: **Manage deployments → edit → Deploy** keeps the same URL.)

Tests in a browser:
- `…/exec?action=ping` → `{"ok":true}`
- `…/exec?sheet=Y1S1` → rows (incl. 65010001's MATH161=A, ENGL101=B+)
- `…/exec?sheet=students` → rows **with no `password` field**

## 4. Point the app at it
`data.js` → `MODE="gsheet"`, `GSHEET_API="…/exec"`. Reload (clear the old service worker once).

## Notes
- Writes use a `text/plain` body (no CORS preflight) — don't add a JSON Content-Type for the gsheet path.
- Passwords stay plaintext **in the Sheet** (owner-only) but never leave via the API.
- Access must be **Anyone**, or fetch gets an HTML login page instead of JSON.
- Container-bound to this Sheet (`getActiveSpreadsheet()`), so no Sheet ID hard-coded.
